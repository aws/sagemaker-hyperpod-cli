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
from kubernetes.client import (
    V1SelfSubjectAccessReview, 
    V1SelfSubjectAccessReviewSpec, 
)


class SelfSubjectAccessReview:
    def __init__(self):
        return

    def self_subject_access_review(
            self, 
            resource_attributes=None, 
            non_resource_attributes=None, 
            local_vars_configuration=None,
        ):
        """
        Submit self subject access review
        """
        auth_v1_api = KubernetesClient().get_auth_v1_api()

        access_review = V1SelfSubjectAccessReview(
            spec=V1SelfSubjectAccessReviewSpec(
                resource_attributes=resource_attributes,
                non_resource_attributes=non_resource_attributes,
                local_vars_configuration=local_vars_configuration,
            )
        )

        response = auth_v1_api.create_self_subject_access_review(body=access_review)
        
        return response
