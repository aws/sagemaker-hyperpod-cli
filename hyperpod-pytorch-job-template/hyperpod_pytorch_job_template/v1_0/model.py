from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional, List, Dict, Union, Literal
from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_unified_config import (
    Containers,
    ReplicaSpec,
    Resources,
    RunPolicy,
    Spec,
    Template,
    Metadata,
    Volumes,
    HostPath, 
    PersistentVolumeClaim
)


class VolumeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(
        ..., 
        description="Volume name",
        min_length=1
    )
    type: Literal['hostPath', 'pvc'] = Field(..., description="Volume type")
    mount_path: str = Field(
        ..., 
        description="Mount path in container",
        min_length=1
    )
    path: Optional[str] = Field(
        None, 
        description="Host path (required for hostPath volumes)",
        min_length=1
    )
    claim_name: Optional[str] = Field(
        None, 
        description="PVC claim name (required for pvc volumes)",
        min_length=1
    )
    read_only: Optional[Literal['true', 'false']] = Field(None, description="Read-only flag for pvc volumes")
    
    @field_validator('mount_path', 'path')
    @classmethod
    def paths_must_be_absolute(cls, v):
        """Validate that paths are absolute (start with /)."""
        if v and not v.startswith('/'):
            raise ValueError('Path must be absolute (start with /)')
        return v
    
    @model_validator(mode='after')
    def validate_type_specific_fields(self):
        """Validate that required fields are present based on volume type."""
        
        if self.type == 'hostPath':
            if not self.path:
                raise ValueError('hostPath volumes require path field')
        elif self.type == 'pvc':
            if not self.claim_name:
                raise ValueError('PVC volumes require claim_name field')
        
        return self


class PyTorchJobConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_name: str = Field(
        alias="job_name", 
        description="Job name",
        min_length=1,
        max_length=63,
        pattern=r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
    )
    image: str = Field(
        description="Docker image for training",
        min_length=1
    )
    namespace: Optional[str] = Field(
        default="default", 
        description="Kubernetes namespace",
        min_length=1
    )
    command: Optional[List[str]] = Field(
        default=None, description="Command to run in the container"
    )
    args: Optional[List[str]] = Field(
        default=None, alias="args", description="Arguments for the entry script"
    )
    environment: Optional[Dict[str, str]] = Field(
        default=None, description="Environment variables as key_value pairs"
    )
    pull_policy: Optional[str] = Field(
        default=None, 
        alias="pull_policy", 
        description="Image pull policy",
        min_length=1
    )
    instance_type: Optional[str] = Field(
        default=None, 
        alias="instance_type", 
        description="Instance type for training",
        min_length=1
    )
    node_count: Optional[int] = Field(
        default=1, 
        alias="node_count", 
        description="Number of nodes",
        ge=1
    )
    tasks_per_node: Optional[int] = Field(
        default=None, 
        alias="tasks_per_node", 
        description="Number of tasks per node",
        ge=1
    )
    label_selector: Optional[Dict[str, str]] = Field(
        default=None,
        alias="label_selector",
        description="Node label selector as key_value pairs",
    )
    deep_health_check_passed_nodes_only: Optional[bool] = Field(
        default=False,
        alias="deep_health_check_passed_nodes_only",
        description="Schedule pods only on nodes that passed deep health check",
    )
    scheduler_type: Optional[str] = Field(
        default=None, 
        alias="scheduler_type", 
        description="If specified, training job pod will be dispatched by specified scheduler. If not specified, the pod will be dispatched by default scheduler.",
        min_length=1
    )
    queue_name: Optional[str] = Field(
        default=None, 
        alias="queue_name", 
        description="Queue name for job scheduling",
        min_length=1,
        max_length=63,
        pattern=r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
    )
    priority: Optional[str] = Field(
        default=None, 
        description="Priority class for job scheduling",
        min_length=1
    )
    max_retry: Optional[int] = Field(
        default=None, 
        alias="max_retry", 
        description="Maximum number of job retries",
        ge=0
    )
    volume: Optional[List[VolumeConfig]] = Field(
        default=None, description="List of volume configurations. \
        Command structure: --volume name=<volume_name>,type=<volume_type>,mount_path=<mount_path>,<type-specific options> \
        For hostPath: --volume name=model-data,type=hostPath,mount_path=/data,path=/data  \
        For persistentVolumeClaim: --volume name=training-output,type=pvc,mount_path=/mnt/output,claim_name=training-output-pvc,read_only=false \
        If multiple --volume flag if multiple volumes are needed \
        "
    )
    service_account_name: Optional[str] = Field(
        default=None, 
        alias="service_account_name", 
        description="Service account name",
        min_length=1
    )

    @field_validator('volume')
    def validate_no_duplicates(cls, v):
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

    @field_validator('command', 'args')
    def validate_string_lists(cls, v):
        """Validate that command and args contain non-empty strings."""
        if not v:
            return v
        
        for i, item in enumerate(v):
            if not isinstance(item, str) or not item.strip():
                field_name = cls.model_fields.get('command', {}).get('alias', 'command') if 'command' in str(v) else 'args'
                raise ValueError(f"{field_name}[{i}] must be a non-empty string")
        
        return v

    @field_validator('environment')
    def validate_environment_variable_names(cls, v):
        """Validate environment variable names follow C_IDENTIFIER pattern."""
        if not v:
            return v
        
        import re
        c_identifier_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        
        for key in v.keys():
            if not c_identifier_pattern.match(key):
                raise ValueError(f"Environment variable name '{key}' must be a valid C_IDENTIFIER")
        
        return v

    @field_validator('label_selector')
    def validate_label_selector_keys(cls, v):
        """Validate label selector keys follow Kubernetes label naming conventions."""
        if not v:
            return v
        
        import re
        # Kubernetes label key pattern - allows namespaced labels like kubernetes.io/arch
        # Pattern: [prefix/]name where prefix and name follow DNS subdomain rules
        # Also reject double dots
        label_key_pattern = re.compile(r'^([a-zA-Z0-9]([a-zA-Z0-9\-_.]*[a-zA-Z0-9])?/)?[a-zA-Z0-9]([a-zA-Z0-9\-_.]*[a-zA-Z0-9])?$')
        
        for key in v.keys():
            if not key or not label_key_pattern.match(key) or '..' in key:
                raise ValueError(f"Label selector key '{key}' must follow Kubernetes label naming conventions")
        
        return v

    def to_domain(self) -> Dict:
        """
        Convert flat config to domain model (HyperPodPytorchJobSpec)
        """
        
        # Create container with required fields
        container_kwargs = {
            "name": "pytorch-job-container",
            "image": self.image,
            "resources": Resources(
                requests={"nvidia.com/gpu": "0"},
                limits={"nvidia.com/gpu": "0"},
            ),
        }

        # Add optional container fields
        if self.command is not None:
            container_kwargs["command"] = self.command
        if self.args is not None:
            container_kwargs["args"] = self.args
        if self.pull_policy is not None:
            container_kwargs["image_pull_policy"] = self.pull_policy
        if self.environment is not None:
            container_kwargs["env"] = [
                {"name": k, "value": v} for k, v in self.environment.items()
            ]

        if self.volume is not None:
            volume_mounts = []
            for i, vol in enumerate(self.volume):
                volume_mount = {"name": vol.name, "mount_path": vol.mount_path}
                volume_mounts.append(volume_mount)
            
            container_kwargs["volume_mounts"] = volume_mounts


        # Create container object
        try:
            container = Containers(**container_kwargs)
        except Exception as e:
            raise

        # Create pod spec kwargs
        spec_kwargs = {"containers": list([container])}

        # Add volumes to pod spec if present
        if self.volume is not None:
            volumes = []
            for i, vol in enumerate(self.volume):
                if vol.type == "hostPath":
                    host_path = HostPath(path=vol.path)
                    volume_obj = Volumes(name=vol.name, host_path=host_path)
                elif vol.type == "pvc":
                    pvc_config = PersistentVolumeClaim(
                         claim_name=vol.claim_name,
                         read_only=vol.read_only == "true" if vol.read_only else False
                    )
                    volume_obj = Volumes(name=vol.name, persistent_volume_claim=pvc_config)
                volumes.append(volume_obj)
            
            spec_kwargs["volumes"] = volumes
        
        # Add node selector if any selector fields are present
        node_selector = {}
        if self.instance_type is not None:
            map = {"node.kubernetes.io/instance-type": self.instance_type}
            node_selector.update(map)
        if self.label_selector is not None:
            node_selector.update(self.label_selector)
        if self.deep_health_check_passed_nodes_only:
            map = {"deep-health-check-passed": "true"}
            node_selector.update(map)
        if node_selector:
            spec_kwargs.update({"node_selector": node_selector})

        # Add other optional pod spec fields
        if self.service_account_name is not None:
            map = {"service_account_name": self.service_account_name}
            spec_kwargs.update(map)

        if self.scheduler_type is not None:
            map = {"scheduler_name": self.scheduler_type}
            spec_kwargs.update(map)

        # Build metadata labels only if relevant fields are present
        metadata_kwargs = {"name": self.job_name}
        if self.namespace is not None:
            metadata_kwargs["namespace"] = self.namespace

        metadata_labels = {}
        if self.queue_name is not None:
            metadata_labels["kueue.x-k8s.io/queue-name"] = self.queue_name
        if self.priority is not None:
            metadata_labels["kueue.x-k8s.io/priority-class"] = self.priority

        if metadata_labels:
            metadata_kwargs["labels"] = metadata_labels

        # Create replica spec with only non-None values
        replica_kwargs = {
            "name": "pod",
            "template": Template(
                metadata=Metadata(**metadata_kwargs), spec=Spec(**spec_kwargs)
            ),
        }

        if self.node_count is not None:
            replica_kwargs["replicas"] = self.node_count

        replica_spec = ReplicaSpec(**replica_kwargs)

        replica_specs = list([replica_spec])

        job_kwargs = {"replica_specs": replica_specs}
        # Add optional fields only if they exist
        if self.tasks_per_node is not None:
            job_kwargs["nproc_per_node"] = str(self.tasks_per_node)

        if self.max_retry is not None:
            job_kwargs["run_policy"] = RunPolicy(
                clean_pod_policy="None", job_max_retry_count=self.max_retry
            )

        # Create base return dictionary
        result = {
            "name": self.job_name,
            "namespace": self.namespace,
            "labels": metadata_labels,
            "spec": job_kwargs,
        }
        return result