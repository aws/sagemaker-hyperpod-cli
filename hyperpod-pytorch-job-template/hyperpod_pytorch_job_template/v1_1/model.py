from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional, List, Dict, Union, Literal
import click
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
    PersistentVolumeClaim,
    ElasticPolicy
)
from sagemaker.hyperpod.training.hyperpod_pytorch_job import HyperPodPytorchJob
import yaml

# Constants
ALLOWED_TOPOLOGY_LABELS = {
    'topology.k8s.aws/ultraserver-id',
    'topology.k8s.aws/network-node-layer-1',
    'topology.k8s.aws/network-node-layer-2',
    'topology.k8s.aws/network-node-layer-3'
}

from sagemaker.hyperpod.training.accelerator_partition_util import _validate_accelerator_partition_parameters
from sagemaker.hyperpod.training.constants import ALLOWED_ACCELERATOR_PARTITION_TYPES

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
    read_only: Optional[bool] = Field(None, description="Read-only flag for pvc volumes")
    
    def to_dict(self) -> dict:
        """Convert VolumeConfig to dictionary format."""
        vol_dict = {
            'name': self.name,
            'type': self.type,
            'mount_path': self.mount_path
        }
        if self.path:
            vol_dict['path'] = self.path
        if self.claim_name:
            vol_dict['claim_name'] = self.claim_name
        if self.read_only is not None:
            vol_dict['read_only'] = self.read_only
        return vol_dict

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
        default=None, 
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
        default=None,
        alias="node_count", 
        description="Number of nodes",
        ge=1
    )
    tasks_per_node: Optional[str] = Field(
        default="auto", 
        alias="tasks_per_node", 
        description="Number of workers per node; supported values: [auto,cpu, gpu, int]",
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
    accelerators: Optional[int] = Field(
        default=None,
        description="Number of accelerators a.k.a GPUs or Trainium Chips",
    )
    vcpu: Optional[float] = Field(
        default=None,
        description="Number of vCPUs",
    )
    memory: Optional[float] = Field(
        default=None,
        description="Amount of memory in GiB",
    )
    accelerators_limit: Optional[int] = Field(
        default=None,
        description="Limit for the number of accelerators a.k.a GPUs or Trainium Chips",
    )
    vcpu_limit: Optional[float] = Field(
        default=None,
        description="Limit for the number of vCPUs",
    )
    memory_limit: Optional[float] = Field(
        default=None,
        description="Limit for the amount of memory in GiB",
    )
    accelerator_partition_type: Optional[str] = Field(
        default=None,
        description="Type of accelerator partition"
    )
    accelerator_partition_count: Optional[int] = Field(
        default=None,
        description="Number of accelerator partitions to request",
        ge=1
    )
    accelerator_partition_limit: Optional[int] = Field(
        default=None,
        description="Limit for the number of accelerator partitions",
        ge=1
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
    preferred_topology: Optional[str] = Field(
        default=None,
        alias="preferred_topology",
        description="Preferred topology annotation for scheduling",
    )
    required_topology: Optional[str] = Field(
        default=None,
        alias="required_topology",
        description="Required topology annotation for scheduling",
    )
    elastic_replica_increment_step: Optional[int] = Field(
        default=None,
        alias="elastic_replica_increment_step",
        description="Scaling step size for elastic training",
        ge=1,
    )
    max_node_count: Optional[int] = Field(
        default=None,
        alias="max_node_count",
        description="Maximum number of nodes for elastic training",
        ge=1,
    )
    elastic_graceful_shutdown_timeout_in_seconds: Optional[int] = Field(
        default=None,
        alias="elastic_graceful_shutdown_timeout_in_seconds",
        description="Graceful shutdown timeout in seconds for elastic scaling operations"
    )
    elastic_scaling_timeout_in_seconds: Optional[int] = Field(
        default=None,
        alias="elastic_scaling_timeout_in_seconds",
        description="Scaling timeout for elastic training"
    )
    elastic_scale_up_snooze_time_in_seconds: Optional[int] = Field(
        default=None,
        alias="elastic_scale_up_snooze_time_in_seconds",
        description="Timeout period after job restart during which no scale up/workload admission is allowed"
    )
    elastic_replica_discrete_values: Optional[List[int]] = Field(
        default=None,
        alias="elastic_replica_discrete_values",
        description="Alternative to replica increment step. Provides exact values for total replicas count"
    )

    @field_validator('tasks_per_node', mode='before')
    @classmethod
    def validate_tasks_per_node(cls, v):
        if v is None:
            return v
        
        # Convert to string for validation
        v_str = str(v).lower()
        
        # Check if it's one of the allowed string values
        if v_str in ['auto', 'cpu', 'gpu']:
            return v_str
        
        # Check if it's a valid integer (reject floats)
        try:
            # First check if it contains a decimal point
            if '.' in str(v):
                raise ValueError("tasks_per_node must be an integer, not a float")
            
            int_val = int(v)
            if int_val >= 0:
                return str(int_val)
            else:
                raise ValueError("tasks_per_node must be non-negative")
        except (ValueError, TypeError):
            raise ValueError("tasks_per_node must be 'auto', 'cpu', 'gpu', or a non-negative integer")
        
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

    @field_validator('preferred_topology', 'required_topology')
    def validate_topology_labels(cls, v):
        """Validate topology labels are from allowed set."""
        if v is None:
            return v
        
        if v not in ALLOWED_TOPOLOGY_LABELS:
            raise ValueError(f"Topology label '{v}' must be one of: {', '.join(sorted(ALLOWED_TOPOLOGY_LABELS))}")
        
        return v

    @field_validator('accelerator_partition_type')
    def validate_accelerator_partition_type(v):
        """Basic validation for accelerator partition type."""
        if v not in ALLOWED_ACCELERATOR_PARTITION_TYPES:
            raise ValueError(f"Accelerator partition type '{v}' must be one of: {', '.join(sorted(ALLOWED_ACCELERATOR_PARTITION_TYPES))}")
        
        return v

    @model_validator(mode='after')
    def validate_accelerator_partition_options(self):
        has_accelerator_partition_parameters = (self.accelerator_partition_type is not None or self.accelerator_partition_count is not None
                                 or self.accelerator_partition_limit is not None)

        if not has_accelerator_partition_parameters:
            return self

        valid, error = _validate_accelerator_partition_parameters(
            self.accelerator_partition_type, self.accelerators, self.accelerators_limit, self.node_count, self.instance_type
        )
        if not valid:
            raise ValueError(error)
        
        return self

    @model_validator(mode='after')
    def validate_elastic_replica_config(self):
        """Validate elastic replica configuration."""
        has_increment_step = self.elastic_replica_increment_step is not None
        has_discrete_values = self.elastic_replica_discrete_values is not None
        
        # Check mutual exclusivity
        if has_increment_step and has_discrete_values:
            raise ValueError(
                "Only one of 'elastic_replica_increment_step' or 'elastic_replica_discrete_values' "
                "can be specified, not both. Please use either:\n"
                "  - elastic_replica_increment_step for uniform scaling steps, or\n"
                "  - elastic_replica_discrete_values for specific replica counts"
            )
        
        # Validate discrete values are within valid range
        if has_discrete_values:
            discrete_values = self.elastic_replica_discrete_values

            # Check that all values are positive
            if any(val <= 0 for val in discrete_values):
                raise ValueError(
                    f"All values in 'elastic_replica_discrete_values' must be positive integers. "
                    f"Got: {discrete_values}"
                )

            # Check against max_node_count if specified
            if self.max_node_count is not None:
                invalid_values = [val for val in discrete_values if val > self.max_node_count]
                if invalid_values:
                    raise ValueError(
                        f"All values in 'elastic_replica_discrete_values' must be ≤ max_node_count ({self.max_node_count}). "
                        f"Invalid values: {invalid_values}. "
                        f"Please either increase max_node_count or remove values exceeding it."
                    )

        return self

    def to_domain(self) -> Dict:
        """Convert flat config to domain model (HyperPodPytorchJobSpec)"""
        
        # Helper function to build dict with non-None values
        def build_dict(**kwargs):
            return {k: v for k, v in kwargs.items() if v is not None}
        
        # Build resources
        if self.instance_type is None:
            requests_value = limits_value = {"nvidia.com/gpu": "0"}
        else:
            if self.accelerator_partition_type:
                partition_resource_key = f"nvidia.com/{self.accelerator_partition_type}"
                requests_value = build_dict(
                    **{partition_resource_key: str(self.accelerator_partition_count)} if self.accelerator_partition_count else {},
                    vcpu=str(self.vcpu) if self.vcpu else None,
                    memory=str(self.memory) if self.memory else None
                )
                limits_value = build_dict(
                    **{partition_resource_key: str(self.accelerator_partition_limit)} if self.accelerator_partition_limit else {},
                    vcpu=str(self.vcpu_limit) if self.vcpu_limit else None,
                    memory=str(self.memory_limit) if self.memory_limit else None
                )
            else:
                requests_value = build_dict(
                    accelerators=str(self.accelerators) if self.accelerators else None,
                    vcpu=str(self.vcpu) if self.vcpu else None,
                    memory=str(self.memory) if self.memory else None
                )
                limits_value = build_dict(
                    accelerators=str(self.accelerators_limit) if self.accelerators_limit else None,
                    vcpu=str(self.vcpu_limit) if self.vcpu_limit else None,
                    memory=str(self.memory_limit) if self.memory_limit else None
                )

        # Build container
        container_kwargs = build_dict(
            name="pytorch-job-container",
            image=self.image,
            resources=Resources(requests=requests_value, limits=limits_value),
            command=self.command,
            args=self.args,
            image_pull_policy=self.pull_policy,
            env=[{"name": k, "value": v} for k, v in self.environment.items()] if self.environment else None,
            volume_mounts=[{"name": vol.name, "mount_path": vol.mount_path} for vol in self.volume] if self.volume else None
        )
        
        container = Containers(**container_kwargs)

        # Build volumes
        volumes = None
        if self.volume:
            volumes = []
            for vol in self.volume:
                if vol.type == "hostPath":
                    volume_obj = Volumes(name=vol.name, host_path=HostPath(path=vol.path))
                elif vol.type == "pvc":
                    volume_obj = Volumes(name=vol.name, persistent_volume_claim=PersistentVolumeClaim(
                        claim_name=vol.claim_name,
                        read_only=vol.read_only == "true" if vol.read_only else False
                    ))
                volumes.append(volume_obj)

        # Build node selector
        node_selector = build_dict(
            **{"node.kubernetes.io/instance-type": self.instance_type} if self.instance_type else {},
            **self.label_selector if self.label_selector else {},
            **{"deep-health-check-passed": "true"} if self.deep_health_check_passed_nodes_only else {},
            **{"nvidia.com/mig.config.state": "success"} if self.accelerator_partition_type else {}
        )

        # Build spec
        spec_kwargs = build_dict(
            containers=[container],
            volumes=volumes,
            node_selector=node_selector if node_selector else None,
            service_account_name=self.service_account_name,
            scheduler_name=self.scheduler_type
        )

        # Build metadata
        metadata_labels = build_dict(
            **{"kueue.x-k8s.io/queue-name": self.queue_name} if self.queue_name else {},
            **{"kueue.x-k8s.io/priority-class": self.priority} if self.priority else {}
        )
        
        annotations = build_dict(
            **{"kueue.x-k8s.io/podset-preferred-topology": self.preferred_topology} if self.preferred_topology else {},
            **{"kueue.x-k8s.io/podset-required-topology": self.required_topology} if self.required_topology else {}
        )

        metadata_kwargs = build_dict(
            name=self.job_name,
            namespace=self.namespace,
            labels=metadata_labels if metadata_labels else None,
            annotations=annotations if annotations else None
        )

        # Build replica spec
        replica_kwargs = build_dict(
            name="pod",
            template=Template(metadata=Metadata(**metadata_kwargs), spec=Spec(**spec_kwargs)),
            replicas=self.node_count,
            max_replicas=self.max_node_count
        )

        # Build elastic policy
        elastic_policy = None
        if any([
            self.elastic_replica_increment_step is not None,
            self.max_node_count is not None,
            self.elastic_graceful_shutdown_timeout_in_seconds is not None,
            self.elastic_scaling_timeout_in_seconds is not None,
            self.elastic_replica_discrete_values is not None
        ]):
            # Build base elastic policy kwargs
            elastic_policy_kwargs = build_dict(
                min_replicas=self.node_count,
                max_replicas=self.max_node_count,
                graceful_shutdown_timeout_in_seconds=self.elastic_graceful_shutdown_timeout_in_seconds,
                scaling_timeout_in_seconds=self.elastic_scaling_timeout_in_seconds
            )

            if self.elastic_replica_discrete_values is not None:
                elastic_policy_kwargs['replica_discrete_values'] = self.elastic_replica_discrete_values
            elif self.elastic_replica_increment_step is not None:
                elastic_policy_kwargs['replica_increment_step'] = self.elastic_replica_increment_step

            elastic_policy = ElasticPolicy(**elastic_policy_kwargs)

        # Build run policy
        run_policy = None
        if self.max_retry is not None or self.elastic_scale_up_snooze_time_in_seconds is not None:
            from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_unified_config import RestartPolicy

            run_policy_kwargs = build_dict(
                clean_pod_policy="None",
                job_max_retry_count=self.max_retry
            )

            # Add restart policy if scale_up_snooze_interval is provided
            if self.elastic_scale_up_snooze_time_in_seconds is not None:
                restart_policy = RestartPolicy(
                    eval_period_seconds=3600,
                    scale_up_snooze_time_in_seconds=self.elastic_scale_up_snooze_time_in_seconds
                )
                run_policy_kwargs['restart_policy'] = restart_policy

            run_policy = RunPolicy(**run_policy_kwargs)

        # Build job
        job_kwargs = build_dict(
            metadata=metadata_kwargs,
            replica_specs=[ReplicaSpec(**replica_kwargs)],
            nproc_per_node=str(self.tasks_per_node) if self.tasks_per_node else None,
            run_policy=run_policy,
            elastic_policy=elastic_policy
        )

        result = HyperPodPytorchJob(**job_kwargs)
        return result


# Volume-specific type handlers - only override what's needed
def volume_parse_strings(ctx_or_strings, param=None, value=None):
    """Parse volume strings into VolumeConfig objects. Can be used as Click callback."""
    # Handle dual usage pattern (inlined)
    if param is not None and value is not None:
        volume_strings, is_click_callback = value, True
    else:
        volume_strings, is_click_callback = ctx_or_strings, False

    if not volume_strings:
        return None
    if not isinstance(volume_strings, (list, tuple)):
        volume_strings = [volume_strings]

    # Core parsing logic
    volumes = []
    for vol_str in volume_strings:
        vol_dict = {}
        for pair in vol_str.split(','):
            if '=' in pair:
                key, val = pair.split('=', 1)
                key = key.strip()
                val = val.strip()
                vol_dict[key] = val.lower() == 'true' if key == 'read_only' else val

        try:
            volumes.append(VolumeConfig(**vol_dict))
        except Exception as e:
            error_msg = f"Invalid volume configuration '{vol_str}': {e}"
            if is_click_callback:
                raise click.BadParameter(error_msg)
            else:
                raise ValueError(error_msg)

    return volumes


def volume_from_dicts(volume_dicts):
    """Convert list of volume dictionaries to VolumeConfig objects."""
    if volume_dicts is None:
        return None
    return [VolumeConfig(**vol_dict) for vol_dict in volume_dicts if isinstance(vol_dict, dict)]


def volume_write_to_yaml(key, volumes, file_handle):
    """Write VolumeConfig objects to YAML format."""
    if volumes:
        file_handle.write(f"{key}:\n")
        for vol in volumes:
            file_handle.write(f"  - name: {vol.name}\n")
            file_handle.write(f"    type: {vol.type}\n")
            file_handle.write(f"    mount_path: {vol.mount_path}\n")
            if vol.path:
                file_handle.write(f"    path: {vol.path}\n")
            if vol.claim_name:
                file_handle.write(f"    claim_name: {vol.claim_name}\n")
            if vol.read_only is not None:
                file_handle.write(f"    read_only: {vol.read_only}\n")
            file_handle.write("\n")
    else:
        file_handle.write(f"{key}: []\n\n")


def volume_merge_dicts(existing_volumes, new_volumes):
    """Merge volume configurations, updating existing volumes by name or adding new ones."""
    merged = {vol.get('name'): vol for vol in existing_volumes}
    merged.update({vol.get('name'): vol for vol in new_volumes})
    return list(merged.values())


# Handler definition - merge with defaults, only override specific functions
def _get_volume_type_handler():
    from sagemaker.hyperpod.cli.type_handler_utils import DEFAULT_TYPE_HANDLER
    return {
        **DEFAULT_TYPE_HANDLER,  # Start with all defaults
        'parse_strings': volume_parse_strings,  # Override only these
        'from_dicts': volume_from_dicts,
        'write_to_yaml': volume_write_to_yaml,
        'merge_dicts': volume_merge_dicts,
        'needs_multiple_option': True
    }

VOLUME_TYPE_HANDLER = _get_volume_type_handler()
