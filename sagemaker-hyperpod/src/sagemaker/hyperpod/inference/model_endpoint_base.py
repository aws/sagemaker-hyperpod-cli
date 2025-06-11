from kubernetes import client, utils
from kubernetes import config as k8s_config
from hyperpod.inference.config.constants import *
import yaml
from hyperpod.inference.config.jumpstart_model_endpoint_config import JumpStartModelSpec
from hyperpod.inference.config.model_endpoint_config import InferenceEndpointConfigSpec
from types import SimpleNamespace


class ModelEndpointBase:
    def __init__(self,
            name: str,
            kind: str,
            namespace: str,
            spec: JumpStartModelSpec | InferenceEndpointConfigSpec,
        ):
        self.apiVersion = INFERENCE_API_VERSION
        self.kind = kind

        self.metadata = SimpleNamespace(
            name=name,
            namespace=namespace
        )

        self.spec = spec

    def _validate_cluster_connection(self):
        try:
            k8s_config.load_kube_config()
            v1 = client.CoreV1Api()
            return True
        except Exception as e:
            return False

    def config(self):
        return {
            "apiVersion": self.apiVersion,
            "kind": self.kind,
            "metadata": self.metadata.__dict__,
            "spec": self.spec.model_dump(exclude_none=True)
        }
    
    def deploy(self):
        if not self._validate_cluster_connection():
            raise Exception("Failed to connect to the Kubernetes cluster. Please check your kubeconfig.")
        
        custom_api = client.CustomObjectsApi()
        print('\n Deploying with dict:', self.config())

        try:
            custom_api.create_namespaced_custom_object(
                group="inference.sagemaker.aws.amazon.com",
                version="v1alpha1",
                namespace=self.metadata.namespace,
                plural=KIND_PLURAL_MAP[self.kind],
                body=self.config(),
            )
            print('Successful deployed model and its endpoint!')
        except Exception as e:
            print(f"Failed to deploy model and its endpoint: {e}")

