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
from typing import List, Optional

import yaml
from kubernetes import client, config, stream
from kubernetes.client import (
    V1Namespace,
    V1NamespaceList,
)
from kubernetes.config import (
    KUBE_CONFIG_DEFAULT_LOCATION,
)
from kubernetes.client.rest import ApiException
from sagemaker.hyperpod.cli.constants.command_constants import (
    SAGEMAKER_MANAGED_QUEUE_LABEL,
    TEMP_KUBE_CONFIG_FILE,
)
from sagemaker.hyperpod.cli.constants.exception_constants import RESOURCE_NOT_FOUND_CODE
from sagemaker.hyperpod.cli.constants.kueue_constants import (
    CLUSTER_QUEUE_PRIORITY_CLASS_CUSTOM_OBJECT_PLURAL,
    KUEUE_CUSTOM_OBJECT_GROUP, 
    KUEUE_CUSTOM_OBJECT_VERSION, 
    WORKLOAD_CUSTOM_OBJECT_PLURAL,
    WORKLOAD_PRIORITY_CLASS_CUSTOM_OBJECT_PLURAL,
)
from sagemaker.hyperpod.cli.constants.pytorch_constants import (
    PYTORCH_CUSTOM_OBJECT_GROUP,
    PYTORCH_CUSTOM_OBJECT_PLURAL,
    PYTORCH_CUSTOM_OBJECT_VERSION,
)
from sagemaker.hyperpod.cli.utils import setup_logger

logger = setup_logger(__name__)

KUBE_CONFIG_PATH = os.path.expanduser(KUBE_CONFIG_DEFAULT_LOCATION)


