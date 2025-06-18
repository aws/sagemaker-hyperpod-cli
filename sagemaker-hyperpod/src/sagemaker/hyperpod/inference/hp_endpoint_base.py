from kubernetes import client
from kubernetes import config as k8s_config
from sagemaker.hyperpod.inference.config.constants import *
import yaml
from sagemaker.hyperpod.inference.config.jumpstart_model_endpoint_config import (
    JumpStartModelSpec,
)
from sagemaker.hyperpod.inference.config.model_endpoint_config import (
    InferenceEndpointConfigSpec,
)
from types import SimpleNamespace


class HPEndpointBase:
    def _validate_connection(self):
        try:
            k8s_config.load_kube_config()
            v1 = client.CoreV1Api()
            return True
        except Exception as e:
            return False

    def call_create_api(
        self,
        name: str,
        kind: str,
        namespace: str,
        spec: JumpStartModelSpec | InferenceEndpointConfigSpec,
    ):
        if not self._validate_connection():
            raise Exception(
                "Failed to connect to the Kubernetes cluster. Please check your kubeconfig."
            )

        custom_api = client.CustomObjectsApi()

        body = {
            "apiVersion": INFERENCE_FULL_API_VERSION,
            "kind": kind,
            "metadata": SimpleNamespace(name=name, namespace=namespace).__dict__,
            "spec": spec.model_dump(exclude_none=True),
        }

        print("\nDeploying model and endpoint using config:\n", yaml.dump(body))

        try:
            custom_api.create_namespaced_custom_object(
                group=INFERENCE_GROUP,
                version=INFERENCE_API_VERSION,
                namespace=namespace,
                plural=KIND_PLURAL_MAP[kind],
                body=body,
            )
            print("\nSuccessful deployed model and its endpoint!")
        except Exception as e:
            print(f"\nFailed to deploy model and its endpoint: {e}")

    def call_get_api(
        self,
        name: str,
        kind: str,
        namespace: str,
    ):
        if not self._validate_connection():
            raise Exception(
                "Failed to connect to the Kubernetes cluster. Please check your kubeconfig."
            )

        custom_api = client.CustomObjectsApi()

        try:
            return custom_api.get_namespaced_custom_object(
                group=INFERENCE_GROUP,
                version=INFERENCE_API_VERSION,
                namespace=namespace,
                plural=KIND_PLURAL_MAP[kind],
                name=name,
            )
        except Exception as e:
            print(f"\nFailed to get endpoint details: {e}")

    def call_delete_api(
        self,
        name: str,
        kind: str,
        namespace: str,
    ):
        if not self._validate_connection():
            raise Exception(
                "Failed to connect to the Kubernetes cluster. Please check your kubeconfig."
            )

        custom_api = client.CustomObjectsApi()

        try:
            custom_api.delete_namespaced_custom_object(
                group=INFERENCE_GROUP,
                version=INFERENCE_API_VERSION,
                namespace=namespace,
                plural=KIND_PLURAL_MAP[kind],
                name=name,
            )
            print(f"Successful deleted model and endpoint!")
        except Exception as e:
            print(f"Failed to delete endpoint details: {e}")

    def call_list_api(
        self,
        kind: str,
        namespace: str,
    ):
        if not self._validate_connection():
            raise Exception(
                "Failed to connect to the Kubernetes cluster. Please check your kubeconfig."
            )

        custom_api = client.CustomObjectsApi()

        try:
            return custom_api.list_namespaced_custom_object(
                group=INFERENCE_GROUP,
                version=INFERENCE_API_VERSION,
                namespace=namespace,
                plural=KIND_PLURAL_MAP[kind],
            )
        except Exception as e:
            print(f"\nFailed to list endpoint: {e}")
