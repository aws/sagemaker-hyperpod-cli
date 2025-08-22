# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from sagemaker.hyperpod.cli.constants.command_constants import NVIDIA_GPU_RESOURCE_LIMIT_KEY, NEURON_RESOURCE_LIMIT_KEY
from sagemaker.hyperpod.cli.utils import (
    setup_logger
)
from typing import Optional, Tuple

logger = setup_logger(__name__)

# TODO: currently there is no API for instances and they are hardcoded; post GA work with partner team on adding support for such API
INSTANCE_RESOURCES = {
    "ml.p4d.24xlarge": {"cpu": 96, "gpu": 8, "trainium": 0, "memory": 1152},
    "ml.p4de.24xlarge": {"cpu": 96, "gpu": 8, "trainium": 0, "memory": 1152},
    "ml.p5.48xlarge": {"cpu": 192, "gpu": 8, "trainium": 0, "memory": 2048},
    "ml.trn1.32xlarge": {"cpu": 128, "gpu": 0, "trainium": 16, "memory": 512},
    "ml.trn1n.32xlarge": {"cpu": 128, "gpu": 0, "trainium": 16, "memory": 512},
    "ml.g5.xlarge": {"cpu": 4, "gpu": 1, "trainium": 0, "memory": 16},
    "ml.g5.2xlarge": {"cpu": 8, "gpu": 1, "trainium": 0, "memory": 32},
    "ml.g5.4xlarge": {"cpu": 16, "gpu": 1, "trainium": 0, "memory": 64},
    "ml.g5.8xlarge": {"cpu": 32, "gpu": 1, "trainium": 0, "memory": 128},
    "ml.g5.12xlarge": {"cpu": 48, "gpu": 4, "trainium": 0, "memory": 192},
    "ml.g5.16xlarge": {"cpu": 64, "gpu": 1, "trainium": 0, "memory": 256},
    "ml.g5.24xlarge": {"cpu": 96, "gpu": 4, "trainium": 0, "memory": 384},
    "ml.g5.48xlarge": {"cpu": 192, "gpu": 8, "trainium": 0, "memory": 768},
    "ml.g6.xlarge": {"cpu": 4, "gpu": 1, "trainium": 0, "memory": 16},
    "ml.g6.2xlarge": {"cpu": 8, "gpu": 1, "trainium": 0, "memory": 32},
    "ml.g6.4xlarge": {"cpu": 16, "gpu": 1, "trainium": 0, "memory": 64},
    "ml.g6.8xlarge": {"cpu": 32, "gpu": 1, "trainium": 0, "memory": 128},
    "ml.g6.16xlarge": {"cpu": 64, "gpu": 1, "trainium": 0, "memory": 256},
    "ml.g6.12xlarge": {"cpu": 48, "gpu": 4, "trainium": 0, "memory": 192},
    "ml.g6.24xlarge": {"cpu": 96, "gpu": 4, "trainium": 0, "memory": 384},
    "ml.g6.48xlarge": {"cpu": 192, "gpu": 8, "trainium": 0, "memory": 768},
    "ml.gr6.4xlarge": {"cpu": 16, "gpu": 1, "trainium": 0, "memory": 128},
    "ml.gr6.8xlarge": {"cpu": 32, "gpu": 1, "trainium": 0, "memory": 256},
    "ml.g6e.xlarge": {"cpu": 4, "gpu": 1, "trainium": 0, "memory": 32},
    "ml.g6e.2xlarge": {"cpu": 8, "gpu": 1, "trainium": 0, "memory": 64},
    "ml.g6e.4xlarge": {"cpu": 16, "gpu": 1, "trainium": 0, "memory": 128},
    "ml.g6e.8xlarge": {"cpu": 32, "gpu": 1, "trainium": 0, "memory": 256},
    "ml.g6e.16xlarge": {"cpu": 64, "gpu": 1, "trainium": 0, "memory": 512},
    "ml.g6e.12xlarge": {"cpu": 48, "gpu": 4, "trainium": 0, "memory": 384},
    "ml.g6e.24xlarge": {"cpu": 96, "gpu": 4, "trainium": 0, "memory": 768},
    "ml.g6e.48xlarge": {"cpu": 192, "gpu": 8, "trainium": 0, "memory": 1536},
    "ml.p5e.48xlarge": {"cpu": 192, "gpu": 8, "trainium": 0, "memory": 2048},
    "ml.p5en.48xlarge": {"cpu": 192, "gpu": 8, "trainium": 0, "memory": 2048},
    "ml.trn2.48xlarge": {"cpu": 192, "gpu": 0, "trainium": 16, "memory": 2048},
    "ml.p6e-gb200.36xlarge": {"cpu": 144, "gpu": 4, "trainium": 0, "memory": 960},
    "ml.p6-b200.48xlarge": {"cpu": 192, "gpu": 8, "trainium": 0, "memory": 2024},
    "ml.c5.large": {"cpu": 2, "gpu": 0, "trainium": 0, "memory": 4},
    "ml.c5.xlarge": {"cpu": 4, "gpu": 0, "trainium": 0, "memory": 8},
    "ml.c5.2xlarge": {"cpu": 8, "gpu": 0, "trainium": 0, "memory": 16},
    "ml.c5.4xlarge": {"cpu": 16, "gpu": 0, "trainium": 0, "memory": 32},
    "ml.c5.9xlarge": {"cpu": 36, "gpu": 0, "trainium": 0, "memory": 72},
    "ml.c5.12xlarge": {"cpu": 48, "gpu": 0, "trainium": 0, "memory": 96},
    "ml.c5.18xlarge": {"cpu": 72, "gpu": 0, "trainium": 0, "memory": 144},
    "ml.c5.24xlarge": {"cpu": 96, "gpu": 0, "trainium": 0, "memory": 192},
    "ml.c5n.large": {"cpu": 2, "gpu": 0, "trainium": 0, "memory": 5},
    "ml.c5n.2xlarge": {"cpu": 8, "gpu": 0, "trainium": 0, "memory": 21},
    "ml.c5n.4xlarge": {"cpu": 16, "gpu": 0, "trainium": 0, "memory": 42},
    "ml.c5n.9xlarge": {"cpu": 36, "gpu": 0, "trainium": 0, "memory": 96},
    "ml.c5n.18xlarge": {"cpu": 72, "gpu": 0, "trainium": 0, "memory": 192},
    "ml.m5.large": {"cpu": 2, "gpu": 0, "trainium": 0, "memory": 8},
    "ml.m5.xlarge": {"cpu": 4, "gpu": 0, "trainium": 0, "memory": 16},
    "ml.m5.2xlarge": {"cpu": 8, "gpu": 0, "trainium": 0, "memory": 32},
    "ml.m5.4xlarge": {"cpu": 16, "gpu": 0, "trainium": 0, "memory": 64},
    "ml.m5.8xlarge": {"cpu": 32, "gpu": 0, "trainium": 0, "memory": 128},
    "ml.m5.12xlarge": {"cpu": 48, "gpu": 0, "trainium": 0, "memory": 192},
    "ml.m5.16xlarge": {"cpu": 64, "gpu": 0, "trainium": 0, "memory": 256},
    "ml.m5.24xlarge": {"cpu": 96, "gpu": 0, "trainium": 0, "memory": 384},
    "ml.t3.medium": {"cpu": 2, "gpu": 0, "trainium": 0, "memory": 4},
    "ml.t3.large": {"cpu": 2, "gpu": 0, "trainium": 0, "memory": 8},
    "ml.t3.xlarge": {"cpu": 4, "gpu": 0, "trainium": 0, "memory": 16},
    "ml.t3.2xlarge": {"cpu": 8, "gpu": 0, "trainium": 0, "memory": 32},
    "ml.c6i.large": {"cpu": 2, "gpu": 0, "trainium": 0, "memory": 4},
    "ml.c6i.xlarge": {"cpu": 4, "gpu": 0, "trainium": 0, "memory": 8},
    "ml.c6i.2xlarge": {"cpu": 8, "gpu": 0, "trainium": 0, "memory": 16},
    "ml.c6i.4xlarge": {"cpu": 16, "gpu": 0, "trainium": 0, "memory": 32},
    "ml.c6i.8xlarge": {"cpu": 32, "gpu": 0, "trainium": 0, "memory": 64},
    "ml.c6i.12xlarge": {"cpu": 48, "gpu": 0, "trainium": 0, "memory": 96},
    "ml.c6i.16xlarge": {"cpu": 64, "gpu": 0, "trainium": 0, "memory": 128},
    "ml.c6i.24xlarge": {"cpu": 96, "gpu": 0, "trainium": 0, "memory": 192},
    "ml.c6i.32xlarge": {"cpu": 128, "gpu": 0, "trainium": 0, "memory": 256},
    "ml.m6i.large": {"cpu": 2, "gpu": 0, "trainium": 0, "memory": 8},
    "ml.m6i.xlarge": {"cpu": 4, "gpu": 0, "trainium": 0, "memory": 16},
    "ml.m6i.2xlarge": {"cpu": 8, "gpu": 0, "trainium": 0, "memory": 32},
    "ml.m6i.4xlarge": {"cpu": 16, "gpu": 0, "trainium": 0, "memory": 64},
    "ml.m6i.8xlarge": {"cpu": 32, "gpu": 0, "trainium": 0, "memory": 128},
    "ml.m6i.12xlarge": {"cpu": 48, "gpu": 0, "trainium": 0, "memory": 192},
    "ml.m6i.16xlarge": {"cpu": 64, "gpu": 0, "trainium": 0, "memory": 256},
    "ml.m6i.24xlarge": {"cpu": 96, "gpu": 0, "trainium": 0, "memory": 384},
    "ml.m6i.32xlarge": {"cpu": 128, "gpu": 0, "trainium": 0, "memory": 512},
    "ml.r6i.large": {"cpu": 2, "gpu": 0, "trainium": 0, "memory": 16},
    "ml.r6i.xlarge": {"cpu": 4, "gpu": 0, "trainium": 0, "memory": 32},
    "ml.r6i.2xlarge": {"cpu": 8, "gpu": 0, "trainium": 0, "memory": 64},
    "ml.r6i.4xlarge": {"cpu": 16, "gpu": 0, "trainium": 0, "memory": 128},
    "ml.r6i.8xlarge": {"cpu": 32, "gpu": 0, "trainium": 0, "memory": 256},
    "ml.r6i.12xlarge": {"cpu": 48, "gpu": 0, "trainium": 0, "memory": 384},
    "ml.r6i.16xlarge": {"cpu": 64, "gpu": 0, "trainium": 0, "memory": 512},
    "ml.r6i.24xlarge": {"cpu": 96, "gpu": 0, "trainium": 0, "memory": 768},
    "ml.r6i.32xlarge": {"cpu": 128, "gpu": 0, "trainium": 0, "memory": 1024},
    "ml.m7i.large": {"cpu": 2, "gpu": 0, "trainium": 0, "memory": 8},
    "ml.m7i.xlarge": {"cpu": 4, "gpu": 0, "trainium": 0, "memory": 16},
    "ml.m7i.2xlarge": {"cpu": 8, "gpu": 0, "trainium": 0, "memory": 32},
    "ml.m7i.4xlarge": {"cpu": 16, "gpu": 0, "trainium": 0, "memory": 64},
    "ml.m7i.8xlarge": {"cpu": 32, "gpu": 0, "trainium": 0, "memory": 128},
    "ml.m7i.12xlarge": {"cpu": 48, "gpu": 0, "trainium": 0, "memory": 192},
    "ml.m7i.16xlarge": {"cpu": 64, "gpu": 0, "trainium": 0, "memory": 256},
    "ml.m7i.24xlarge": {"cpu": 96, "gpu": 0, "trainium": 0, "memory": 384},
    "ml.m7i.48xlarge": {"cpu": 192, "gpu": 0, "trainium": 0, "memory": 768},
    "ml.r7i.large": {"cpu": 2, "gpu": 0, "trainium": 0, "memory": 16},
    "ml.r7i.xlarge": {"cpu": 4, "gpu": 0, "trainium": 0, "memory": 32},
    "ml.r7i.2xlarge": {"cpu": 8, "gpu": 0, "trainium": 0, "memory": 64},
    "ml.r7i.4xlarge": {"cpu": 16, "gpu": 0, "trainium": 0, "memory": 128},
    "ml.r7i.8xlarge": {"cpu": 32, "gpu": 0, "trainium": 0, "memory": 256},
    "ml.r7i.12xlarge": {"cpu": 48, "gpu": 0, "trainium": 0, "memory": 384},
    "ml.r7i.16xlarge": {"cpu": 64, "gpu": 0, "trainium": 0, "memory": 512},
    "ml.r7i.24xlarge": {"cpu": 96, "gpu": 0, "trainium": 0, "memory": 768},
    "ml.r7i.48xlarge": {"cpu": 192, "gpu": 0, "trainium": 0, "memory": 1536},
    "ml.i3en.large": {"cpu": 2, "gpu": 0, "trainium": 0, "memory": 16},
    "ml.i3en.xlarge": {"cpu": 4, "gpu": 0, "trainium": 0, "memory": 32},
    "ml.i3en.2xlarge": {"cpu": 8, "gpu": 0, "trainium": 0, "memory": 64},
    "ml.i3en.3xlarge": {"cpu": 12, "gpu": 0, "trainium": 0, "memory": 96},
    "ml.i3en.6xlarge": {"cpu": 24, "gpu": 0, "trainium": 0, "memory": 192},
    "ml.i3en.12xlarge": {"cpu": 48, "gpu": 0, "trainium": 0, "memory": 384},
    "ml.i3en.24xlarge": {"cpu": 96, "gpu": 0, "trainium": 0, "memory": 768}
}

