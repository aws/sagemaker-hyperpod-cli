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
import re
from sagemaker.hyperpod.cli.constants.command_constants import NVIDIA_GPU_RESOURCE_LIMIT_KEY, NEURON_RESOURCE_LIMIT_KEY
from sagemaker.hyperpod.cli.utils import (
    setup_logger
)
from typing import Optional, Tuple
from sagemaker.hyperpod.training.accelerator_partition_util import _validate_accelerator_partition, _get_accelerator_partition_defaults
from sagemaker.hyperpod.training.constants import INSTANCE_RESOURCES
logger = setup_logger(__name__)

def _has_compute_resource_quota_allocation_resources(memory_in_gib: Optional[float], vcpu: Optional[float], accelerators: Optional[int]) -> bool:
    return (
        (memory_in_gib is not None and memory_in_gib > 0) or
        (vcpu is not None and vcpu > 0) or
        (accelerators is not None and accelerators > 0)
    )

# Gets resources from compute quotas that user provided; if not all provided, calculates defaults.
def _get_resources_from_compute_quotas(instance_type: str, 
                                       vcpu: Optional[float], 
                                       memory_in_gib: Optional[float], 
                                       accelerators: Optional[int] = 0,
                                       accelerator_partition_type: Optional[str] = None,
                                       accelerator_partition_count: Optional[int] = None) -> Optional[dict]:
    has_accelerator_partition = accelerator_partition_type is not None and accelerator_partition_count is not None
    has_compute_resources = _has_compute_resource_quota_allocation_resources(memory_in_gib, vcpu, accelerators)

    if not has_compute_resources and not has_accelerator_partition:
        return None

    result = {}
    if has_accelerator_partition:
        return _process_accelerator_partition_allocation(
            instance_type, vcpu, memory_in_gib, accelerator_partition_type, accelerator_partition_count
        )
    
    type_of_accelerator, _max_accelerator_per_instance = _get_accelerator_type_and_count(instance_type)

    instance = INSTANCE_RESOURCES.get(instance_type, {})

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
    _trim_resource_requests(instance_type, result)
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


def _trim_resource_requests(instance_type: str, requests_values: dict) -> dict:
    instance = INSTANCE_RESOURCES.get(instance_type, {})
    cpu_capacity = instance.get("cpu", 0)
    max_allocatable_cpu = cpu_capacity - (_calculate_cpu_reservation(cpu_capacity))
    memory_capacity = instance.get("memory", 0)
    max_allocatable_memory = memory_capacity - (_calculate_memory_reservation(memory_capacity))

    cpu_request_str = requests_values.get('cpu', '0')
    cpu_request = float(''.join(filter(lambda x: x.isdigit() or x == '.', cpu_request_str)))

    mem_request_str = requests_values.get('memory', '0Gi')
    mem_request = float(mem_request_str.replace('Gi', ''))

    final_cpu = min(max_allocatable_cpu, cpu_request)
    final_memory = min(max_allocatable_memory, mem_request)

    requests_values['cpu'] = str(final_cpu)
    requests_values['memory'] = f"{final_memory}Gi"

    return requests_values


def _get_limits(instance_type: str, vcpu_limit: Optional[float], memory_in_gib_limit: Optional[float], accelerators_limit: Optional[int], accelerator_partition_type: Optional[str], accelerator_partition_limit: Optional[int]) -> dict:

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
    if accelerator_partition_limit is not None:
        result[f"nvidia.com/{accelerator_partition_type}"] = accelerator_partition_limit
    if memory_in_gib_limit is not None:
        result["memory"] = str(memory_in_gib_limit) + "Gi"

    return result


def _resolve_default_cpu_values(instance_type: str, requests_values: dict) -> None:
    instance = INSTANCE_RESOURCES.get(instance_type, {})
    total_available_cpu = instance.get('cpu')

    cpu_request = float(requests_values.get('cpu')) if requests_values.get('cpu') is not None else None

    if cpu_request is not None and cpu_request > total_available_cpu:
        raise ValueError(
            f"Specified CPU request ({cpu_request}) exceeds instance capacity. "
            f"Maximum available CPU for {instance_type} is {total_available_cpu}."
        )

    max_allocatable_cpu = int(total_available_cpu - _calculate_cpu_reservation(total_available_cpu))
    cpu_request = min(cpu_request, max_allocatable_cpu)
    requests_values["cpu"] = str(cpu_request)


