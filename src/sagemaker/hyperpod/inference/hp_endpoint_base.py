from typing import Union
import logging
import yaml
from types import SimpleNamespace
from kubernetes import client, config
from sagemaker.hyperpod.inference.config.constants import *
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import (
    _HPJumpStartEndpoint,
)
from sagemaker.hyperpod.inference.config.hp_endpoint_config import (
    _HPEndpoint,
)
from sagemaker.hyperpod.common.utils import (
    handle_exception,
    setup_logging,
    get_default_namespace,
)


class HPEndpointBase:
    is_kubeconfig_loaded = False

    @classmethod
    def verify_kube_config(cls):
        if not cls.is_kubeconfig_loaded:
            config.load_kube_config()
            cls.is_kubeconfig_loaded = True

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
        cls.verify_kube_config()

        logger = cls.get_logger()
        logger = setup_logging(logger)

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
            logger.error(f"Failed to create endpoint in namespace {namespace}!")
            handle_exception(e, name, namespace)

    @classmethod
    def call_list_api(
        cls,
        kind: str,
        namespace: str,
    ):
        cls.verify_kube_config()

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
        cls.verify_kube_config()

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
        self.verify_kube_config()

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
        cls.verify_kube_config()

        v1 = client.CoreV1Api()

        pods = v1.list_namespaced_pod(namespace=OPERATOR_NAMESPACE)

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
        namespace=None,
    ):
        cls.verify_kube_config()

        v1 = client.CoreV1Api()

        if not namespace:
            namespace = get_default_namespace()

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

    @classmethod
    def list_pods(cls, namespace=None):
        cls.verify_kube_config()

        if not namespace:
            namespace = get_default_namespace()

        v1 = client.CoreV1Api()
        response = v1.list_namespaced_pod(namespace=namespace)

        pods = []
        for item in response.items:
            pods.append(item.metadata.name)

        return pods

    @classmethod
    def list_namespaces(cls):
        cls.verify_kube_config()

        v1 = client.CoreV1Api()
        response = v1.list_namespace()

        namespaces = []
        for item in response.items:
            namespaces.append(item.metadata.name)

        return namespaces
