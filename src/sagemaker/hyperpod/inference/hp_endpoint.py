from sagemaker.hyperpod.common.config.metadata import Metadata
from sagemaker.hyperpod.inference.config.constants import *
from sagemaker.hyperpod.inference.config.hp_endpoint_config import (
    InferenceEndpointConfigStatus,
    _HPEndpoint,
)
from sagemaker.hyperpod.inference.hp_endpoint_base import HPEndpointBase
from typing import Dict, List, Optional
from typing_extensions import Self
from sagemaker_core.main.resources import Endpoint
from pydantic import Field, ValidationError
import logging


class HPEndpoint(_HPEndpoint, HPEndpointBase):
    metadata: Optional[Metadata] = Field(default=None)
    status: Optional[InferenceEndpointConfigStatus] = Field(default=None)

    def create(
        self,
        name=None,
        namespace="default",
        debug=False,
    ) -> None:
        logging.basicConfig()
        if debug:
            self.get_logger().setLevel(logging.DEBUG)
        else:
            self.get_logger().setLevel(logging.INFO)
        spec = _HPEndpoint(**self.model_dump(by_alias=True, exclude_none=True))

        if not name:
            name = spec.modelName

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

        self.get_logger().info(
            "Creating sagemaker model and endpoint. This may take a few minutes..."
        )

    def create_from_dict(
        self,
        input: Dict,
        namespace: str = "default",
    ) -> None:
        spec = _HPEndpoint.model_validate(input, by_name=True)

        if not name:
            name = spec.modelName

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

        self.get_logger().info(
            "Creating sagemaker model and endpoint. This may take a few minutes..."
        )

    def refresh(self) -> Self:
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
        namespace: str = "default",
    ) -> List[Endpoint]:
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
    def get(cls, name: str, namespace: str = "default") -> Endpoint:
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
        self.call_delete_api(
            name=self.metadata.name,
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace=self.metadata.namespace,
        )

    def invoke(self, body, content_type="application/json"):
        if not self.endpointName:
            raise Exception("SageMaker endpoint name not found in this object!")

        endpoint = Endpoint.get(
            self.endpointName, region=HPEndpoint.get_current_region()
        )

        return endpoint.invoke(body=body, content_type=content_type)
