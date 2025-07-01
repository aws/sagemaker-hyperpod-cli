from sagemaker.hyperpod.inference.config.constants import *
from sagemaker.hyperpod.inference.hp_endpoint_base import HPEndpointBase
from sagemaker.hyperpod.inference.config.common import Metadata
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import (
    _HPJumpStartEndpoint,
    JumpStartModelStatus,
)
from typing import Dict, List, Optional, Self
from sagemaker_core.main.resources import Endpoint
from pydantic import Field
from pydantic import ValidationError
import logging


class HPJumpStartEndpoint(_HPJumpStartEndpoint, HPEndpointBase):
    metadata: Optional[Metadata] = Field(default=None)
    status: Optional[JumpStartModelStatus] = Field(default=None)

    def create(
        self,
        name=None,
        namespace="default",
        debug=False,
    ) -> None:
        if debug:
            logging.basicConfig(level=logging.DEBUG)

        spec = _HPJumpStartEndpoint(**self.model_dump(by_alias=True, exclude_none=True))

        if not name:
            name = spec.model.modelId

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

    def create_from_dict(
        self,
        input: Dict,
        name: str = None,
        namespace: str = "default",
    ) -> None:
        spec = _HPJumpStartEndpoint.model_validate(input, by_name=True)

        if not name:
            name = spec.model.modelId

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

    def refresh(self) -> Self:
        if not self.metadata:
            raise Exception(
                "Metadata not found! Please provide object name and namespace in metadata field."
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
        namespace: str = "default",
    ) -> List[Endpoint]:
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
    def get(cls, name: str, namespace: str = "default") -> Self:
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

    def invoke(self, body, content_type="application/json"):
        if not self.sageMakerEndpoint or not self.sageMakerEndpoint.name:
            raise Exception("SageMaker endpoint name not found in this object!")

        endpoint = Endpoint.get(
            self.sageMakerEndpoint.name, region=HPJumpStartEndpoint.get_current_region()
        )

        return endpoint.invoke(body=body, content_type=content_type)
