from typing import Union
import logging
import yaml
from types import SimpleNamespace
from kubernetes import client
from sagemaker.hyperpod.inference.config.constants import *
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import (
    _HPJumpStartEndpoint,
)
from sagemaker.hyperpod.inference.config.hp_endpoint_config import (
    _HPEndpoint,
)
from sagemaker.hyperpod.common.utils import (
    validate_cluster_connection,
    handle_exception,
)


class HPEndpointBase:
    @classmethod
    def get_logger(cls):
        return logging.getLogger(__name__)

    @classmethod
    def call_create_api(
        cls,
        name: str,
        kind: str,
        namespace: str,
        spec: Union[_HPJumpStartEndpoint, _HPEndpoint],
    ):
        if not validate_cluster_connection():
            raise Exception(
                "Failed to connect to the Kubernetes cluster. Please check your kubeconfig."
            )

        logger = cls.get_logger()

        custom_api = client.CustomObjectsApi()

        body = {
            "apiVersion": INFERENCE_FULL_API_VERSION,
            "kind": kind,
            "metadata": SimpleNamespace(name=name, namespace=namespace).__dict__,
            "spec": spec.model_dump(exclude_none=True),
        }

        logger.debug("Creating endpoint with config:\n%s", yaml.dump(body))

        try:
            custom_api.create_namespaced_custom_object(
                group=INFERENCE_GROUP,
                version=INFERENCE_API_VERSION,
                namespace=namespace,
                plural=KIND_PLURAL_MAP[kind],
                body=body,
            )
        except Exception as e:
            logger.debug(f"Failed to create endpoint in namespace {namespace}!")
            handle_exception(e, name, namespace)

    @classmethod
    def call_list_api(
        cls,
        kind: str,
        namespace: str,
    ):
        if not validate_cluster_connection():
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
            handle_exception(e, "", namespace)

    @classmethod
    def call_get_api(
        cls,
        name: str,
        kind: str,
        namespace: str,
    ):
        if not validate_cluster_connection():
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
            handle_exception(e, name, namespace)

    def call_delete_api(
        self,
        name: str,
        kind: str,
        namespace: str,
    ):
        if not validate_cluster_connection():
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
            handle_exception(e, name, namespace)

    @classmethod
    def get_operator_logs(cls, since_hours: float):
        if not validate_cluster_connection():
            raise Exception(
                "Failed to connect to the Kubernetes cluster. Please check your kubeconfig."
            )

        v1 = client.CoreV1Api()

        pods = v1.list_namespaced_pod(namespace="hyperpod-inference-operator-system")

        if not pods.items:
            raise Exception(
                "No pod found in namespace hyperpod-inference-operator-system"
            )

        # Get logs from first pod
        first_pod = pods.items[0]
        pod_name = first_pod.metadata.name

        try:
            logs = v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=OPERATOR_NAMESPACE,
                timestamps=True,
                since_seconds=int(3600 * since_hours),
            )
        except Exception as e:
            handle_exception(e, pod_name, OPERATOR_NAMESPACE)

        return logs

    @classmethod
    def get_logs(
        cls,
        pod: str,
        container: str = None,
        namespace="default",
    ):
        if not validate_cluster_connection():
            raise Exception(
                "Failed to connect to the Kubernetes cluster. Please check your kubeconfig."
            )

        v1 = client.CoreV1Api()

        pod_details = v1.read_namespaced_pod(
            name=pod,
            namespace=namespace,
        )

        # if pod has multiple containers, get logs in the first container
        if not container:
            container = pod_details.spec.containers[0].name

        try:
            logs = v1.read_namespaced_pod_log(
                name=pod,
                namespace=namespace,
                container=container,
                timestamps=True,
            )
        except Exception as e:
            handle_exception(e, pod, namespace)

        return logs
