from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Dict, Literal, Any
from enum import Enum


class OwnershipType(str, Enum):
    PUBLIC = "Public"
    OWNER_ONLY = "OwnerOnly"


class DesiredStatus(str, Enum):
    RUNNING = "Running"
    STOPPED = "Stopped"


class VolumeSpec(BaseModel):
    """VolumeSpec defines a volume to mount from an existing PVC"""
    name: str = Field(
        description="Name is a unique identifier for this volume within the pod (maps to pod.spec.volumes[].name)",
        min_length=1
    )
    mount_path: str = Field(
        alias="mountPath",
        description="MountPath is the path where the volume should be mounted (Unix-style path, e.g. /data)",
        min_length=1
    )
    persistent_volume_claim_name: str = Field(
        alias="persistentVolumeClaimName",
        description="PersistentVolumeClaimName is the name of the existing PVC to mount",
        min_length=1
    )


class ContainerConfig(BaseModel):
    """ContainerConfig defines container command and args configuration"""
    command: Optional[List[str]] = Field(
        default=None,
        description="Command specifies the container command"
    )
    args: Optional[List[str]] = Field(
        default=None,
        description="Args specifies the container arguments"
    )


class StorageSpec(BaseModel):
    """StorageSpec defines the storage configuration for Workspace"""
    storage_class_name: Optional[str] = Field(
        default=None,
        alias="storageClassName",
        description="StorageClassName specifies the storage class to use for persistent storage"
    )
    size: Optional[str] = Field(
        default="10Gi",
        description="Size specifies the size of the persistent volume. Supports standard Kubernetes resource quantities (e.g., '10Gi', '500Mi', '1Ti'). Integer values without units are interpreted as bytes"
    )
    mount_path: Optional[str] = Field(
        default="/home",
        alias="mountPath",
        description="MountPath specifies where to mount the persistent volume in the container. Default is /home/jovyan (jovyan is the standard user in Jupyter images)"
    )


class ResourceRequirements(BaseModel):
    """ResourceRequirements describes the compute resource requirements"""
    requests: Optional[Dict[str, str]] = Field(
        default=None,
        description="Requests describes the minimum amount of compute resources required. If Requests is omitted for a container, it defaults to Limits if that is explicitly specified, otherwise to an implementation-defined value. Requests cannot exceed Limits."
    )
    limits: Optional[Dict[str, str]] = Field(
        default=None,
        description="Limits describes the maximum amount of compute resources allowed."
    )


class SpaceConfig(BaseModel):
    """SpaceConfig defines the desired state of a Space"""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description="Space name",
        min_length=1,
        max_length=63,
        pattern=r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
    )
    display_name: str = Field(
        alias="display_name",
        description="Display Name of the space",
        min_length=1
    )
    namespace: str = Field(
        default="default",
        description="Kubernetes namespace",
        min_length=1
    )
    image: Optional[str] = Field(
        default=None,
        description="Image specifies the container image to use"
    )
    desired_status: Optional[DesiredStatus] = Field(
        default=None,
        alias="desired_status",
        description="DesiredStatus specifies the desired operational status"
    )
    ownership_type: Optional[OwnershipType] = Field(
        default=None,
        alias="ownership_type",
        description="OwnershipType specifies who can modify the space. Public means anyone with RBAC permissions can update/delete the space. OwnerOnly means only the creator can update/delete the space."
    )
    resources: Optional[ResourceRequirements] = Field(
        default=None,
        description="Resources specifies the resource requirements"
    )
    storage: Optional[StorageSpec] = Field(
        default=None,
        description="Storage specifies the storage configuration"
    )
    volumes: Optional[List[VolumeSpec]] = Field(
        default=None,
        description="Volumes specifies additional volumes to mount from existing PersistentVolumeClaims"
    )
    container_config: Optional[ContainerConfig] = Field(
        default=None,
        alias="container_config",
        description="ContainerConfig specifies container command and args configuration"
    )
    node_selector: Optional[Dict[str, str]] = Field(
        default=None,
        alias="node_selector",
        description="NodeSelector specifies node selection constraints for the space pod (JSON)"
    )
    affinity: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Affinity specifies node affinity and anti-affinity rules for the space pod (JSON)"
    )
    tolerations: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Tolerations specifies tolerations for the space pod to schedule on nodes with matching taints (JSON)"
    )
    lifecycle: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Lifecycle specifies actions that the management system should take in response to container lifecycle events (JSON)"
    )
    template_ref: Optional[str] = Field(
        default=None,
        alias="template_ref",
        description="TemplateRef references a WorkspaceTemplate to use as base configuration. When set, template provides defaults and spec fields (Image, Resources, Storage.Size) act as overrides."
    )

    @field_validator('volumes')
    def validate_no_duplicate_volumes(cls, v):
        """Validate no duplicate volume names or mount paths."""
        if not v:
            return v
        
        # Check for duplicate volume names
        names = [vol.name for vol in v]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate volume names found")
        
        # Check for duplicate mount paths
        mount_paths = [vol.mount_path for vol in v]
        if len(mount_paths) != len(set(mount_paths)):
            raise ValueError("Duplicate mount paths found")
        
        return v

    def to_domain(self) -> Dict:
        """
        Convert flat config to domain model for space creation
        """
        # Create the space spec
        spec = {
            "displayName": self.display_name
        }

        # Add optional spec fields
        if self.image is not None:
            spec["image"] = self.image
        if self.desired_status is not None:
            spec["desiredStatus"] = self.desired_status.value
        if self.ownership_type is not None:
            spec["ownershipType"] = self.ownership_type.value
        if self.resources is not None:
            spec["resources"] = self.resources.model_dump(exclude_none=True)
        if self.storage is not None:
            spec["storage"] = self.storage.model_dump(exclude_none=True, by_alias=True)
        if self.volumes is not None:
            spec["volumes"] = [vol.model_dump(exclude_none=True, by_alias=True) for vol in self.volumes]
        if self.container_config is not None:
            spec["containerConfig"] = self.container_config.model_dump(exclude_none=True)
        if self.node_selector is not None:
            spec["nodeSelector"] = self.node_selector
        if self.affinity is not None:
            spec["affinity"] = self.affinity
        if self.tolerations is not None:
            spec["tolerations"] = self.tolerations
        if self.lifecycle is not None:
            spec["lifecycle"] = self.lifecycle
        if self.template_ref is not None:
            spec["templateRef"] = self.template_ref

        # Create metadata
        metadata = {"name": self.name}
        if self.namespace is not None:
            metadata["namespace"] = self.namespace

        # Create the complete space configuration
        space_config = {
            "apiVersion": "workspace.jupyter.org/v1alpha1",
            "kind": "Workspace",
            "metadata": metadata,
            "spec": spec
        }

        return {
            "name": self.name,
            "namespace": self.namespace,
            "space_spec": space_config
        }