def _has_compute_resource_quota_allocation_resources(memory_in_gib: Optional[float], vcpu: Optional[float], accelerators: Optional[int]) -> bool:
    return (
        (memory_in_gib is not None) or
        (vcpu is not None ) or
        (accelerators is not None)
    )

# Gets resources from compute quotas that user provided; if not all provided, calculates defaults.
def _get_resources_from_compute_quotas(instance_type: str, 
                                       vcpu: Optional[float], 
                                       memory_in_gib: Optional[float], 
                                       accelerators: Optional[int] = 0) -> Optional[dict]:
    if not _has_compute_resource_quota_allocation_resources(memory_in_gib, vcpu, accelerators):
        return None

    type_of_accelerator, _max_accelerator_per_instance = _get_accelerator_type_and_count(instance_type)

    instance = INSTANCE_RESOURCES.get(instance_type, {})

    result = {}

    # if only memory set, then default cpu to (allocated memory/instance memory) ratio
    if (vcpu is None and accelerators is None):
        instance_memory = instance.get("memory", 0)
        instance_cpu = instance.get("cpu", 0)
        
        cpu_value = 0

        if instance_memory > 0 and memory_in_gib is not None:
            cpu_value = (memory_in_gib / instance_memory) * instance_cpu

        result["cpu"] = cpu_value
        result["memory"] = memory_in_gib

    # if user specified accelerators and the instance type has accelerators
    elif (accelerators is not None and accelerators > 0 and type_of_accelerator is not None and _max_accelerator_per_instance > 0):
        gpu_ratio = accelerators/_max_accelerator_per_instance
        # default cpu and memory to (allocated gpu/instance gpu) ratio
        result["cpu"] = vcpu or (gpu_ratio * instance.get("cpu", 0))
        memory_value = memory_in_gib or (gpu_ratio * instance.get("memory", 0))
        result["memory"] = memory_value
        result[type_of_accelerator] = accelerators
    
    else:
        result["cpu"] = vcpu or 0
        # default memory to (allocated cpu/instance cpu) ratio
        cpu_ratio = vcpu / instance.get("cpu", 0) if vcpu is not None else 0
        memory_value = memory_in_gib or (cpu_ratio * instance.get("memory", 0))
        result["memory"] = memory_value

    result["cpu"] = f"{result['cpu']}"
    result["memory"] = f"{result['memory']}Gi"
    return result


