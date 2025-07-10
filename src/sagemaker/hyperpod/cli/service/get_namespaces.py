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
from sagemaker.hyperpod.cli.clients.kubernetes_client import (
    KubernetesClient,
)

from sagemaker.hyperpod.cli.constants.command_constants import SAGEMAKER_MANAGED_QUEUE_LABEL


LIMIT_PER_REQUEST = 200

class GetNamespaces:

    def __init__(self):
        return

    def get_namespaces(self, label_selector=None):
        """
        Get namespaces in the cluster
        """
        core_v1_api = KubernetesClient().get_core_v1_api()
        all_namespaces = list()
        continue_token = None

        while True:
            response = None
            if continue_token:
                response = core_v1_api.list_namespace(
                    limit=LIMIT_PER_REQUEST, label_selector=label_selector, _continue=continue_token
                )
            else:
                response = core_v1_api.list_namespace(
                    limit=LIMIT_PER_REQUEST, label_selector=label_selector
                )

            all_namespaces.extend([ns.metadata.name for ns in response.items])
            continue_token = response.metadata._continue

            if not continue_token:
                break
        
        return all_namespaces

    def get_sagemaker_managed_namespaces(self):
        """
        Get sagemaker managed namespaces in the cluster
        """

        return self.get_namespaces(SAGEMAKER_MANAGED_QUEUE_LABEL + "=true")
