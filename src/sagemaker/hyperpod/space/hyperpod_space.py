import logging
import yaml
import boto3
from typing import List, Optional, ClassVar, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from sagemaker.hyperpod.common.config.metadata import Metadata
from sagemaker.hyperpod.common.utils import (
    handle_exception,
    get_default_namespace,
    setup_logging,
    verify_kubernetes_version_compatibility,
    get_current_cluster,
    get_current_region,
    get_cluster_instance_types,
)
from sagemaker.hyperpod.space.utils import (
    map_kubernetes_response_to_model,
    get_pod_instance_type,
)
from sagemaker.hyperpod.common.telemetry.telemetry_logging import (
    _hyperpod_telemetry_emitter,
)
from sagemaker.hyperpod.common.telemetry.constants import Feature
from sagemaker.hyperpod.cli.constants.space_constants import (
    SPACE_GROUP,
    SPACE_VERSION,
    SPACE_PLURAL,
    ENABLE_MIG_PROFILE_VALIDATION,
)
from sagemaker.hyperpod.cli.constants.space_access_constants import (
    SPACE_ACCESS_GROUP,
    SPACE_ACCESS_VERSION,
    SPACE_ACCESS_PLURAL,
)
from hyperpod_space_template.v1_0.model import SpaceConfig

if ENABLE_MIG_PROFILE_VALIDATION:
    from sagemaker.hyperpod.training.hyperpod_pytorch_job import list_accelerator_partition_types


