from kubernetes import client, utils
from kubernetes import config as k8s_config
from hyperpod.inference.config.constants import *
import yaml
from hyperpod.inference.config.jumpstart_model_endpoint_config import JumpStartModelSpec
from hyperpod.inference.config.model_endpoint_config import InferenceEndpointConfigSpec
from types import SimpleNamespace


class ModelEndpointBase:
    def _validate_cluster_connection(self):
        try:
            k8s_config.load_kube_config()
            v1 = client.CoreV1Api()
            return True
        except Exception as e:
            return False
    
    def invoke_api_call(
            self,
            name: str,
            kind: str,
            namespace: str,
            spec: JumpStartModelSpec | InferenceEndpointConfigSpec,
        ):
        if not self._validate_cluster_connection():
            raise Exception("Failed to connect to the Kubernetes cluster. Please check your kubeconfig.")
        
        custom_api = client.CustomObjectsApi()

        body = {
            "apiVersion": INFERENCE_API_VERSION,
            "kind": kind,
            "metadata": SimpleNamespace(name=name, namespace=namespace).__dict__,
            "spec": spec.model_dump(exclude_none=True)
        }
        print('\n Deploying with dict:', body)

        try:
            custom_api.create_namespaced_custom_object(
                group="inference.sagemaker.aws.amazon.com",
                version="v1alpha1",
                namespace=namespace,
                plural=KIND_PLURAL_MAP[kind],
                body=body,
            )
            print('\nSuccessful deployed model and its endpoint!')
        except Exception as e:
            print(f"\nFailed to deploy model and its endpoint: {e}")

