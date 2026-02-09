import os
import re
from sagemaker.hyperpod.cli.clients.kubernetes_client import KubernetesClient
from sagemaker.hyperpod.training.constants import (
    INSTANCE_RESOURCES,
    INSTANCE_TYPE_MIG_PROFILES,
    VALIDATE_PROFILE_IN_CLUSTER,
    ALLOWED_ACCELERATOR_PARTITION_TYPES
)
from typing import Optional, Tuple



def _validate_accelerator_partition_parameters(accelerator_partition_type: Optional[str],
                                               accelerators: Optional[int],
                                               accelerators_limit: Optional[int],
                                               node_count: Optional[int],
                                               instance_type: Optional[str]) -> Tuple[bool, str]:
    """Basic accelerator partition validation without cluster checks."""
    if not accelerator_partition_type:
        return False, "accelerator_partition_type must be specified to use accelerator partitions."
    for param, name in [(accelerators, "accelerators"), (accelerators_limit, "accelerators_limit"), (node_count, "node_count")]:
        if param is not None and param > 0:
            return False, f"accelerator_partition_type cannot be used together with {name}."

    if instance_type not in INSTANCE_TYPE_MIG_PROFILES:
        return False, f"Instance type '{instance_type}' does not support accelerator partitions."
    if accelerator_partition_type not in ALLOWED_ACCELERATOR_PARTITION_TYPES:
        return False, f"Accelerator partition type '{accelerator_partition_type}' must be one of: {', '.join(sorted(ALLOWED_ACCELERATOR_PARTITION_TYPES))}"
    allowed_profiles = INSTANCE_TYPE_MIG_PROFILES.get(instance_type, [])
    if accelerator_partition_type not in allowed_profiles:
        return False, (f"Accelerator partition '{accelerator_partition_type}' is not supported on instance type '{instance_type}'. "
                       f"Allowed partitions: {', '.join(sorted(allowed_profiles))}")
    return True, ""

def _validate_accelerator_partition(accelerator_partition_type: Optional[str],
                                    accelerators: Optional[int],
                                    accelerators_limit: Optional[int],
                                    node_count: Optional[int],
                                    instance_type: Optional[str]) -> Tuple[bool, str]:
    valid, err = _validate_accelerator_partition_parameters(accelerator_partition_type, accelerators, accelerators_limit, node_count, instance_type)
    if not valid:
        return valid, err

    if os.getenv(VALIDATE_PROFILE_IN_CLUSTER) == "false":
        return True, ""

    # Validate accelerator partition in cluster
    resource_key = f"nvidia.com/{accelerator_partition_type}"
    for node in KubernetesClient().get_core_v1_api().list_node().items:
        if node.status:
            allocatable_accelerator_partitions = node.status.allocatable.get(resource_key)
            if allocatable_accelerator_partitions and int(allocatable_accelerator_partitions) > 0:
                return True, ""
    return False, (f"accelerator partition type '{accelerator_partition_type}' does not exist in this cluster. "
                   f"Use 'hyp list-accelerator-partition-type' to check for available resources.")

def _get_accelerator_partition_defaults(instance_type: str,
                                        accelerator_partition_type: str,
                                        accelerator_partition_count: int) -> dict:
    """Calculate default CPU/memory for accelerator partitions when both CPU and memory are not provided."""
    instance = INSTANCE_RESOURCES.get(instance_type, {})
    instance_vcpu = instance.get("cpu", 0)
    instance_memory = instance.get("memory", 0)

    gpu_slices_per_profile = _extract_gpu_slices_from_accelerator_partition_type(accelerator_partition_type)
    total_gpus_per_instance = instance.get("gpu", 0)
    MAX_GPU_SLICES = 7

    ratio = (accelerator_partition_count * gpu_slices_per_profile) / (total_gpus_per_instance * MAX_GPU_SLICES)

    calculated_vcpu = float(int(ratio * instance_vcpu))
    calculated_memory = float(int(ratio * instance_memory))

    return {
        "cpu": str(calculated_vcpu),
        "memory": f"{calculated_memory}Gi",
    }


def _get_accelerator_partition(requests: dict, limits: dict) -> tuple:
    accelerator_partition_resource_key = None
    accelerator_partition_type = None
    accelerator_partition_count = None
    accelerator_partition_limit = None

    for key in requests.keys():
        if key.startswith('nvidia.com/mig-'):
            accelerator_partition_resource_key = key
            accelerator_partition_type = key.replace('nvidia.com/', '')
            accelerator_partition_count = int(requests.get(key))
            break

    if not accelerator_partition_resource_key:
        for key in limits.keys():
            if key.startswith('nvidia.com/mig-'):
                accelerator_partition_resource_key = key
                accelerator_partition_type = key.replace('nvidia.com/', '')
                break

    if accelerator_partition_resource_key and limits.get(accelerator_partition_resource_key):
        accelerator_partition_limit = int(limits.get(accelerator_partition_resource_key))

    return accelerator_partition_type, accelerator_partition_count, accelerator_partition_limit

def _set_default_accelerator_partition_val(accelerator_partition_count: Optional[int], accelerator_partition_limit: Optional[int]) -> Tuple[Optional[int], Optional[int]]:
    if accelerator_partition_count is None and accelerator_partition_limit is None:
        return None, None
    elif accelerator_partition_count is not None and accelerator_partition_limit is None:
        return accelerator_partition_count, accelerator_partition_count
    elif accelerator_partition_count is None and accelerator_partition_limit is not None:
        return accelerator_partition_limit, accelerator_partition_limit
    else:
        return accelerator_partition_count, accelerator_partition_limit

def _extract_gpu_slices_from_accelerator_partition_type(partition_type: str) -> int:
    """Extract GPU slices from MIG partition type (e.g., 'mig-1g.5gb' -> 1, 'mig-7g.40gb' -> 7)."""
    if not partition_type.startswith('mig-'):
        raise ValueError(f"Invalid MIG partition type: {partition_type}")

    match = re.search(r'mig-(\d+)g\.[\d.]+gb', partition_type)
    if not match:
        raise ValueError(f"Invalid MIG partition format: {partition_type}")

    return int(match.group(1))