def _resolve_default_memory_values(instance_type: str, requests_values: dict, limits_values: dict) -> None:

    instance = INSTANCE_RESOURCES.get(instance_type, {})
    total_available_memory = instance.get("memory", 0)
    mem_limit_str = limits_values.get("memory")
    mem_request_str = requests_values.get("memory")

    user_set_limit = True if mem_limit_str is not None else False
    if mem_limit_str is None and mem_request_str is not None:
        mem_limit_str = mem_request_str

    try:
        memory_limit = float(re.match(r'^([0-9]*\.?[0-9]+)', mem_limit_str).group(1))
        memory_request = float(re.match(r'^([0-9]*\.?[0-9]+)', mem_request_str).group(1))
    except (AttributeError, ValueError):
        raise ValueError(f"Invalid memory format: {mem_limit_str or mem_request_str}")

    if memory_request > total_available_memory:
        raise ValueError(
            f"Specified memory request ({memory_request}Gi) exceeds instance capacity. "
            f"Maximum available memory for {instance_type} is {total_available_memory}Gi."
        )

    max_allocatable_memory = int(total_available_memory - _calculate_memory_reservation(total_available_memory))

    if not user_set_limit:
        memory_limit = min(memory_limit, max_allocatable_memory)

    memory_request = min(memory_request, max_allocatable_memory)
    limits_values["memory"] = str(memory_limit) + "Gi"
    requests_values["memory"] = str(memory_request) + "Gi"


def _validate_accelerators_inputs(instance_type: str, accelerators_request: int, accelerators_limit: int) -> None:
    type_of_accelerator, _max_accelerator_per_instance = _get_accelerator_type_and_count(instance_type)
    if type_of_accelerator is None and (accelerators_request is not None or accelerators_limit is not None):
        raise ValueError(
            f"Instance type {instance_type} does not support accelerators, but accelerator values were provided.")

    if type_of_accelerator is not None:
        if accelerators_request is not None and accelerators_limit is not None:
            if accelerators_request !=  accelerators_limit:
                raise ValueError('Accelerator request must equal accelerator limit')
            if accelerators_limit > _max_accelerator_per_instance:
                raise ValueError('Requested accelerators exceeds capacity')
            if accelerators_request > _max_accelerator_per_instance:
                raise ValueError('Requested accelerators exceeds capacity')


def _set_default_accelerators_val(instance_type: Optional[str], accelerators_request: Optional[int], accelerators_limit: Optional[int]) -> Tuple[Optional[int], Optional[int]]:
    type_of_accelerator, _max_accelerator_per_instance = _get_accelerator_type_and_count(instance_type)
    if type_of_accelerator is not None:
        if accelerators_request is None and accelerators_limit is None:
            return None, None
        elif accelerators_request is not None and accelerators_limit is None:
            return accelerators_request, accelerators_request
        elif accelerators_request is None and accelerators_limit is not None:
            return accelerators_limit, accelerators_limit
        else:
            return accelerators_request, accelerators_limit
    return None, None