# Gets resources from instance type.
def _get_resources_from_instance(instance_type: str, node_count: int) -> dict:

    instance = INSTANCE_RESOURCES.get(instance_type, {})
    cpu = instance.get("cpu", 0)
    memory = instance.get("memory", 0)

    result = {
        "cpu": cpu * node_count,
        "memory": memory * node_count
    }

    type_of_accelerator, max_accelerator_per_instance = _get_accelerator_type_and_count(instance_type)
    if type_of_accelerator is not None:
        result[type_of_accelerator] = max_accelerator_per_instance * node_count

    result["cpu"] = f"{result['cpu']}"
    result["memory"] = f"{result['memory']}Gi"
    return result

def _get_limits(instance_type: str, vcpu_limit: Optional[float], memory_in_gib_limit: Optional[float], accelerators_limit: Optional[int]) -> dict:
    
    result = {}
    type_of_accelerator, _max_accelerator_per_instance = _get_accelerator_type_and_count(instance_type)

    if vcpu_limit is not None:
        result["cpu"] = vcpu_limit
        result["cpu"] = f"{result['cpu']}"
    if accelerators_limit is not None:
        if type_of_accelerator is not None:
            result[type_of_accelerator] = accelerators_limit
        else: 
            # user specified accelerator limit but the instance type wasn't found, set limit to 0 as a precaution 
            result["nvidia.com/gpu"] = 0
    
    if memory_in_gib_limit is not None:
        result["memory"] = memory_in_gib_limit
        result["memory"] = f"{result['memory']}Gi"

    return result


