import logging
import yaml
from typing import List, Optional, ClassVar, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from sagemaker.hyperpod.common.config.metadata import Metadata
from sagemaker.hyperpod.common.utils import (
    handle_exception,
    get_default_namespace,
    setup_logging,
    verify_kubernetes_version_compatibility
)
from sagemaker.hyperpod.space.utils import map_kubernetes_response_to_model
from sagemaker.hyperpod.common.telemetry.telemetry_logging import (
    _hyperpod_telemetry_emitter,
)
from sagemaker.hyperpod.common.telemetry.constants import Feature
from sagemaker.hyperpod.cli.constants.space_constants import (
    SPACE_GROUP,
    SPACE_VERSION,
    SPACE_PLURAL,
)
from hyperpod_space_template.v1_0.model import SpaceConfig


class HPSpace(BaseModel):
    """HyperPod Space on Amazon SageMaker HyperPod clusters.

    This class provides methods to create, manage, and monitor spaces
    on SageMaker HyperPod clusters orchestrated by Amazon EKS.
    """
    
    is_kubeconfig_loaded: ClassVar[bool] = False
    model_config = ConfigDict(extra="forbid")

    config: SpaceConfig = Field(
        description="The space configuration using the template model"
    )
    
    raw_resource: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The complete Kubernetes resource data including apiVersion, kind, metadata, and status"
    )

    @classmethod
    def get_logger(cls):
        """Get logger for the class."""
        return logging.getLogger(__name__)

    @property
    def api_version(self) -> Optional[str]:
        """Get the apiVersion from the Kubernetes resource."""
        return self.raw_resource.get("apiVersion") if self.raw_resource else None

    @property
    def kind(self) -> Optional[str]:
        """Get the kind from the Kubernetes resource."""
        return self.raw_resource.get("kind") if self.raw_resource else None

    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        """Get the metadata from the Kubernetes resource."""
        return self.raw_resource.get("metadata") if self.raw_resource else None

    @property
    def status(self) -> Optional[Dict[str, Any]]:
        """Get the status from the Kubernetes resource."""
        return self.raw_resource.get("status") if self.raw_resource else None

    @classmethod
    def verify_kube_config(cls):
        """Verify and load Kubernetes configuration."""
        if not cls.is_kubeconfig_loaded:
            try:
                config.load_kube_config()
                cls.is_kubeconfig_loaded = True
                verify_kubernetes_version_compatibility(cls.get_logger())
            except Exception as e:
                raise RuntimeError(f"Failed to load kubeconfig: {e}")

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "create_space")
    def create(self, debug: bool = False):
        """Create and submit the HyperPod Space to the Kubernetes cluster.

        Args:
            debug (bool, optional): Enable debug logging. Defaults to False.

        Raises:
            Exception: If the space creation fails or Kubernetes API call fails
        """
        self.verify_kube_config()
        
        logger = self.get_logger()
        logger = setup_logging(logger, debug)

        # Convert config to domain model
        domain_config = self.config.to_domain()
        config_body = domain_config["space_spec"]

        logger.debug(
            "Creating HyperPod Space with config:\n%s",
            yaml.dump(config_body),
        )

        custom_api = client.CustomObjectsApi()

        try:
            custom_api.create_namespaced_custom_object(
                group=SPACE_GROUP,
                version=SPACE_VERSION,
                namespace=self.config.namespace,
                plural=SPACE_PLURAL,
                body=config_body,
            )
            logger.info(f"Successfully created HyperPod Space '{self.config.name}'!")
        except Exception as e:
            logger.error(f"Failed to create HyperPod Space {self.config.name}!")
            handle_exception(e, self.config.name, self.config.namespace)

    @classmethod
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "list_spaces")
    def list(cls, namespace: Optional[str] = None) -> List["HPSpace"]:
        """List all HyperPod Spaces in the specified namespace.

        Args:
            namespace (str, optional): The Kubernetes namespace to list spaces from.
                If None, uses the default namespace from current context.

        Returns:
            List[HPSpace]: List of HPSpace instances found in the namespace

        Raises:
            Exception: If the Kubernetes API call fails or spaces cannot be retrieved
        """
        cls.verify_kube_config()
        
        if not namespace:
            namespace = get_default_namespace()

        custom_api = client.CustomObjectsApi()
        
        try:
            response = custom_api.list_namespaced_custom_object(
                group=SPACE_GROUP,
                version=SPACE_VERSION,
                namespace=namespace,
                plural=SPACE_PLURAL
                )

            spaces = []
            for item in response.get("items", []):
                # Create SpaceConfig from the Kubernetes resource
                spec = item.get("spec", {})
                config_data = {
                    "name": item["metadata"]["name"],
                    "namespace": item["metadata"]["namespace"],
                }
                
                config_data = map_kubernetes_response_to_model(item, SpaceConfig)
                space_config = SpaceConfig(**config_data)
                
                space = cls(
                    config=space_config,
                    raw_resource=item
                )
                spaces.append(space)
            
            return spaces
        except Exception as e:
            handle_exception(e, "list", namespace)

    @classmethod
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "get_space")
    def get(cls, name: str, namespace: str = "default") -> "HPSpace":
        """Get a specific HyperPod Space by name.

        Args:
            name (str): The name of the space to retrieve
            namespace (str, optional): The Kubernetes namespace. Defaults to "default".

        Returns:
            HPSpace: The space instance

        Raises:
            Exception: If the space is not found or Kubernetes API call fails
        """
        cls.verify_kube_config()

        custom_api = client.CustomObjectsApi()
        
        try:
            response = custom_api.get_namespaced_custom_object(
                group=SPACE_GROUP,
                version=SPACE_VERSION,
                namespace=namespace,
                plural=SPACE_PLURAL,
                name=name
            )

            # Use dynamic mapping based on SpaceConfig model
            config_data = map_kubernetes_response_to_model(response, SpaceConfig)
                    
            space_config = SpaceConfig(**config_data)
            
            return cls(
                config=space_config,
                raw_resource=response
            )
        except Exception as e:
            handle_exception(e, name, namespace)

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "delete_space")
    def delete(self):
        """Delete the HyperPod Space from the Kubernetes cluster.

        Raises:
            Exception: If the deletion fails or Kubernetes API call fails
        """
        self.verify_kube_config()
        logger = self.get_logger()

        custom_api = client.CustomObjectsApi()

        try:
            custom_api.delete_namespaced_custom_object(
                group=SPACE_GROUP,
                version=SPACE_VERSION,
                namespace=self.config.namespace,
                plural=SPACE_PLURAL,
                name=self.config.name
            )
            logger.info(f"Successfully deleted HyperPod Space '{self.config.name}'!")
        except Exception as e:
            logger.error(f"Failed to delete HyperPod Space {self.config.name}!")
            handle_exception(e, self.config.name, self.config.namespace)

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "update_space")
    def update(self, **kwargs):
        """Update the HyperPod Space configuration.

        Args:
            **kwargs: Configuration fields to update (e.g., desired_status="Stopped")

        Raises:
            Exception: If the update fails or Kubernetes API call fails
        """
        self.verify_kube_config()
        logger = self.get_logger()

        custom_api = client.CustomObjectsApi()

        # Update space config with the input config
        current_config = self.config.model_dump(by_alias=True)
        current_config.update(kwargs)
        self.config = SpaceConfig(**current_config)

        # Convert to domain model and extract spec
        domain_config = self.config.to_domain()
        spec_updates = domain_config["space_spec"]["spec"]

        try:
            custom_api.patch_namespaced_custom_object(
                group=SPACE_GROUP,
                version=SPACE_VERSION,
                namespace=self.config.namespace,
                plural=SPACE_PLURAL,
                name=self.config.name,
                body={"spec": spec_updates}
            )
            logger.info(f"Successfully updated HyperPod Space '{self.config.name}'!")
        except Exception as e:
            logger.error(f"Failed to update HyperPod Space {self.config.name}!")
            handle_exception(e, self.config.name, self.config.namespace)

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "start_space")
    def start(self):
        """Start the HyperPod Space by setting desired status to Running."""
        self.update(desired_status="Running")

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "stop_space")
    def stop(self):
        """Stop the HyperPod Space by setting desired status to Stopped."""
        self.update(desired_status="Stopped")

    def list_pods(self) -> List[str]:
        """List all pods associated with this space.

        Returns:
            List[str]: List of pod names associated with the space
        """
        self.verify_kube_config()
        logger = self.get_logger()
        
        v1 = client.CoreV1Api()
        
        try:
            pods = v1.list_namespaced_pod(
                namespace=self.config.namespace,
                label_selector=f"{SPACE_GROUP}/workspaceName={self.config.name}"
            )
            return [pod.metadata.name for pod in pods.items]
        except Exception as e:
            handle_exception(e, self.config.name, self.config.namespace)

    def get_logs(self, pod_name: Optional[str] = None, container: Optional[str] = None) -> str:
        """Get logs from a pod associated with this space.

        Args:
            pod_name (str, optional): Name of the pod to get logs from. 
                If None, gets logs from the first available pod.
            container (str, optional): Name of the container to get logs from.

        Returns:
            str: The pod logs
        """
        self.verify_kube_config()
        logger = self.get_logger()

        if not pod_name:
            pods = self.list_pods()
            if not pods:
                raise RuntimeError(f"No pods found for space '{self.config.name}'")
            pod_name = pods[0]

        v1 = client.CoreV1Api()
        
        try:
            if container:
                logs = v1.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=self.config.namespace,
                    container=container
                )
            else:
                logs = v1.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=self.config.namespace
                )
            return logs
        except Exception as e:
            handle_exception(e, pod_name, self.config.namespace)