class KubernetesClient:
    _instance = None
    _kube_client = None

    def __new__(cls, is_get_capacity: bool = False) -> "KubernetesClient":
        if cls._instance is None:
            cls._instance = super(KubernetesClient, cls).__new__(cls)
            config.load_kube_config(
                config_file=KUBE_CONFIG_PATH
                if not is_get_capacity
                else TEMP_KUBE_CONFIG_FILE
            )  # or config.load_incluster_config() for in-cluster config
            cls._instance._kube_client = client.ApiClient()
        return cls._instance

    def set_context(
        self,
        context_name: str,
        namespace: Optional[str],
    ) -> None:
        """
        Set the current context in the kubeconfig file.

        Args:
            context_name (str): The name of the context to set as current.
            namespace (str): The name of the namespace to use.
        """
        with open(KUBE_CONFIG_PATH, "r") as file:
            kubeconfig = yaml.safe_load(file)

        # Check if the context exists in the kubeconfig and update the context namespace
        # when namespace is specified in command line
        exist = False
        for context in kubeconfig["contexts"]:
            if context["name"] == context_name:
                if namespace is not None:
                    context["context"]["namespace"] = namespace
                    logger.debug(f"updated the namespace to {namespace}")
                else:
                    context["context"].pop("namespace", None)
                exist = True

        if not exist:
            raise ValueError(f"Context '{context_name}' not found in kubeconfig file")

        # Set the current context
        kubeconfig["current-context"] = context_name

        # Write the updated kubeconfig back to the file
        with open(KUBE_CONFIG_PATH, "w") as file:
            yaml.safe_dump(kubeconfig, file)

        # Load the updated kubeconfig
        config.load_kube_config(config_file=KUBE_CONFIG_PATH)
        logger.debug(f"Current context set to '{context_name}'")

    def get_core_v1_api(self) -> client.CoreV1Api:
        """
        Get the CoreV1Api client.

        Returns:
            client.CoreV1Api: The CoreV1Api client.
        """
        if self._kube_client is None:
            raise RuntimeError(
                "Kubernetes client is not initialized. Call set_context() first."
            )
        return client.CoreV1Api(self._kube_client)

    def get_apps_v1_api(self) -> client.AppsV1Api:
        """
        Get the AppsV1Api client.

        Returns:
            client.AppsV1Api: The AppsV1Api client.
        """
        if self._kube_client is None:
            raise RuntimeError(
                "Kubernetes client is not initialized. Call set_context() first."
            )
        return client.AppsV1Api(self._kube_client)

    def get_auth_v1_api(self) -> client.AuthorizationV1Api:
        """
        Get the AuthorizationV1Api client.

        Returns:
            client.AuthorizationV1Api: The AuthorizationV1Api client.
        """

        if self._kube_client is None:
            raise RuntimeError(
                "Kubernetes client is not initialized. Call set_context() first."
            )
        return client.AuthorizationV1Api(self._kube_client)

    def context_exists(self, context: str) -> bool:
        """
        Check if the specified context exists in the kubeconfig.

        Args:
            context (str): The name of the context to check.

        Returns:
            bool: True if the context exists, False otherwise.
        """
        try:
            contexts, _ = config.list_kube_config_contexts()
            return any(ctx["name"] == context for ctx in contexts)
        except Exception as e:
            raise RuntimeError(f"Failed to check Kubernetes context: {e}")

    def list_node_with_temp_config(
        self,
        file: str,
        selector_str: str,
    ) -> List:
        """
        Load kubeconfig from a local file

        Args:
            file (str): The path to the kubeconfig file
            selector_str (str): Selector to filter
        """
        config.load_kube_config(config_file=file)
        v1Client = client.CoreV1Api()
        _continue = None

        nodes = []
        while True:
            response = v1Client.list_node(
                label_selector=selector_str,
                limit=200,  # Set a reasonable limit
                _continue=_continue,
            )
            nodes.extend(response.items)

            _continue = response._metadata._continue  # Get the continue token

            if not _continue:  # If there's no more data, break the loop
                break
        return nodes

    def get_current_context_namespace(
        self,
    ) -> str:
        """
        Returns current user namespace context
        """
        contexts, active_context = config.list_kube_config_contexts()
        return active_context["context"]["namespace"] if "namespace" in active_context["context"] else None

    def list_namespaces(self) -> List[str]:
        """
        returns all namespaces
        """
        result: List[str] = []
        namespaces: V1NamespaceList = client.CoreV1Api().list_namespace()
        namespace: V1Namespace
        for namespace in namespaces.items:
            if namespace.metadata and namespace.metadata.name:
                result.append(namespace.metadata.name)
        return result

    def get_sagemaker_managed_namespace(self, namespace: Optional[str]):
        """
        Verify if a namespace is sagemaker managed. SageMaker created namespaces have custom label
        attached, indicating that the namespace is SageMaker managed.

        Args:
            namespace (Optional[str]): The input namespace that will be checked.

        Returns:
            Optional[V1Namespace]: V1Namespace response if namespace exists and it is verified being managed by SageMaker. Otherwise return None.
        """
        if namespace is None:
            return None
        try:
            response = client.CoreV1Api().read_namespace(name=namespace)
            labels = response.metadata.labels
            if labels and SAGEMAKER_MANAGED_QUEUE_LABEL in labels and labels[SAGEMAKER_MANAGED_QUEUE_LABEL] == "true":
                return response
        except ApiException as e:
            if e.status == RESOURCE_NOT_FOUND_CODE:
                return None
            else:
                raise e
        return None

    def list_pods_with_labels(self, namespace: str, label_selector: str):
        return client.CoreV1Api().list_namespaced_pod(
            namespace=namespace,
            label_selector=label_selector,
        )

    def list_pods_in_all_namespaces_with_labels(self, label_selector: str):
        v1Client = client.CoreV1Api()
        pods = []
        _continue = None

        while True:
            response = v1Client.list_pod_for_all_namespaces(
                label_selector=label_selector,
                limit=200,  # Set a reasonable limit
                _continue=_continue,
            )
            pods.extend(response.items)

            _continue = response._metadata._continue  # Get the continue token

            if not _continue:  # If there's no more data, break the loop
                break

        return pods

    def get_logs_for_pod(self, pod_name: str, namespace: str):
        return client.CoreV1Api().read_namespaced_pod_log(
            name=pod_name, namespace=namespace
        )

    def get_job(self, job_name: str, namespace: str):
        return client.CustomObjectsApi().get_namespaced_custom_object(
            group=PYTORCH_CUSTOM_OBJECT_GROUP,
            version=PYTORCH_CUSTOM_OBJECT_VERSION,
            namespace=namespace,
            plural=PYTORCH_CUSTOM_OBJECT_PLURAL,
            name=job_name,
        )
    
    def get_pod_details(self, pod_name: str, namespace: str):
        return client.CoreV1Api().read_namespaced_pod(
            name=pod_name, namespace=namespace
        )

    def delete_training_job(self, job_name: str, namespace: str):
        return client.CustomObjectsApi().delete_namespaced_custom_object(
            group=PYTORCH_CUSTOM_OBJECT_GROUP,
            version=PYTORCH_CUSTOM_OBJECT_VERSION,
            namespace=namespace,
            plural=PYTORCH_CUSTOM_OBJECT_PLURAL,
            name=job_name,
        )

    def list_training_jobs(
        self,
        namespace: str,
        label_selector: Optional[str],
    ):
        return client.CustomObjectsApi().list_namespaced_custom_object(
            group=PYTORCH_CUSTOM_OBJECT_GROUP,
            version=PYTORCH_CUSTOM_OBJECT_VERSION,
            namespace=namespace,
            plural=PYTORCH_CUSTOM_OBJECT_PLURAL,
            label_selector=label_selector,
        )
    
    def check_if_namespace_exists(self, namespace: str):
        try:
            client.CoreV1Api().read_namespace(name=namespace)
            return True
        except client.rest.ApiException as e:
            if e.status == 404:
                return False
            else:
                print(f"Exception when calling read_namespace: {e}")
                raise e

    def exec_command_on_pod(
        self,
        pod: str,
        namespace: str,
        bash_command: str,
    ):
        return stream.stream(
            client.CoreV1Api().connect_get_namespaced_pod_exec,
            stderr=True,
            stdout=True,
            name=pod,
            namespace=namespace,
            command=bash_command,
        )

    def patch_workload(self, workload_name: str, namespace: str, patch_body: str):
        return client.CustomObjectsApi().patch_namespaced_custom_object(
            group=KUEUE_CUSTOM_OBJECT_GROUP,
            version=KUEUE_CUSTOM_OBJECT_VERSION,
            namespace=namespace,
            plural=WORKLOAD_CUSTOM_OBJECT_PLURAL,
            name=workload_name,
            body=patch_body
        )

    def get_workload_by_label(self, label_selector: str, namespace: str):
        return client.CustomObjectsApi().list_namespaced_custom_object(
            group=KUEUE_CUSTOM_OBJECT_GROUP,
            version=KUEUE_CUSTOM_OBJECT_VERSION,
            namespace=namespace,
            plural=WORKLOAD_CUSTOM_OBJECT_PLURAL,
            label_selector=label_selector,
        )
    
    def list_workload_priority_classes(self):
        return client.CustomObjectsApi().list_cluster_custom_object(
            group=KUEUE_CUSTOM_OBJECT_GROUP,
            version=KUEUE_CUSTOM_OBJECT_VERSION,
            plural=WORKLOAD_PRIORITY_CLASS_CUSTOM_OBJECT_PLURAL,
        )
    
    def get_cluster_queue(self, cluster_queue_name: str):
        return client.CustomObjectsApi().get_cluster_custom_object(
            group=KUEUE_CUSTOM_OBJECT_GROUP,
            version=KUEUE_CUSTOM_OBJECT_VERSION,
            plural=CLUSTER_QUEUE_PRIORITY_CLASS_CUSTOM_OBJECT_PLURAL,
            name=cluster_queue_name
        )
    # Add more methods to access other APIs as needed
