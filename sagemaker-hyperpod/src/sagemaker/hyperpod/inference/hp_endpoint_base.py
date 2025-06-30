from kubernetes import client
from kubernetes import config as k8s_config
from sagemaker.hyperpod.inference.config.constants import *
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import (
    _HPJumpStartEndpoint,
)
from sagemaker.hyperpod.inference.config.hp_endpoint_config import (
    _HPEndpoint,
)
from types import SimpleNamespace
import boto3
from sagemaker.hyperpod.hyperpod_manager import HyperPodManager
import re


class HPEndpointBase:
    @classmethod
    def get_current_region(cls):
        eks_arn = HyperPodManager.get_context()
        eks_arn_pattern = r"arn:aws:eks:([\w-]+):\d+:cluster/[\w-]+"
        match = re.match(eks_arn_pattern, eks_arn)

        if match:
            return match.group(1)

        region = boto3.session.Session().region_name

        return region

    @classmethod
    def _validate_connection(cls):
        try:
            k8s_config.load_kube_config()
            v1 = client.CoreV1Api()
            return True
        except Exception as e:
            return False

    @classmethod
    def call_create_api(
        cls,
        name: str,
        kind: str,
        namespace: str,
        spec: _HPJumpStartEndpoint | _HPEndpoint,
    ):
        if not cls._validate_connection():
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

        try:
            custom_api.create_namespaced_custom_object(
                group=INFERENCE_GROUP,
                version=INFERENCE_API_VERSION,
                namespace=namespace,
                plural=KIND_PLURAL_MAP[kind],
                body=body,
            )
        except Exception as e:
            raise Exception(f"Failed to deploy model and its endpoint: {e}")

    @classmethod
    def call_list_api(
        cls,
        kind: str,
        namespace: str,
    ):
        if not cls._validate_connection():
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
            raise Exception(f"Failed to list endpoint: {e}")

    @classmethod
    def call_get_api(
        cls,
        name: str,
        kind: str,
        namespace: str,
    ):
        if not cls._validate_connection():
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
            raise Exception(f"Failed to get endpoint details: {e}")

    def call_delete_api(
        cls,
        name: str,
        kind: str,
        namespace: str,
    ):
        if not cls._validate_connection():
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
        except Exception as e:
            raise Exception(f"Failed to delete endpoint details: {e}")
