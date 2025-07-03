from sagemaker.hyperpod.inference.config.constants import *
from sagemaker.hyperpod.inference.hp_endpoint_base import HPEndpointBase
from sagemaker.hyperpod.common.config.metadata import Metadata
from sagemaker.hyperpod.common.utils import append_uuid
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import (
    _HPJumpStartEndpoint,
    JumpStartModelStatus,
)
from sagemaker.hyperpod.common.utils import get_default_namespace
from typing import Dict, List, Optional
from sagemaker_core.main.resources import Endpoint
from pydantic import Field, ValidationError
import logging


class HPJumpStartEndpoint(_HPJumpStartEndpoint, HPEndpointBase):
    metadata: Optional[Metadata] = Field(default=None)
    status: Optional[JumpStartModelStatus] = Field(default=None)

    def create(
        self,
        name=None,
        namespace=None,
        debug=False,
    ) -> None:
        logging.basicConfig()
        if debug:
            self.get_logger().setLevel(logging.DEBUG)
        else:
            self.get_logger().setLevel(logging.INFO)

        spec = _HPJumpStartEndpoint(**self.model_dump(by_alias=True, exclude_none=True))

        if not name:
            name = append_uuid(spec.model.modelId)

        if spec.sageMakerEndpoint and spec.sageMakerEndpoint.name:
            spec.sageMakerEndpoint.name = append_uuid(spec.sageMakerEndpoint.name)

        if not namespace:
            namespace = get_default_namespace()

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

        self.get_logger().info(
            "Creating JumpStart model and sagemaker endpoint. This may take a few minutes..."
        )

    def create_from_dict(
        self,
        input: Dict,
        name: str = None,
        namespace: str = None,
    ) -> None:
        spec = _HPJumpStartEndpoint.model_validate(input, by_name=True)

        if not name:
            name = append_uuid(spec.model.modelId)

        if spec.sageMakerEndpoint and spec.sageMakerEndpoint.name:
            spec.sageMakerEndpoint.name = append_uuid(spec.sageMakerEndpoint.name)

        if not namespace:
            namespace = get_default_namespace()

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

        self.get_logger().info(
            "Creating JumpStart model and sagemaker endpoint. This may take a few minutes..."
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
        self.call_delete_api(
            name=self.metadata.name,
            kind=JUMPSTART_MODEL_KIND,
            namespace=self.metadata.namespace,
        )
        self.get_logger().info(
            f"Deleting JumpStart model and sagemaker endpoint: {self.metadata.name}. This may take a few minutes..."
        )

    def invoke(self, body, content_type="application/json"):
        if not self.sageMakerEndpoint or not self.sageMakerEndpoint.name:
            raise Exception("SageMaker endpoint name not found in this object!")

        endpoint = Endpoint.get(
            self.sageMakerEndpoint.name, region=HPJumpStartEndpoint.get_current_region()
        )

        return endpoint.invoke(body=body, content_type=content_type)
