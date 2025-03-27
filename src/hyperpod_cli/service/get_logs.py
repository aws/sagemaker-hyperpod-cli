# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from typing import Optional
import boto3

from hyperpod_cli.clients.kubernetes_client import (
    KubernetesClient,
)
from hyperpod_cli.service.discover_namespaces import DiscoverNamespaces
from hyperpod_cli.service.list_pods import (
    ListPods,
)
from hyperpod_cli.utils import (
    get_eks_cluster_name,
    get_hyperpod_cluster_region,
)
from kubernetes.client.rest import ApiException
from kubernetes.client import V1ResourceAttributes

AMAZON_ClOUDWATCH_OBSERVABILITY = "amazon-cloudwatch-observability"

class GetLogs:
    def __init__(self):
        return

    def get_training_job_logs(
        self,
        job_name: str,
        pod_name: str,
        namespace: Optional[str],
    ):
        """
        Get logs for pod asscoited with the training job
        """
        k8s_client = KubernetesClient()
        list_pods_service = ListPods()

        if not namespace:
            resource_attributes_template = V1ResourceAttributes(
                verb="get",
                group="",
                resource="pods",
                subresource="log",
            )
            namespace = DiscoverNamespaces().discover_accessible_namespace(
                resource_attributes_template
            )

        try:
            pods_for_training_job = list_pods_service.list_pods_for_training_job(
                job_name, namespace, False
            )
            if pod_name not in pods_for_training_job:
                raise RuntimeError(
                    f"Given pod name {pod_name} is not associated with training job {job_name} in namespace {namespace}"
                )
            return k8s_client.get_logs_for_pod(pod_name, namespace)
        except ApiException as e:
            raise RuntimeError(f"Unexpected API error: {e.reason} ({e.status})")
    
    def generate_cloudwatch_link(
        self,
        pod_name: str,
        namespace: Optional[str],
    ):
        eks_cluster_name = get_eks_cluster_name()

        if self.is_container_insights_addon_enabled(eks_cluster_name):
            k8s_client = KubernetesClient()

            # pod_details is a V1Pod object
            pod_details = k8s_client.get_pod_details(pod_name, namespace)
            
            # get node name
            if pod_details.spec and pod_details.spec.node_name:
                node_name = pod_details.spec.node_name
            else:
                node_name = None

            # get container name
            if pod_details.spec and pod_details.spec.containers and pod_details.spec.containers[0].name:
                container_name = pod_details.spec.containers[0].name
            else:
                container_name = None

            # get container_id
            if pod_details.status and pod_details.status.container_statuses and pod_details.status.container_statuses[0].container_id:
                full_container_id = pod_details.status.container_statuses[0].container_id

                # full_container_id has format "containerd://xxxxxxxxxx" 
                container_id = full_container_id[13:] if full_container_id.startswith('containerd://') else None
            else:
                container_id = None         

            # Cloudwatch container insight log groups should have the same pod log as API response
            if node_name and pod_name and namespace and container_name and container_id:
                region = get_hyperpod_cluster_region()

                cloudwatch_url = self.get_log_url(eks_cluster_name, region, node_name, pod_name, namespace, container_name, container_id)
                cloudwatch_link = f'The pod cloudwatch log stream link is {cloudwatch_url}'
            else:
                cloudwatch_link = 'Failed to load container insights CloudWatch Link!'
        else:
            cloudwatch_link = None

        return cloudwatch_link

    def get_log_url(self, eks_cluster_name, region, node_name, pod_name, namespace, container_name, container_id):
        console_prefix = f'https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}#'
        log_group_prefix = f'logsV2:log-groups/log-group/$252Faws$252Fcontainerinsights$252F{eks_cluster_name}$252Fapplication/log-events/'
        log_stream = f'{node_name}-application.var.log.containers.{pod_name}_{namespace}_{container_name}-{container_id}.log'
        
        return console_prefix + log_group_prefix + log_stream

    def is_container_insights_addon_enabled(self, eks_cluster_name):
        response = boto3.client("eks").list_addons(clusterName=eks_cluster_name, maxResults=50)
        if AMAZON_ClOUDWATCH_OBSERVABILITY in response.get('addons', []):
            return True
        else:
            return False