class HPSpace(BaseModel):
    """HyperPod Space on Amazon SageMaker HyperPod clusters.

    This class provides methods to create, manage, and monitor spaces
    on SageMaker HyperPod clusters orchestrated by Amazon EKS. Spaces are
    interactive workspaces that provide development environments with
    configurable resources, storage, and access controls.

    **Attributes:**

    .. list-table::
       :header-rows: 1
       :widths: 20 20 60

       * - Attribute
         - Type
         - Description
       * - config
         - SpaceConfig
         - The space configuration using the space parameter model
       * - raw_resource
         - Dict[str, Any], optional
         - The complete Kubernetes resource data including apiVersion, kind, metadata, and status

    .. dropdown:: Usage Examples
       :open:

       .. code-block:: python

          >>> # Create a new space
          >>> from hyperpod_space_template.v1_0.model import SpaceConfig
          >>> config = SpaceConfig(name="my-space", display_name="My Space")
          >>> space = HPSpace(config=config)
          >>> space.create()
          
          >>> # List all spaces
          >>> spaces = HPSpace.list()
          >>> for space in spaces:
          ...     print(f"Space: {space.config.name}")
    """
    
    is_kubeconfig_loaded: ClassVar[bool] = False
    model_config = ConfigDict(extra="forbid")

    config: SpaceConfig = Field(
        description="The space configuration using the space parameter model"
    )
    
    raw_resource: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The complete Kubernetes resource data including apiVersion, kind, metadata, and status"
    )

    @classmethod
    def get_logger(cls):
        """Get logger for the HPSpace class.

        **Returns:**

        logging.Logger: Logger instance configured for the HPSpace class

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> logger = HPSpace.get_logger()
              >>> logger.info("Space operation completed")
        """
        return logging.getLogger(__name__)

    @property
    def api_version(self) -> Optional[str]:
        """Get the apiVersion from the Kubernetes resource.

        **Returns:**

        str or None: The API version of the Kubernetes resource, or None if raw_resource is not available

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> space = HPSpace.get("my-space")
              >>> print(f"API Version: {space.api_version}")
        """
        return self.raw_resource.get("apiVersion") if self.raw_resource else None

    @property
    def kind(self) -> Optional[str]:
        """Get the kind from the Kubernetes resource.

        **Returns:**

        str or None: The kind of the Kubernetes resource, or None if raw_resource is not available

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> space = HPSpace.get("my-space")
              >>> print(f"Resource Kind: {space.kind}")
        """
        return self.raw_resource.get("kind") if self.raw_resource else None

    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        """Get the metadata from the Kubernetes resource.

        **Returns:**

        Dict[str, Any] or None: The metadata section of the Kubernetes resource, or None if raw_resource is not available

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> space = HPSpace.get("my-space")
              >>> print(f"Creation Time: {space.metadata['creationTimestamp']}")
        """
        return self.raw_resource.get("metadata") if self.raw_resource else None

    @property
    def status(self) -> Optional[Dict[str, Any]]:
        """Get the status from the Kubernetes resource.

        **Returns:**

        Dict[str, Any] or None: The status section of the Kubernetes resource, or None if raw_resource is not available

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> space = HPSpace.get("my-space")
              >>> conditions = space.status.get('conditions', [])
              >>> for condition in conditions:
              ...     print(f"{condition['type']}: {condition['status']}")
        """
        return self.raw_resource.get("status") if self.raw_resource else None

    @classmethod
    def verify_kube_config(cls):
        """Verify and load Kubernetes configuration.

        Loads the Kubernetes configuration from the default kubeconfig location
        and verifies compatibility with the cluster. This method is called
        automatically by other methods that interact with the Kubernetes API.

        **Raises:**

        RuntimeError: If the kubeconfig cannot be loaded or is invalid

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Verify kubeconfig before operations
              >>> HPSpace.verify_kube_config()
        """
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

        Creates a new space resource in the Kubernetes cluster based on the
        configuration provided in the space config. Validates MIG profiles
        if enabled and converts the configuration to the appropriate domain model.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - debug
             - bool, optional
             - Enable debug logging (default: False)

        **Raises:**

        RuntimeError: If MIG profile validation fails or unsupported profiles are used
        Exception: If the space creation fails or Kubernetes API call fails

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Create a space with debug logging
              >>> space = HPSpace(config=space_config)
              >>> space.create(debug=True)
              
              >>> # Create a space with default settings
              >>> space.create()
        """

        self.verify_kube_config()
        
        logger = self.get_logger()
        logger = setup_logging(logger, debug)

        # Validate supported MIG profiles for the cluster
        if ENABLE_MIG_PROFILE_VALIDATION:
            if self.config.resources:
                mig_profiles = set()
                if self.config.resources.requests:
                    mig_profiles.update([key for key in self.config.resources.requests.keys() if key.startswith("nvidia.com/mig")])
                if self.config.resources.limits:
                    mig_profiles.update([key for key in self.config.resources.limits.keys() if key.startswith("nvidia.com/mig")])

                if len(mig_profiles) > 1:
                    raise RuntimeError("Space only supports one MIG profile")

                if mig_profiles:
                    cluster_instance_types = get_cluster_instance_types(
                        get_current_cluster(),
                        get_current_region()
                    )
                    supported_mig_profiles = {profile for instance_type in cluster_instance_types for profile in list_accelerator_partition_types(instance_type)}
                    if list(mig_profiles)[0] not in supported_mig_profiles:
                        raise RuntimeError(f"Accelerator partition type '{list(mig_profiles)[0]}' does not exist in this cluster. Use 'hyp list-accelerator-partition-type' to check for available resources.")

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
            logger.debug(f"Successfully created HyperPod Space '{self.config.name}'!")
        except Exception as e:
            logger.error(f"Failed to create HyperPod Space {self.config.name}!")
            handle_exception(e, self.config.name, self.config.namespace, debug=debug)

    @classmethod
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "list_spaces")
    def list(cls, namespace: Optional[str] = None) -> List["HPSpace"]:
        """List all HyperPod Spaces in the specified namespace created by the caller.

        Retrieves all spaces that were either created by the current caller (based on
        AWS STS identity) or are marked as 'Public' ownership type. Uses pagination
        to handle large numbers of spaces efficiently.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - namespace
             - str, optional
             - The Kubernetes namespace to list spaces from. If None, uses the default namespace from current context

        **Returns:**

        List[HPSpace]: List of HPSpace instances created by the caller or marked as public

        **Raises:**

        Exception: If the Kubernetes API call fails or spaces cannot be retrieved

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # List spaces in default namespace
              >>> spaces = HPSpace.list()
              >>> print(f"Found {len(spaces)} spaces")
              
              >>> # List spaces in specific namespace
              >>> spaces = HPSpace.list(namespace="my-namespace")
              >>> for space in spaces:
              ...     print(f"Space: {space.config.name}")
        """
        cls.verify_kube_config()
        
        if not namespace:
            namespace = get_default_namespace()

        # Get caller identity
        sts_client = boto3.client('sts')
        caller_identity = sts_client.get_caller_identity()
        caller_arn = caller_identity['Arn']

        custom_api = client.CustomObjectsApi()
        spaces = []
        continue_token = None
        
        try:
            while True:
                response = custom_api.list_namespaced_custom_object(
                    group=SPACE_GROUP,
                    version=SPACE_VERSION,
                    namespace=namespace,
                    plural=SPACE_PLURAL,
                    _continue=continue_token
                )

                for item in response.get("items", []):
                    # Check if space was created by the caller or it's set as 'Public'
                    created_by = item.get('metadata', {}).get('annotations', {}).get('workspace.jupyter.org/created-by')
                    ownership_type = item.get('spec', {}).get('ownershipType', '')
                    if created_by == caller_arn or ownership_type == "Public":
                        config_data = map_kubernetes_response_to_model(item, SpaceConfig)
                        space_config = SpaceConfig(**config_data)
                        
                        space = cls(
                            config=space_config,
                            raw_resource=item
                        )
                        spaces.append(space)

                # Check if there are more pages
                continue_token = response.get('metadata', {}).get('continue')
                if not continue_token:
                    break
            
            return spaces
        except Exception as e:
            handle_exception(e, "list", namespace)

    @classmethod
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "get_space")
    def get(cls, name: str, namespace: str = None) -> "HPSpace":
        """Get a specific HyperPod Space by name.

        Retrieves a single space resource from the Kubernetes cluster and maps
        the response to the SpaceConfig model for easy access to configuration
        and status information.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - name
             - str
             - The name of the space to retrieve
           * - namespace
             - str, optional
             - The Kubernetes namespace. If None, uses the default namespace from current context

        **Returns:**

        HPSpace: The space instance with configuration and raw Kubernetes resource data

        **Raises:**

        Exception: If the space is not found or Kubernetes API call fails

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Get space from default namespace
              >>> space = HPSpace.get("my-space")
              >>> print(f"Space status: {space.status}")
              
              >>> # Get space from specific namespace
              >>> space = HPSpace.get("my-space", namespace="production")
              >>> print(f"Display name: {space.config.display_name}")
        """
        cls.verify_kube_config()

        if not namespace:
            namespace = get_default_namespace()

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

        Permanently removes the space resource from the Kubernetes cluster.
        This operation cannot be undone and will terminate any running
        workloads associated with the space.

        **Raises:**

        Exception: If the deletion fails or Kubernetes API call fails

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Delete a space
              >>> space = HPSpace.get("my-space")
              >>> space.delete()
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
            logger.debug(f"Successfully deleted HyperPod Space '{self.config.name}'!")
        except Exception as e:
            logger.error(f"Failed to delete HyperPod Space {self.config.name}!")
            handle_exception(e, self.config.name, self.config.namespace)

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "update_space")
    def update(self, **kwargs):
        """Update the HyperPod Space configuration.

        Updates the space configuration with the provided parameters. Validates
        MIG profiles if resource updates are requested and ensures compatibility
        with the current node instance type.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - **kwargs
             - Any
             - Configuration fields to update (e.g., desired_status="Stopped", display_name="New Name")

        **Raises:**

        RuntimeError: If MIG profile validation fails or unsupported profiles are used
        Exception: If the update fails or Kubernetes API call fails

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Update space status
              >>> space = HPSpace.get("my-space")
              >>> space.update(desired_status="Stopped")
              
              >>> # Update display name and resources
              >>> space.update(
              ...     display_name="Updated Space",
              ...     resources={"requests": {"cpu": "2", "memory": "4Gi"}}
              ... )
        """
        self.verify_kube_config()
        logger = self.get_logger()

        # Validate supported MIG profile for node which the Space is running on
        if ENABLE_MIG_PROFILE_VALIDATION:
            if "resources" in kwargs:
                mig_profiles = set()
                mig_profiles.update([key for key in kwargs["resources"].get("requests", {}).keys() if key.startswith("nvidia.com/mig")])
                mig_profiles.update([key for key in kwargs["resources"].get("limits", {}).keys() if key.startswith("nvidia.com/mig")])

                if len(mig_profiles) > 1:
                    raise RuntimeError("Space only supports one MIG profile")

                if mig_profiles:
                    pods = self.list_pods()
                    if not pods:
                        raise RuntimeError(f"No pods found for space '{self.config.name}'")

                    node_instance_type = get_pod_instance_type(pods[0], self.config.namespace)
                    supported_mig_profiles = set(list_accelerator_partition_types(node_instance_type))
                    if list(mig_profiles)[0] not in supported_mig_profiles:
                        raise RuntimeError(f"Accelerator partition type '{list(mig_profiles)[0]}' does not exist in this cluster. Use 'hyp list-accelerator-partition-type' to check for available resources.")

                    # Ensure existing MIG profile gets removed before setting a new one
                    existing_config = HPSpace.get(self.config.name, self.config.namespace).config
                    existing_mig_profiles = [key for key in existing_config.resources.requests.keys() if key.startswith("nvidia.com/mig")]
                    if existing_mig_profiles:
                        kwargs["resources"]["requests"].update({existing_mig_profiles[0]: None})
                        kwargs["resources"]["limits"].update({existing_mig_profiles[0]: None})

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
            logger.debug(f"Successfully updated HyperPod Space '{self.config.name}'!")
        except Exception as e:
            logger.error(f"Failed to update HyperPod Space {self.config.name}!")
            handle_exception(e, self.config.name, self.config.namespace)

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "start_space")
    def start(self):
        """Start the HyperPod Space by setting desired status to Running.

        Convenience method that updates the space's desired status to "Running",
        which will cause the Kubernetes operator to start the space workloads.

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Start a space
              >>> space = HPSpace.get("my-space")
              >>> space.start()
        """
        self.update(desired_status="Running")

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "stop_space")
    def stop(self):
        """Stop the HyperPod Space by setting desired status to Stopped.

        Convenience method that updates the space's desired status to "Stopped",
        which will cause the Kubernetes operator to stop the space workloads.

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Stop a space
              >>> space = HPSpace.get("my-space")
              >>> space.stop()
        """
        self.update(desired_status="Stopped")

    def list_pods(self) -> List[str]:
        """List all pods associated with this space.

        Retrieves all Kubernetes pods that are labeled as belonging to this
        space using the workspace-name label selector.

        **Returns:**

        List[str]: List of pod names associated with the space

        **Raises:**

        Exception: If the Kubernetes API call fails

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # List pods for a space
              >>> space = HPSpace.get("my-space")
              >>> pods = space.list_pods()
              >>> print(f"Found {len(pods)} pods: {pods}")
        """
        self.verify_kube_config()
        logger = self.get_logger()

        v1 = client.CoreV1Api()

        try:
            pods = v1.list_namespaced_pod(
                namespace=self.config.namespace,
                label_selector=f"{SPACE_GROUP}/workspace-name={self.config.name}"
            )
            return [pod.metadata.name for pod in pods.items]
        except Exception as e:
            handle_exception(e, self.config.name, self.config.namespace)

    def get_logs(self, pod_name: Optional[str] = None, container: Optional[str] = None) -> str:
        """Get logs from a pod associated with this space.

        Retrieves logs from a specific pod and container. If no pod is specified,
        uses the first available pod. If no container is specified, defaults to
        the "workspace" container.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - pod_name
             - str, optional
             - Name of the pod to get logs from. If None, gets logs from the first available pod
           * - container
             - str, optional
             - Name of the container to get logs from. Defaults to "workspace"

        **Returns:**

        str: The pod logs as a string

        **Raises:**

        RuntimeError: If no pods are found for the space
        Exception: If the Kubernetes API call fails

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Get logs from default pod and container
              >>> space = HPSpace.get("my-space")
              >>> logs = space.get_logs()
              >>> print(logs)
              
              >>> # Get logs from specific pod and container
              >>> logs = space.get_logs(pod_name="my-pod", container="sidecar")
        """
        self.verify_kube_config()
        logger = self.get_logger()

        if not pod_name:
            pods = self.list_pods()
            if not pods:
                raise RuntimeError(f"No pods found for space '{self.config.name}'")
            pod_name = pods[0]

        if not container:
            container = "workspace"

        v1 = client.CoreV1Api()
        
        try:
            return v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=self.config.namespace,
                container=container
            )
        except Exception as e:
            handle_exception(e, pod_name, self.config.namespace)

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "create_space_access")
    def create_space_access(self, connection_type: str = "vscode-remote") -> Dict[str, str]:
        """Create a space access for this space.

        Creates a space access resource that provides remote connection capabilities
        to the space. Supports VS Code remote development and web UI access types.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - connection_type
             - str, optional
             - The IDE type for remote access. Must be "vscode-remote" or "web-ui" (default: "vscode-remote")

        **Returns:**

        Dict[str, str]: Dictionary containing 'SpaceConnectionType' and 'SpaceConnectionUrl' keys

        **Raises:**

        ValueError: If connection_type is not "vscode-remote" or "web-ui"
        Exception: If the space access creation fails or Kubernetes API call fails

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Create VS Code remote access
              >>> space = HPSpace.get("my-space")
              >>> access = space.create_space_access("vscode-remote")
              >>> print(f"Connection URL: {access['SpaceConnectionUrl']}")
              
              >>> # Create web UI access
              >>> access = space.create_space_access("web-ui")
              >>> print(f"Web UI URL: {access['SpaceConnectionUrl']}")
        """
        self.verify_kube_config()
        logger = self.get_logger()

        if connection_type not in {"vscode-remote", "web-ui"}:
            raise ValueError("--connection-type must be 'vscode-remote' or 'web-ui'.")

        config = {
            "metadata": {
                "namespace": self.config.namespace,
            },
            "spec": {
                "workspaceName": self.config.name,
                "workspaceConnectionType": connection_type,
            }
        }

        custom_api = client.CustomObjectsApi()

        try:
            response = custom_api.create_namespaced_custom_object(
                group=SPACE_ACCESS_GROUP,
                version=SPACE_ACCESS_VERSION,
                namespace=self.config.namespace,
                plural=SPACE_ACCESS_PLURAL,
                body=config
            )
            logger.debug(f"Successfully created space access for '{self.config.name}'!")
            return {
                "SpaceConnectionType": connection_type,
                "SpaceConnectionUrl": response["status"]["workspaceConnectionUrl"]
            }
        except Exception as e:
            logger.error(f"Failed to create space access for {self.config.name}!")
            handle_exception(e, self.config.name, self.config.namespace)