def _is_valid(vcpu: Optional[float], memory_in_gib: Optional[float], accelerators: Optional[int], accelerators_limit: Optional[int],
              node_count: Optional[int], instance_type: Optional[str],
              accelerator_partition_type: Optional[str] = None,
              accelerator_partition_count: Optional[int] = None,
              accelerator_partition_limit: Optional[int] = None) -> Tuple[bool, str]:

    if accelerator_partition_type or accelerator_partition_count or accelerator_partition_limit:
        partition_valid, partition_error = _validate_accelerator_partition(
            accelerator_partition_type, accelerators, accelerators_limit, node_count, instance_type)
        if not partition_valid:
            return False, partition_error
            
    has_gpu_quota_allocation = _has_compute_resource_quota_allocation_resources(memory_in_gib, vcpu, accelerators)

    if (instance_type is None and has_gpu_quota_allocation) or (instance_type is None and accelerator_partition_type):
        return False, "Instance-type must be specified when accelerators, accelerator_partition_type, vcpu, or memory-in-gib specified"

    node_specified = node_count is not None and node_count > 0

    # Check if instance_type is valid only when it's provided
    if instance_type is not None and (INSTANCE_RESOURCES.get(instance_type) is None):
        return False, f"Invalid instance-type {instance_type}. Please re-check the instance type and contact AWS for support."
    if instance_type is not None:
        #both resources and node count specified
        if (has_gpu_quota_allocation and node_specified):
            return False, f"Either node-count OR a combination of accelerators, vcpu, memory-in-gib must be specified for instance-type {instance_type}"
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


def _calculate_memory_reservation(memory_gb: int) -> float:

    static_memory_overhead = 0.5  # 500MB

    reserved_memory = static_memory_overhead
    remaining = memory_gb

    # First 4 GB (30%)
    first_4gb = min(4, remaining)
    reserved_memory += first_4gb * 0.3
    remaining -= first_4gb

    # Next 4 GB (25%)
    if remaining > 0:
        next_4gb = min(4, remaining)
        reserved_memory += next_4gb * 0.25
        remaining -= next_4gb

    # Next 8 GB (20%)
    if remaining > 0:
        next_8gb = min(8, remaining)
        reserved_memory += next_8gb * 0.2
        remaining -= next_8gb

    # Next 112 GB (17%)
    if remaining > 0:
        next_112gb = min(112, remaining)
        reserved_memory += next_112gb * 0.17
        remaining -= next_112gb

    # Remaining memory (7%)
    if remaining > 0:
        reserved_memory += remaining * 0.07

    return reserved_memory


def _calculate_cpu_reservation(cpu_count: int) -> float:

    # Static overhead for observability tools and system processes
    static_cpu_overhead = 0.1  # 0.1 cores

    reserved_cpu = static_cpu_overhead

    # First core (30%)
    if cpu_count >= 1:
        reserved_cpu += 0.3

    # Second core (15%)
    if cpu_count >= 2:
        reserved_cpu += 0.15

    # Cores 3-4 (10% each)
    for _ in range(min(2, max(0, cpu_count - 2))):
        reserved_cpu += 0.1

    # Remaining cores (6% each)
    if cpu_count > 4:
        reserved_cpu += (cpu_count - 4) * 0.06

    return reserved_cpu

def _process_accelerator_partition_allocation(instance_type: str,
                                            vcpu: Optional[float],
                                            memory_in_gib: Optional[float],
                                            accelerator_partition_type: str,
                                            accelerator_partition_count: int) -> dict:
    instance = INSTANCE_RESOURCES.get(instance_type, {})
    instance_vcpu = instance.get("cpu", 0)
    instance_memory = instance.get("memory", 0)

    # Case 1: both vCpu and memoryInGiB are provided
    if vcpu is not None and memory_in_gib is not None:
        result = {"cpu": str(vcpu), "memory": f"{memory_in_gib}Gi"}
    # Case 2: vCpu is provided but not memoryInGiB
    elif vcpu is not None and memory_in_gib is None:
        memory_in_gib = float(int((vcpu / instance_vcpu) * instance_memory))
        result = {"cpu": str(vcpu), "memory": f"{memory_in_gib}Gi"}
    # Case 3: memory is provided but not vcpu
    elif vcpu is None and memory_in_gib is not None:
        vcpu = float(int((memory_in_gib / instance_memory) * instance_vcpu))
        result = {"cpu": str(vcpu), "memory": f"{memory_in_gib}Gi"}
    # Case 4: neither vcpu or memory is provided
    else:
        result = _get_accelerator_partition_defaults(instance_type, accelerator_partition_type, accelerator_partition_count)

    accelerator_partition_resource_key = f"nvidia.com/{accelerator_partition_type}"
    result[accelerator_partition_resource_key] = str(accelerator_partition_count)

    _trim_resource_requests(instance_type, result)
    return result
