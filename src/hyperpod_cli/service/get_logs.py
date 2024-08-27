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

from hyperpod_cli.clients.kubernetes_client import KubernetesClient
from hyperpod_cli.service.list_pods import ListPods


class GetLogs:
    def __init__(self):
        return

    def get_training_job_logs(self, job_name: str, pod_name: str, namespace: Optional[str]):
        """
        Get logs for pod asscoited with the training job
        """
        k8s_client = KubernetesClient()
        list_pods_service = ListPods()

        if not namespace:
            namespace = k8s_client.get_current_context_namespace()

        pods_for_training_job = list_pods_service.list_pods_for_training_job(
            job_name, namespace, False
        )
        if pod_name not in pods_for_training_job:
            raise RuntimeError(
                f"Given pod name {pod_name} is not associated with training job {job_name} in namespace {namespace}"
            )

        return k8s_client.get_logs_for_pod(pod_name, namespace)
