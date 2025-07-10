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
from sagemaker.hyperpod.inference.hp_endpoint_base import HPEndpointBase
from typing import Dict, List, Optional
from sagemaker_core.main.resources import Endpoint
from pydantic import Field, ValidationError


class HPEndpoint(_HPEndpoint, HPEndpointBase):
    metadata: Optional[Metadata] = Field(default=None)
    status: Optional[InferenceEndpointConfigStatus] = Field(default=None)

    def create(
        self,
        name=None,
        namespace=None,
        debug=False,
    ) -> None:
        logger = self.get_logger()
        logger = setup_logging(logger, debug)

        spec = _HPEndpoint(**self.model_dump(by_alias=True, exclude_none=True))

        if not spec.endpointName and not name:
            raise Exception('Input "name" is required if endpoint name is not provided')

        if not namespace:
            namespace = get_default_namespace()

        if not name:
            name = spec.endpointName

        self.validate_instance_type(spec.instanceType)

        self.call_create_api(
            name=name,  # use model name as metadata name
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace=namespace,
            spec=spec,
        )

        self.metadata = Metadata(
            name=name,
            namespace=namespace,
        )

        logger.info(
            f"Creating sagemaker model and endpoint. Endpoint name: {spec.endpointName}.\n The process may take a few minutes..."
        )

    def create_from_dict(
        self,
        input: Dict,
        name: str = None,
        namespace: str = None,
    ) -> None:
        logger = self.get_logger()
        logger = setup_logging(logger)

        spec = _HPEndpoint.model_validate(input, by_name=True)

        if not namespace:
            namespace = get_default_namespace()

        if not spec.endpointName and not name:
            raise Exception('Input "name" is required if endpoint name is not provided')

        if not name:
            name = spec.endpointName

        self.validate_instance_type(spec.instanceType)

        self.call_create_api(
            name=name,  # use model name as metadata name
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace=namespace,
            spec=spec,
        )

        self.metadata = Metadata(
            name=name,
            namespace=namespace,
        )

        logger.info(
            f"Creating sagemaker model and endpoint. Endpoint name: {spec.endpointName}.\n The process may take a few minutes..."
        )

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

    def delete(self) -> None:
        logger = self.get_logger()
        logger = setup_logging(logger)

        self.call_delete_api(
            name=self.metadata.name,
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace=self.metadata.namespace,
        )
        logger.info(f"Deleting HPEndpoint: {self.metadata.name}...")

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
