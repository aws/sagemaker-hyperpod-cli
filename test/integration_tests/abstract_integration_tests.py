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
import os
import subprocess
import time
import uuid
import re

import boto3
import yaml
from botocore.exceptions import ClientError

from hyperpod_cli.utils import setup_logger
from kubernetes.client.rest import ApiException
from kubernetes import client, config

logger = setup_logger(__name__)


class AbstractIntegrationTests:
    cfn_output_map = {}
    hyperpod_cluster_terminal_state = [
        "Failed",
        "InService",
    ]
    suffix = str(uuid.uuid4())[:8]
    hyperpod_cli_job_name: str = 'hyperpod-job-'+ suffix
    test_job_file = os.path.expanduser("./test/integration_tests/data/basicJob.yaml")
    hyperpod_cli_cluster_name = "HyperPodCLI-cluster"
    s3_roles_stack_name = "hyperpod-cli-resource-stack"
    vpc_stack_name = "hyperpod-cli-vpc-stack"
    test_team_name = "test-team"

    def _create_session(self):
        session = boto3.Session()
        return session

    def replace_placeholders(self):
        replacements = {
            'JOB_NAME': self.hyperpod_cli_job_name,
        }
        with open(self.test_job_file, 'r') as file:
            yaml_content = file.read()
        pattern = re.compile(r'\$\{([^}^{]+)\}')

        def replace(match):
            key = match.group(1)
            return str(replacements.get(key, match.group(0)))

        processed_yaml = pattern.sub(replace, yaml_content)

        with open(self.test_job_file, 'w') as file:
            file.write(processed_yaml)


    def create_kube_context(self):
        eks_cluster_name = 'HyperPodCLI-eks-cluster'
        command = [
            "aws",
            "eks",
            "update-kubeconfig",
            "--name",
            eks_cluster_name,
        ]

        try:
            # Execute the command to update kubeconfig
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to update kubeconfig: {e}")

    def apply_helm_charts(self):
        command = ["helm", "dependencies", "update", "helm_chart/HyperPodHelmChart"]

        try:
            # Execute the command to update helm charts
            logger.info(
                subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to update helm charts: {e}")

        apply_command = [
            "helm",
            "upgrade",
            "--install",
            "dependencies",
            "helm_chart/HyperPodHelmChart",
            "--namespace",
            "kube-system",
        ]

        try:
            # Execute the command to apply helm charts
            logger.info(
                subprocess.run(
                    apply_command,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to apply helm charts: {e}")

    def install_kueue(self):
        command = ["./helm_chart/install_dependencies.sh"]
        wait_command = ["kubectl", "wait", "deploy/kueue-controller-manager", "-nkueue-system", "--for=condition=available", "--timeout=5m"]
        try:
            # Execute the dependencies installation script to install kueue
            logger.info(
                subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            )

            # Wait for kueue to be available
            logger.info(
                subprocess.run(
                    wait_command,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to install the dependencies: {e}")

    # TODO: Manually setup quota allocation for now. Migrate to sagemaker public APIs afterwards
    def create_quota_allocation_resources(self):
        config.load_kube_config()
        # Create an instance of the API class
        core_api = client.CoreV1Api()
        custom_api = client.CustomObjectsApi()

        try:
            # Setup namespace 
            namespace = client.V1Namespace(
                metadata=client.V1ObjectMeta(
                    name=f"hyperpod-ns-{self.test_team_name}",
                    labels={
                        "sagemaker.amazonaws.com/sagemaker-managed-queue": "true",
                        "sagemaker.amazonaws.com/quota-allocation-id": self.test_team_name,
                    }
                )
            )
            core_api.create_namespace(body=namespace)
            logger.info("Namespace created successfully")
        except ApiException as e:
            if e.status == 409:
                logger.info("Already exists, move on")
            else:
                raise e
        
        try:
            # Setup resource flavor
            resource_flavor = {
                "apiVersion": "kueue.x-k8s.io/v1beta1",
                "kind": "ResourceFlavor",
                "metadata": {
                    "name": "ml.c5.2xlarge"
                }
            }
            custom_api.create_cluster_custom_object(
                group="kueue.x-k8s.io",
                version="v1beta1",
                plural="resourceflavors",
                body=resource_flavor
            )
            logger.info("ResourceFlavor created successfully")
        except ApiException as e:
            if e.status == 409:
                logger.info("Already exists, move on")
            else:
                raise e
        
        try:
            # Setup cluster queue
            cluster_queue = {
                "apiVersion": "kueue.x-k8s.io/v1beta1",
                "kind": "ClusterQueue",
                "metadata": {
                    "name": f"hyperpod-ns-{self.test_team_name}-clusterqueue"
                },
                "spec": {
                    "resourceGroups": [
                        {
                            "coveredResources": ["cpu", "memory"],
                            "flavors": [
                                {
                                    "name": "ml.c5.2xlarge",
                                    "resources": [
                                        {
                                            "name": "cpu",
                                            "nominalQuota": 2
                                        },
                                        {
                                            "name": "memory",
                                            "nominalQuota": "2Gi"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
            custom_api.create_cluster_custom_object(
                group="kueue.x-k8s.io",
                version="v1beta1",
                plural="clusterqueues",
                body=cluster_queue
            )
            logger.info("ClusterQueue created successfully")
        except ApiException as e:
            if e.status == 409:
                logger.info("Already exists, move on")
            else:
                raise e

        try:
            # Setup local queue
            local_queue = {
                "apiVersion": "kueue.x-k8s.io/v1beta1",
                "kind": "LocalQueue",
                "metadata": {
                    "name": f"hyperpod-ns-{self.test_team_name}-localqueue",
                    "namespace": f"hyperpod-ns-{self.test_team_name}"
                },
                "spec": {
                    "clusterQueue": f"hyperpod-ns-{self.test_team_name}-clusterqueue"
                }
            }
            custom_api.create_namespaced_custom_object(
                group="kueue.x-k8s.io",
                version="v1beta1",
                namespace=f"hyperpod-ns-{self.test_team_name}",
                plural="localqueues",
                body=local_queue
            )
        except ApiException as e:
            if e.status == 409:
                logger.info("Already exists, move on")
            else:
                raise e

    def setup(self):
        self.new_session = self._create_session()
        self.replace_placeholders()
        self.create_kube_context()
        self.apply_helm_charts()
        # self.install_kueue()
        # self.create_quota_allocation_resources()

    def tearDown(self):
        logger.info("Tests completed")