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
from sagemaker.hyperpod.common.config.metadata import Metadata
from sagemaker.hyperpod.common.utils import (
    handle_exception,
    setup_logging,
    get_default_namespace,
    verify_kubernetes_version_compatibility,
)
from sagemaker.hyperpod.common.telemetry.telemetry_logging import (
    _hyperpod_telemetry_emitter,
)
from sagemaker.hyperpod.common.telemetry.constants import Feature


class HPEndpointBase:
    """Base class for HyperPod inference endpoints.

    This class provides common functionality for managing inference endpoints
    on SageMaker HyperPod clusters orchestrated by Amazon EKS. It handles
    Kubernetes API interactions for creating, listing, getting, and deleting
    inference endpoints.
    """
    is_kubeconfig_loaded = False

    @classmethod
    def get_logger(cls):
        """Get logger instance for the class.

        **Returns:**

        logging.Logger: Logger instance for this module.
        """
        return logging.getLogger(__name__)
    
    @classmethod
    def verify_kube_config(cls):
        """Verify and load Kubernetes configuration.

        Loads the Kubernetes configuration if not already loaded and verifies
        Kubernetes version compatibility.
        """
        if not cls.is_kubeconfig_loaded:
            config.load_kube_config()
            cls.is_kubeconfig_loaded = True
            
            # Verify Kubernetes version compatibility
            verify_kubernetes_version_compatibility(cls.get_logger())

    @classmethod
    def call_create_api(
        cls,
        metadata: Metadata,
        kind: str,
        spec: Union[_HPJumpStartEndpoint, _HPEndpoint],
        debug: bool = False,
    ):
        """Create an inference endpoint using Kubernetes API.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - metadata
             - Metadata
             - Kubernetes metadata object containing name, namespace, labels, and annotations
           * - kind
             - str
             - Kubernetes resource kind (e.g., 'HPJumpStartEndpoint')
           * - spec
             - Union[_HPJumpStartEndpoint, _HPEndpoint]
             - Endpoint specification

        **Raises:**

        Exception: If endpoint creation fails

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import _HPJumpStartEndpoint
              >>> from sagemaker.hyperpod.common.config.metadata import Metadata
              >>> spec = _HPJumpStartEndpoint(...)
              >>> metadata = Metadata(name="my-endpoint", namespace="default")
              >>> HPEndpointBase.call_create_api(metadata, "HPJumpStartEndpoint", spec)
        """
        cls.verify_kube_config()

        logger = cls.get_logger()
        logger = setup_logging(logger, debug)

        custom_api = client.CustomObjectsApi()

        body = {
            "apiVersion": INFERENCE_FULL_API_VERSION,
            "kind": kind,
            "metadata": metadata.model_dump(exclude_none=True),
            "spec": spec.model_dump(exclude_none=True),
        }

        logger.debug("Creating endpoint with config:\n%s", yaml.dump(body))

        try:
            custom_api.create_namespaced_custom_object(
                group=INFERENCE_GROUP,
                version=INFERENCE_API_VERSION,
                namespace=metadata.namespace,
                plural=KIND_PLURAL_MAP[kind],
                body=body,
            )
        except Exception as e:
            logger.error(f"Failed to create endpoint in namespace {metadata.namespace}!")
            handle_exception(e, metadata.name, metadata.namespace, debug=debug)

    @classmethod
    def call_list_api(
        cls,
        kind: str,
        namespace: str,
    ):
        """List inference endpoints using Kubernetes API.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - kind
             - str
             - Kubernetes resource kind to list
           * - namespace
             - str
             - Kubernetes namespace to list endpoints from

        **Returns:**

        dict: List of endpoints in the specified namespace

        **Raises:**

        Exception: If listing endpoints fails

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> endpoints = HPEndpointBase.call_list_api("HPJumpStartEndpoint", "default")
              >>> print(f"Found {len(endpoints['items'])} endpoints")
        """
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
        """Get a specific inference endpoint using Kubernetes API.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - name
             - str
             - Name of the endpoint to retrieve
           * - kind
             - str
             - Kubernetes resource kind
           * - namespace
             - str
             - Kubernetes namespace containing the endpoint

        **Returns:**

        dict: Endpoint details

        **Raises:**

        Exception: If retrieving endpoint fails

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> endpoint = HPEndpointBase.call_get_api("my-endpoint", "HPJumpStartEndpoint", "default")
              >>> print(endpoint['metadata']['name'])
        """
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
            # Map kind to correct resource type
            resource_type = 'hyp_jumpstart_endpoint' if kind == 'JumpStartModel' else 'hyp_custom_endpoint'
            handle_exception(e, name, namespace,
                            operation_type='get', resource_type=resource_type)

    def call_delete_api(
        self,
        name: str,
        kind: str,
        namespace: str,
    ):
        """Delete an inference endpoint using Kubernetes API.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - name
             - str
             - Name of the endpoint to delete
           * - kind
             - str
             - Kubernetes resource kind
           * - namespace
             - str
             - Kubernetes namespace containing the endpoint

        **Raises:**

        Exception: If deleting endpoint fails

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> base = HPEndpointBase()
              >>> base.call_delete_api("my-endpoint", "HPJumpStartEndpoint", "default")
        """
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
            # Map kind to correct resource type
            resource_type = 'hyp_jumpstart_endpoint' if kind == 'JumpStartModel' else 'hyp_custom_endpoint'
            handle_exception(e, name, namespace,
                            operation_type='delete', resource_type=resource_type)

    @classmethod
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "get_operator_logs")
    def get_operator_logs(cls, since_hours: float):
        """Get logs from the inference operator.

        Retrieves logs from the HyperPod inference operator pods for debugging
        and monitoring purposes.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - since_hours
             - float
             - Number of hours back to retrieve logs from

        **Returns:**

        str: Operator logs with timestamps

        **Raises:**

        Exception: If no operator pods found or log retrieval fails

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> logs = HPEndpointBase.get_operator_logs(1.0)
              >>> print(logs)
              >>>
              >>> # Get logs from last 30 minutes
              >>> logs = HPEndpointBase.get_operator_logs(0.5)
        """
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
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "get_logs_endpoint")
    def get_logs(
        cls,
        pod: str,
        container: str = None,
        namespace=None,
    ):
        """Get logs from a specific pod.

        Retrieves logs from a pod associated with an inference endpoint.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - pod
             - str
             - Name of the pod to get logs from
           * - container
             - str, optional
             - Container name. If not specified, uses the first container in the pod
           * - namespace
             - str, optional
             - Kubernetes namespace. If not specified, uses the default namespace

        **Returns:**

        str: Pod logs with timestamps

        **Raises:**

        Exception: If log retrieval fails

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> logs = HPEndpointBase.get_logs("my-pod-name")
              >>> print(logs)
              >>>
              >>> # Get logs from specific container
              >>> logs = HPEndpointBase.get_logs("my-pod", container="inference")
              >>>
              >>> # Get logs from specific namespace
              >>> logs = HPEndpointBase.get_logs("my-pod", namespace="my-namespace")
        """
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
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "list_pods_endpoint")
    def list_pods(cls, namespace=None):
        """List all pods in a namespace.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - namespace
             - str, optional
             - Kubernetes namespace to list pods from. If not specified, uses the default namespace

        **Returns:**

        List[str]: List of pod names in the namespace

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> pods = HPEndpointBase.list_pods()
              >>> print(f"Found {len(pods)} pods: {pods}")
              >>>
              >>> # List pods in specific namespace
              >>> pods = HPEndpointBase.list_pods(namespace="my-namespace")
        """
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
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "list_namespaces")
    def list_namespaces(cls):
        """List all available Kubernetes namespaces.

        **Returns:**

        List[str]: List of namespace names

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> namespaces = HPEndpointBase.list_namespaces()
              >>> print(f"Available namespaces: {namespaces}")
        """
        cls.verify_kube_config()

        v1 = client.CoreV1Api()
        response = v1.list_namespace()

        namespaces = []
        for item in response.items:
            namespaces.append(item.metadata.name)

        return namespaces
