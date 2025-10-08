from sagemaker.hyperpod.common.config.metadata import Metadata
from sagemaker.hyperpod.inference.config.constants import *
from sagemaker.hyperpod.common.utils import (
    get_default_namespace,
    get_cluster_instance_types,
    setup_logging,
    get_current_cluster,
    get_current_region,
)
from sagemaker.hyperpod.inference.config.hp_endpoint_config import (
    InferenceEndpointConfigStatus,
    _HPEndpoint,
)
from sagemaker.hyperpod.common.telemetry.telemetry_logging import (
    _hyperpod_telemetry_emitter,
)
from sagemaker.hyperpod.common.telemetry.constants import Feature
from sagemaker.hyperpod.inference.hp_endpoint_base import HPEndpointBase
from typing import Dict, List, Optional
from sagemaker_core.main.resources import Endpoint
from pydantic import Field, ValidationError
from kubernetes import client


class HPEndpoint(_HPEndpoint, HPEndpointBase):
    metadata: Optional[Metadata] = Field(default=None)
    status: Optional[InferenceEndpointConfigStatus] = Field(default=None)

    def _create_internal(self, spec, debug=False):
        """Shared internal create logic"""
        logger = self.get_logger()
        logger = setup_logging(logger, debug)

        name = self.metadata.name if self.metadata else None
        namespace = self.metadata.namespace if self.metadata else None

        if not spec.endpointName and not name:
            raise Exception('Either metadata name or endpoint name must be provided')

        if not namespace:
            namespace = get_default_namespace()

        if not name:
            name = spec.endpointName

        # Create metadata object with labels and annotations if available
        metadata = Metadata(
            name=name,
            namespace=namespace,
            labels=self.metadata.labels if self.metadata else None,
            annotations=self.metadata.annotations if self.metadata else None,
        )

        self.validate_instance_type(spec.instanceType)

        self.call_create_api(
            metadata=metadata,
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            spec=spec,
            debug=debug,
        )

        self.metadata = metadata

        logger.info(
            f"Creating sagemaker model and endpoint. Endpoint name: {spec.endpointName}.\n The process may take a few minutes..."
        )

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "create_endpoint")
    def create(
        self,
        debug=False
    ) -> None:
        spec = _HPEndpoint(**self.model_dump(by_alias=True, exclude_none=True))
        self._create_internal(spec, debug)

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "create_endpoint_from_dict")
    def create_from_dict(
        self,
        input: Dict,
        debug=False
    ) -> None:
        spec = _HPEndpoint.model_validate(input, by_name=True)
        self._create_internal(spec, debug)


    def refresh(self):
        if not self.metadata:
            raise Exception(
                "Metadata not found! Please provide object name and namespace in metadata field."
            )

        response = self.call_get_api(
            name=self.metadata.name,
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace=self.metadata.namespace,
        )

        self.status = InferenceEndpointConfigStatus.model_validate(
            response["status"], by_name=True
        )

        return self

    @classmethod
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "list_endpoints")
    def list(
        cls,
        namespace: str = None,
    ) -> List[Endpoint]:
        if not namespace:
            namespace = get_default_namespace()

        response = cls.call_list_api(
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace=namespace,
        )

        endpoints = []

        if response and response["items"]:
            for item in response["items"]:
                name = item["metadata"]["name"]
                endpoints.append(cls.get(name, namespace=namespace))

        return endpoints

    @classmethod
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "get_endpoint")
    def get(cls, name: str, namespace: str = None) -> Endpoint:
        if not namespace:
            namespace = get_default_namespace()

        response = cls.call_get_api(
            name=name,
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace=namespace,
        )

        endpoint = HPEndpoint.model_validate(response["spec"], by_name=True)
        status = response.get("status")
        if status is not None:
            try:
                endpoint.status = InferenceEndpointConfigStatus.model_validate(
                    status, by_name=True
                )
            except ValidationError:
                endpoint.status = None
        else:
            endpoint.status = None
        endpoint.metadata = Metadata.model_validate(response["metadata"], by_name=True)

        return endpoint

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "delete_endpoint")
    def delete(self) -> None:
        logger = self.get_logger()
        logger = setup_logging(logger)

        self.call_delete_api(
            name=self.metadata.name,
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace=self.metadata.namespace,
        )
        logger.info(f"Deleting HPEndpoint: {self.metadata.name}...")

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "invoke_endpoint")
    def invoke(self, body, content_type="application/json"):
        if not self.endpointName:
            raise Exception("SageMaker endpoint name not found in this object!")

        endpoint = Endpoint.get(self.endpointName, region=get_current_region())

        return endpoint.invoke(body=body, content_type=content_type)

    def validate_instance_type(self, instance_type: str):
        logger = self.get_logger()
        logger = setup_logging(logger)

        cluster_instance_types = None

        # verify supported instance types from HyperPod cluster
        try:
            cluster_instance_types = get_cluster_instance_types(
                cluster=get_current_cluster(),
                region=get_current_region(),
            )
        except Exception as e:
            logger.warning(f"Failed to get instance types from HyperPod cluster: {e}")

        if cluster_instance_types and (instance_type not in cluster_instance_types):
            raise Exception(
                f"Current HyperPod cluster does not have instance type {instance_type}. Supported instance types are {cluster_instance_types}"
            )

    @classmethod
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "list_pods_endpoint")
    def list_pods(cls, namespace=None, endpoint_name=None):
        cls.verify_kube_config()

        if not namespace:
            namespace = get_default_namespace()

        v1 = client.CoreV1Api()
        list_pods_response = v1.list_namespaced_pod(namespace=namespace)

        endpoints = set()
        if endpoint_name:
            endpoints.add(endpoint_name)
        else:
            list_response = cls.call_list_api(
                kind=INFERENCE_ENDPOINT_CONFIG_KIND,
                namespace=namespace,
            )
            if list_response and list_response["items"]:
                for item in list_response["items"]:
                    endpoints.add(item["metadata"]["name"])

        pods = []
        for item in list_pods_response.items:
            app_name = item.metadata.labels.get("app", None)
            if app_name in endpoints:
                # list_namespaced_pod will return all pods in the namespace, so we need to filter
                # out the pods that are created by custom endpoint
                pods.append(item.metadata.name)

        return pods