def _is_valid(vcpu: Optional[float], memory_in_gib: Optional[float], accelerators: Optional[int], 
              node_count: Optional[int], instance_type: Optional[str]) -> tuple[bool, str]:
            
    has_gpu_quota_allocation = _has_compute_resource_quota_allocation_resources(memory_in_gib, vcpu, accelerators)

    if instance_type is None and has_gpu_quota_allocation:
        return False, "Instance-type must be specified when accelerators, vcpu, or memory-in-gib specified"
    
    node_specified = node_count is not None and node_count > 0
    
    # Check if instance_type is valid only when it's provided
    if instance_type is not None and (INSTANCE_RESOURCES.get(instance_type) is None):
        return False, f"Invalid instance-type {instance_type}. Please re-check the instance type and contact AWS for support."

    if instance_type is not None:
        #both resources and node count specified
        if (has_gpu_quota_allocation and node_specified):
            return False, f"Either node-count or a combination of accelerators, vcpu, memory-in-gib must be specified for instance-type {instance_type}"
    return True, ""


def _get_accelerator_type_and_count(instance_type: str) -> Tuple[Optional[str], int]:
    instance = INSTANCE_RESOURCES.get(instance_type, {})

    trainium_count = instance.get("trainium", 0)        
    gpu_count = instance.get("gpu", 0)
    
    # Initialize variables
    accelerator_key = None
    instance_accelerator_count = 0
    
    # Determine the appropriate key based on instance type
    if trainium_count > 0:
        accelerator_key = NEURON_RESOURCE_LIMIT_KEY
        instance_accelerator_count = trainium_count
    elif gpu_count > 0:
        accelerator_key = NVIDIA_GPU_RESOURCE_LIMIT_KEY
        instance_accelerator_count = gpu_count
    
    if instance_accelerator_count is not None:
        return accelerator_key, instance_accelerator_count
    else:
        # valid use-case for cpu-only machines, hence return None
        return None, 0
