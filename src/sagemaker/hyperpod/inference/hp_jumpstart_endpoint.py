from typing import Dict, List, Optional
from pydantic import Field, ValidationError
from sagemaker.hyperpod.inference.config.constants import *
from sagemaker.hyperpod.inference.constant import INSTANCE_MIG_PROFILES
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
from sagemaker.hyperpod.common.telemetry.telemetry_logging import (
    _hyperpod_telemetry_emitter,
)
from sagemaker.hyperpod.common.telemetry.constants import Feature
from kubernetes import client


class HPJumpStartEndpoint(_HPJumpStartEndpoint, HPEndpointBase):
    metadata: Optional[Metadata] = Field(default=None)
    status: Optional[JumpStartModelStatus] = Field(default=None)

    def _create_internal(self, spec, debug=False):
        """Shared internal create logic"""
        logger = self.get_logger()
        logger = setup_logging(logger, debug)

        endpoint_name = ""
        name = self.metadata.name if self.metadata else None
        namespace = self.metadata.namespace if self.metadata else None

        if spec.sageMakerEndpoint and spec.sageMakerEndpoint.name:
            endpoint_name = spec.sageMakerEndpoint.name

        if not endpoint_name and not name:
            raise Exception("Either metadata name or endpoint name must be provided")

        if not name:
            name = endpoint_name

        if not namespace:
            namespace = get_default_namespace()


        # Create metadata object with labels and annotations if available
        metadata = Metadata(
            name=name,
            namespace=namespace,
            labels=self.metadata.labels if self.metadata else None,
            annotations=self.metadata.annotations if self.metadata else None,
        )

        # Only validate instance type if accelerator_partition_validation is provided
        if not spec.server.acceleratorPartitionType:
            self.validate_instance_type(spec.model.modelId, spec.server.instanceType)
        else:
            self.validate_mig_profile(spec.server.acceleratorPartitionType, spec.server.instanceType)

        self.call_create_api(
            metadata=metadata,
            kind=JUMPSTART_MODEL_KIND,
            spec=spec,
            debug=debug,
        )

        self.metadata = metadata

        logger.info(
            f"Creating JumpStart model and sagemaker endpoint. Endpoint name: {endpoint_name}.\n The process may take a few minutes..."
        )

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "create_js_endpoint")
    def create(
        self,
        debug=False
    ) -> None:
        logger = self.get_logger()
        logger = setup_logging(logger, debug)
        spec = _HPJumpStartEndpoint(**self.model_dump(by_alias=True, exclude_none=True))
        self._create_internal(spec, debug)


    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "create_js_endpoint_from_dict")
    def create_from_dict(self, input: Dict, debug=False) -> None:
        logger = self.get_logger()
        logger = setup_logging(logger, debug)

        spec = _HPJumpStartEndpoint.model_validate(input, by_name=True)

        endpoint_name = ""
        name = self.metadata.name if self.metadata else None
        namespace = self.metadata.namespace if self.metadata else None

        if spec.sageMakerEndpoint and spec.sageMakerEndpoint.name:
            endpoint_name = spec.sageMakerEndpoint.name

        if not endpoint_name and not name:
            raise Exception('Input "name" is required if endpoint name is not provided')

        if not name:
            name = endpoint_name

        if not namespace:
            namespace = get_default_namespace()

        # Only validate instance type if accelerator_partition_validation is provided
        if not spec.server.acceleratorPartitionType:
            self.validate_instance_type(spec.model.modelId, spec.server.instanceType)
        else:
            self.validate_mig_profile(spec.server.acceleratorPartitionType, spec.server.instanceType)

        self.call_create_api(
            name=name,  # use model name as metadata name
            kind=JUMPSTART_MODEL_KIND,
            namespace=namespace,
            spec=spec,
            debug=debug,
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

        if isinstance(response, dict) and "status" in response:
            self.status = JumpStartModelStatus.model_validate(
                response["status"], by_name=True
            )
        else:
            self.status = None

        return self

    @classmethod
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "list_js_endpoints")
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
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "get_js_endpoint")
    def get(cls, name: str, namespace: str = None):
        if not namespace:
            namespace = get_default_namespace()

        response = cls.call_get_api(
            name=name,
            kind=JUMPSTART_MODEL_KIND,
            namespace=namespace,
        )

        if not isinstance(response, dict):
            raise Exception(f"Expected dictionary response, got {type(response)}")

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

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "delete_js_endpoint")
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

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "invoke_js_endpoint")
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

    def validate_mig_profile(self, mig_profile: str, instance_type: str):
        """
        Validate if the MIG profile is supported for the given instance type.

        Args:
            instance_type: SageMaker instance type (e.g., "ml.p4d.24xlarge")
            mig_profile: MIG profile (e.g., "1g.10gb")

        Raises:
            ValueError: If the instance type doesn't support MIG profiles or if the MIG profile is not supported for the instance type
        """
        logger = self.get_logger()
        logger = setup_logging(logger)

        if instance_type not in INSTANCE_MIG_PROFILES:
            error_msg = (
                f"Instance type '{instance_type}' does not support MIG profiles. "
                f"Supported instance types: {list(INSTANCE_MIG_PROFILES.keys())}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        if mig_profile not in INSTANCE_MIG_PROFILES[instance_type]:
            error_msg = (
                f"MIG profile '{mig_profile}' is not supported for instance type '{instance_type}'. "
                f"Supported MIG profiles for {instance_type}: {INSTANCE_MIG_PROFILES[instance_type]}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(
            f"MIG profile '{mig_profile}' is valid for instance type '{instance_type}'"
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
                kind=JUMPSTART_MODEL_KIND,
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
                # out the pods that are created by jumpstart endpoint
                pods.append(item.metadata.name)

        return pods