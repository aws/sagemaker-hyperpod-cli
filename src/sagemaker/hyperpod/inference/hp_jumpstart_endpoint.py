from typing import Dict, List, Optional
from pydantic import Field, ValidationError
from sagemaker.hyperpod.inference.config.constants import *
from sagemaker.hyperpod.inference.hp_endpoint_base import HPEndpointBase
from sagemaker.hyperpod.common.config.metadata import Metadata
from sagemaker.hyperpod.common.utils import (
    get_current_cluster,
    get_current_region,
    get_jumpstart_model_instance_types,
    get_cluster_instance_types,
    get_default_namespace,
    setup_logging,
)
from sagemaker_core.main.resources import Endpoint
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import (
    _HPJumpStartEndpoint,
    JumpStartModelStatus,
)


class HPJumpStartEndpoint(_HPJumpStartEndpoint, HPEndpointBase):
    metadata: Optional[Metadata] = Field(default=None)
    status: Optional[JumpStartModelStatus] = Field(default=None)

    def create(
        self,
        name=None,
        namespace=None,
        debug=False,
    ) -> None:
        logger = self.get_logger()
        logger = setup_logging(logger, debug)

        spec = _HPJumpStartEndpoint(**self.model_dump(by_alias=True, exclude_none=True))

        endpoint_name = ""
        if spec.sageMakerEndpoint and spec.sageMakerEndpoint.name:
            endpoint_name = spec.sageMakerEndpoint.name

        if not endpoint_name and not name:
            raise Exception('Input "name" is required if endpoint name is not provided')

        if not name:
            name = endpoint_name

        if not namespace:
            namespace = get_default_namespace()

        self.validate_instance_type(spec.model.modelId, spec.server.instanceType)

        self.call_create_api(
            name=name,  # use model name as metadata name
            kind=JUMPSTART_MODEL_KIND,
            namespace=namespace,
            spec=spec,
        )

        self.metadata = Metadata(
            name=name,
            namespace=namespace,
        )

        logger.info(
            f"Creating JumpStart model and sagemaker endpoint. Endpoint name: {endpoint_name}.\n The process may take a few minutes..."
        )

    def create_from_dict(
        self,
        input: Dict,
        name: str = None,
        namespace: str = None,
    ) -> None:
        logger = self.get_logger()
        logger = setup_logging(logger)

        spec = _HPJumpStartEndpoint.model_validate(input, by_name=True)

        endpoint_name = ""
        if spec.sageMakerEndpoint and spec.sageMakerEndpoint.name:
            endpoint_name = spec.sageMakerEndpoint.name

        if not endpoint_name and not name:
            raise Exception('Input "name" is required if endpoint name is not provided')

        if not name:
            name = endpoint_name

        if not namespace:
            namespace = get_default_namespace()

        self.validate_instance_type(spec.model.modelId, spec.server.instanceType)

        self.call_create_api(
            name=name,  # use model name as metadata name
            kind=JUMPSTART_MODEL_KIND,
            namespace=namespace,
            spec=spec,
        )

        self.metadata = Metadata(
            name=name,
            namespace=namespace,
        )

        logger.info(
            f"Creating JumpStart model and sagemaker endpoint. Endpoint name: {endpoint_name}.\n The process may take a few minutes..."
        )

    def refresh(self):
        if not self.metadata:
            raise Exception(
                "Metadata is empty. Please provide name and namespace in metadata field."
            )

        response = HPJumpStartEndpoint.call_get_api(
            name=self.metadata.name,
            kind=JUMPSTART_MODEL_KIND,
            namespace=self.metadata.namespace,
        )

        self.status = JumpStartModelStatus.model_validate(
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
            kind=JUMPSTART_MODEL_KIND,
            namespace=namespace,
        )

        endpoints = []

        if response and response["items"]:
            for item in response["items"]:
                name = item["metadata"]["name"]
                endpoints.append(cls.get(name, namespace=namespace))

        return endpoints

    @classmethod
    def get(cls, name: str, namespace: str = None):
        if not namespace:
            namespace = get_default_namespace()

        response = cls.call_get_api(
            name=name,
            kind=JUMPSTART_MODEL_KIND,
            namespace=namespace,
        )

        endpoint = HPJumpStartEndpoint.model_validate(response["spec"], by_name=True)
        status = response.get("status")
        if status is not None:
            try:
                endpoint.status = JumpStartModelStatus.model_validate(
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
            kind=JUMPSTART_MODEL_KIND,
            namespace=self.metadata.namespace,
        )
        logger.info(
            f"Deleting JumpStart model and sagemaker endpoint: {self.metadata.name}. This may take a few minutes..."
        )

    def invoke(self, body, content_type="application/json"):
        if not self.sageMakerEndpoint or not self.sageMakerEndpoint.name:
            raise Exception("SageMaker endpoint name not found in this object!")

        endpoint = Endpoint.get(
            self.sageMakerEndpoint.name, region=get_current_region()
        )

        return endpoint.invoke(body=body, content_type=content_type)

    def validate_instance_type(self, model_id: str, instance_type: str):
        logger = self.get_logger()
        logger = setup_logging(logger)

        model_types = None
        cluster_instance_types = None

        # verify supported instance types from model hub
        try:
            model_types = get_jumpstart_model_instance_types(
                model_id, get_current_region()
            )
        except Exception as e:
            logger.warning(
                f"Failed to fetch supported instance type from SageMakerPublicHub content: {e}"
            )

        if model_types and (instance_type not in model_types):
            raise Exception(
                f"Instance type {instance_type} not supported by JumpStart model {model_id}. Supported types are {model_types}"
            )

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
