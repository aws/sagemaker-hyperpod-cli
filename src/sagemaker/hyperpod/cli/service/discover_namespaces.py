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
import concurrent
import sys
import copy
from kubernetes.client.rest import ApiException
from sagemaker.hyperpod.cli.clients.kubernetes_client import KubernetesClient
from sagemaker.hyperpod.cli.service.get_namespaces import GetNamespaces
from sagemaker.hyperpod.cli.service.self_subject_access_review import SelfSubjectAccessReview
from sagemaker.hyperpod.cli.utils import setup_logger


logger = setup_logger(__name__)

class DiscoverNamespaces:
    def __init__(self):
        return

    def discover_accessible_namespace(self, resource_attributes_template, only_sm_managed=True):
        """
        Discover the accessible namespaces
        """
        k8s_client = KubernetesClient()
        context_namespace = k8s_client.get_current_context_namespace()

        # If the namespace is explicitly set by user, take the namespace from the config instead
        # of discovering automatically 
        if context_namespace is not None:
            return context_namespace
        
        try:
            if only_sm_managed:
                namespaces = GetNamespaces().get_sagemaker_managed_namespaces()
            else:
                namespaces = GetNamespaces().get_namespaces()

            discovered_namespaces = self.get_namespaces_by_checking_access_permission(
                namespaces,
                resource_attributes_template,
            )

            if len(discovered_namespaces) == 0:
                logger.error("Found no accessible namespaces. Please ask for cluster admin for assistance or specify value of namespace explicitly in the command.")
                sys.exit(1)
            if len(discovered_namespaces) > 1:
                logger.error(f"Found more than 1 accessible namespaces {discovered_namespaces}. Please specify value of namespace explicitly in the command.")
                sys.exit(1)
            
            if len(discovered_namespaces) == 1:
                logger.info(f"Found accessible namespace: {discovered_namespaces}")
            return discovered_namespaces[0]
        except ApiException as e:
            if e.status == 403:
                logger.error("Got access denied error when discovering accessible namespaces, please specify the '--namespace' parameter in the command and try again.")
                sys.exit(1)


    def get_namespaces_by_checking_access_permission(
            self,
            namespaces,
            resource_attributes_template, 
            max_workers=10
        ):
        """
        Get the accessible namespaces by performing the SelfSubjectAccessReview. For each of the namespace,
        check if user has specified permission to it, if the answer is NO, the namespace will be skipped.

        Performing access check can take quite long if the number of namespaces is large. Thus the implementation
        leverages the multi-threading to ensure that multiple access check can be performed in parallel.
        """
        subject_access_review = SelfSubjectAccessReview()
        accessible_namespaces = list()
        resource_attributes = list()

        for namespace in namespaces:
            resource_attribute = copy.deepcopy(resource_attributes_template)
            resource_attribute.namespace = namespace
            resource_attributes.append(resource_attribute)

        # Multi-thread the self subject access review to improve the performance
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    subject_access_review.self_subject_access_review, resource_attribute
                ) for resource_attribute in resource_attributes
            }
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    response = future.result()
                    if response.status.allowed:
                        accessible_namespaces.append(
                            response.spec.resource_attributes.namespace
                        )
                except Exception as e:
                    raise(e)

        return accessible_namespaces