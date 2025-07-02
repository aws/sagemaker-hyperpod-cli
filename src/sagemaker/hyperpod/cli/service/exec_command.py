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

from sagemaker.hyperpod.cli.clients.kubernetes_client import (
    KubernetesClient,
)
from sagemaker.hyperpod.cli.service.list_pods import (
    ListPods,
)

from kubernetes.client.rest import ApiException


class ExecCommand:
    def __init__(self):
        return

    def exec_command(
        self,
        job_name: str,
        pod_name: Optional[str],
        namespace: Optional[str],
        all_pods: Optional[bool],
        bash_command: tuple,
    ):
        bash_command_str: str = " ".join(bash_command)

        k8s_client = KubernetesClient()
        list_pods_service = ListPods()

        if not namespace:
            namespace = k8s_client.get_current_context_namespace()

        pods_for_training_job = list_pods_service.list_pods_for_training_job(
            job_name, namespace, False
        )

        try:
            if all_pods:
                output = ""
                for pod in pods_for_training_job:
                    output += pod + "\n"
                    output += (
                        k8s_client.exec_command_on_pod(
                            pod,
                            namespace,
                            bash_command_str,
                        )
                        + "\n"
                    )
                    output += "\n"
                return output
            else:
                if pod_name not in pods_for_training_job:
                    raise RuntimeError(
                        f"Given pod name {pod_name} is not associated with training job {job_name} in namespace {namespace}"
                    )
                return k8s_client.exec_command_on_pod(
                    pod_name,
                    namespace,
                    bash_command_str,
                )
        except ApiException as e:
            raise RuntimeError(f"Unexpected API error: {e.reason} ({e.status})")
