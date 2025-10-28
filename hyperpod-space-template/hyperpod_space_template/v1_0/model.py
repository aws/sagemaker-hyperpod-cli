from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Dict, Literal
from enum import Enum


# TODO: Temporarily removed for private beta
# class VolumeConfig(BaseModel):
#     name: str = Field(
#         ..., 
#         description="Volume name",
#         min_length=1
#     )
#     type: Literal['hostPath', 'pvc'] = Field(..., description="Volume type")
#     mount_path: str = Field(
#         ..., 
#         description="Mount path in container",
#         min_length=1
#     )
#     path: Optional[str] = Field(
#         None, 
#         description="Host path (required for hostPath volumes)",
#         min_length=1
#     )
#     claim_name: Optional[str] = Field(
#         None, 
#         description="PVC claim name (required for pvc volumes)",
#         min_length=1
#     )
#     read_only: Optional[Literal['true', 'false']] = Field(None, description="Read-only flag for pvc volumes")


class SharedStatus(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class Application(str, Enum):
    JUPYTER = "jupyter"
    CODE_EDITOR = "code-editor"


class ResourcesConfig(BaseModel):
    memory: Optional[str] = Field(default="1Gi", description="Memory limit")
    cpu: Optional[str] = Field(default="500m", description="CPU limit")
    nvidia_gpu: Optional[str] = Field(default=None, alias="nvidia.com/gpu", description="GPU limit")


class SpaceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description="Dev space name",
        min_length=1,
        max_length=63,
        pattern=r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
    )
    image: Optional[str] = Field(
        default="public.ecr.aws/sagemaker/sagemaker-distribution:3.2.0-cpu",
        description="Container image for the space",
        min_length=1
    )
    namespace: str = Field(
        default="default",
        description="Kubernetes namespace",
        min_length=1
    )
    desired_status: Optional[Literal['Running', 'Stopped']] = Field(
        default="Running",
        alias="desired_status",
        description="Desired status of the space"
    )
    service_account_name: Optional[str] = Field(
        default="default",
        alias="service_account_name",
        description="Service account name",
        min_length=1
    )
    resources: Optional[ResourcesConfig] = Field(
        default=ResourcesConfig(),
        description="Resource limit"
    )
    storage_class_name: Optional[str] = Field(
        default=None,
        alias="storage_class_name",
        description="Storage class name",
        min_length=1
    )
    storage_size: Optional[str] = Field(
        default=None,
        alias="storage_size",
        description="Storage size (e.g., '10Gi')",
        min_length=1
    )
    shared_status: Optional[SharedStatus] = Field(
        default=SharedStatus.PRIVATE,
        description="Space shared setting (private | public)"
    )
    application: Optional[Application] = Field(
        default=Application.JUPYTER,
        description="Application to run in the container (jupyter | code-editor)"
    )
    # TODO: Temporarily removed for private beta
    # queue_name: Optional[str] = Field(
    #     default=None,
    #     alias="queue_name",
    #     description="Queue name for scheduling",
    #     min_length=1,
    #     max_length=63,
    #     pattern=r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
    # )
    # priority: Optional[str] = Field(
    #     default=None,
    #     description="Priority class for scheduling",
    #     min_length=1
    # )
    # volume: Optional[List[VolumeConfig]] = Field(
    #     default=None, description="List of volume configurations. \
    #     Command structure: --volume name=<volume_name>,type=<volume_type>,mount_path=<mount_path>,<type-specific options> \
    #     For hostPath: --volume name=model-data,type=hostPath,mount_path=/data,path=/data  \
    #     For persistentVolumeClaim: --volume name=training-output,type=pvc,mount_path=/mnt/output,claim_name=training-output-pvc,read_only=false \
    #     If multiple --volume flag if multiple volumes are needed \
    #     "
    # )

    # @field_validator('volume')
    # def validate_no_duplicates(cls, v):
    #     """Validate no duplicate volume names or mount paths."""
    #     if not v:
    #         return v
        
    #     # Check for duplicate volume names
    #     names = [vol.name for vol in v]
    #     if len(names) != len(set(names)):
    #         raise ValueError("Duplicate volume names found")
        
    #     # Check for duplicate mount paths
    #     mount_paths = [vol.mount_path for vol in v]
    #     if len(mount_paths) != len(set(mount_paths)):
    #         raise ValueError("Duplicate mount paths found")
        
    #     return v

    def to_domain(self) -> Dict:
        """
        Convert flat config to domain model for space creation
        """
        # Create the space spec
        spec = {
            "image": self.image
        }

        # Add optional spec fields
        if self.desired_status is not None:
            spec["desiredStatus"] = self.desired_status
        if self.service_account_name is not None:
            spec["serviceAccountName"] = self.service_account_name
        if self.resources is not None:
            spec["resources"] = self.resources.model_dump(exclude_none=True)
        if self.storage_class_name is not None:
            spec["storageClassName"] = self.storage_class_name
        if self.storage_size is not None:
            spec["storageSize"] = self.storage_size
        if self.shared_status is not None:
            spec["sharedStatus"] = self.shared_status.value
        if self.application is not None:
            spec["application"] = self.application.value

        # Create metadata
        metadata = {"name": self.name}
        if self.namespace is not None:
            metadata["namespace"] = self.namespace

        # Add labels for scheduling
        # labels = {}
        # if self.queue_name is not None:
        #     labels["kueue.x-k8s.io/queue-name"] = self.queue_name
        # if self.priority is not None:
        #     labels["kueue.x-k8s.io/priority-class"] = self.priority
        
        # if labels:
        #     metadata["labels"] = labels

        # Create the complete space configuration
        space_config = {
            "apiVersion": "sagemaker.aws.com/v1alpha1",
            "kind": "Space",
            "metadata": metadata,
            "spec": spec
        }

        return {
            "name": self.name,
            "namespace": self.namespace,
            "space_spec": space_config
        }
