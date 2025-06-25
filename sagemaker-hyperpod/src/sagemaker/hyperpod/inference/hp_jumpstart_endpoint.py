from sagemaker.hyperpod.inference.config.constants import *
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import (
    Model,
    JumpStartModelSpec,
    SageMakerEndpoint,
    Server,
)
from sagemaker.hyperpod.inference.hp_endpoint_base import HPEndpointBase
from datetime import datetime
from typing import Dict
from tabulate import tabulate
import yaml


class HPJumpStartEndpoint(HPEndpointBase):
    def _validate_inputs(
        self,
        model_id: str,
        instance_type: str,
    ):
        # Validate required parameters when spec is None
        if model_id is None or instance_type is None:
            raise ValueError("Must provide both model_id and instance_type.")

        # Type validation
        if not isinstance(model_id, str):
            raise TypeError(f"model_id must be of type str, got {type(model_id)}")
        if not isinstance(instance_type, str):
            raise TypeError(
                f"instance_type must be of type str, got {type(instance_type)}"
            )

    def _validate_instance_type(self):
        """
        Get supported instance types from node and model
        """
        pass

    def _get_default_endpoint_name(self, model_id: str):
        """
        Generate default endpoint name if not specified by user
        """
        time_str = datetime.now().strftime("%y%m%d-%H%M%S-%f")

        return model_id + "-" + time_str

    @classmethod
    def create(
        cls,
        namespace: str = "default",
        model_id: str = None,
        model_version: str = None,
        instance_type: str = None,
        sagemaker_endpoint: str = None,
        accept_eula: bool = False,
    ):
        instance = cls()
        instance._validate_inputs(model_id, instance_type)

        if not sagemaker_endpoint:
            sagemaker_endpoint = instance._get_default_endpoint_name(model_id)

        spec = JumpStartModelSpec(
            model=Model(
                model_id=model_id,
                model_version=model_version,
                accept_eula=accept_eula,
            ),
            server=Server(instance_type=instance_type),
            sage_maker_endpoint=SageMakerEndpoint(name=sagemaker_endpoint),
        )

        instance.call_create_api(
            name=spec.model.modelId,  # use model id as metadata name
            kind=JUMPSTART_MODEL_KIND,
            namespace=namespace,
            spec=spec,
        )

    @classmethod
    def create_from_spec(
        cls,
        spec: JumpStartModelSpec,
        namespace: str = "default",
    ):
        cls().call_create_api(
            name=spec.model.modelId,  # use model id as metadata name
            kind=JUMPSTART_MODEL_KIND,
            namespace=namespace,
            spec=spec,
        )

    @classmethod
    def create_from_dict(
        cls,
        input: Dict,
        namespace: str = "default",
    ):
        spec = JumpStartModelSpec.model_validate(input, by_name=True)

        cls().call_create_api(
            name=spec.model.modelId,  # use model id as metadata name
            kind=JUMPSTART_MODEL_KIND,
            namespace=namespace,
            spec=spec,
        )

    @classmethod
    def list(
        cls,
        namespace: str = "default",
    ):
        response = cls().call_list_api(
            kind=JUMPSTART_MODEL_KIND,
            namespace=namespace,
        )

        output_data = []
        if response and response["items"]:
            for item in response["items"]:
                metadata = item["metadata"]
                output_data.append((metadata["name"], metadata["creationTimestamp"]))
        headers = ["METADATA NAME", "CREATE TIME"]

        print(tabulate(output_data, headers=headers))

    @classmethod
    def describe(
        cls,
        name: str,
        namespace: str = "default",
    ):
        response = cls().call_get_api(
            name=name,
            kind=JUMPSTART_MODEL_KIND,
            namespace=namespace,
        )

        response["metadata"].pop("managedFields")
        print(yaml.dump(response))

    @classmethod
    def delete(
        cls,
        name: str,
        namespace: str = "default",
    ):
        cls().call_delete_api(
            name=name,  # use model id as metadata name
            kind=JUMPSTART_MODEL_KIND,
            namespace=namespace,
        )
