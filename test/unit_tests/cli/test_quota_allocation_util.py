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

import pytest
from sagemaker.hyperpod.training.quota_allocation_util import (
    _get_resources_from_instance,
    _get_limits,
    _is_valid,
    _get_accelerator_type_and_count,
    _get_resources_from_compute_quotas,
    _has_compute_resource_quota_allocation_resources,
    _resolve_default_memory_values,
    _validate_accelerators_inputs,
    _set_default_accelerators_val,
    _resolve_default_cpu_values,
    _trim_resource_requests,
    _calculate_memory_reservation,
    _calculate_cpu_reservation,
    INSTANCE_RESOURCES
)

def float_equals(a, b, tolerance=0.0001):
    return abs(a - b) <= tolerance


class TestQuotaAllocationUtil:
    """Test suite for QuotaAllocationUtil functions"""

     # Tests for _has_gpu_quota_allocation_resources method
    @pytest.mark.parametrize(
        "memory_in_gib,vcpu,accelerators,expected",
        [
            # All None
            (None, None, None, False),
            # Single values
            (16.0, None, None, True),
            (None, 4.0, None, True),
            (None, None, 2, True),
            # Multiple values
            (16.0, 4.0, None, True),
            (16.0, None, 2, True),
            (None, 4.0, 2, True),
            (16.0, 4.0, 2, True),
            # Zero values
            (0, None, None, True),
            (None, 0, None, True),
            (None, None, 0, True),
        ]
    )
    def test_has_gpu_quota_allocation_resources(self, memory_in_gib, vcpu, accelerators, expected):
        result = _has_compute_resource_quota_allocation_resources(memory_in_gib, vcpu, accelerators)
        assert result == expected

    # Tests for _get_accelerator_type_and_count method
    @pytest.mark.parametrize(
        "instance_type,expected_key,expected_count",
        [
            # GPU instances
            ("ml.p4d.24xlarge", "nvidia.com/gpu", 8),
            ("ml.p5.48xlarge", "nvidia.com/gpu", 8),
            ("ml.g5.xlarge", "nvidia.com/gpu", 1),
            ("ml.g5.12xlarge", "nvidia.com/gpu", 4),
            ("ml.g6.48xlarge", "nvidia.com/gpu", 8),
            # Trainium instances
            ("ml.trn1.32xlarge", "aws.amazon.com/neurondevice", 16),
            ("ml.trn1n.32xlarge", "aws.amazon.com/neurondevice", 16),
            ("ml.trn2.48xlarge", "aws.amazon.com/neurondevice", 16),
            # CPU-only instances
            ("ml.c5.large", None, 0),
            ("ml.m5.xlarge", None, 0),
            ("ml.t3.medium", None, 0),
            # Invalid instance
            ("invalid-instance", None, 0),
            (None, None, 0),
            ("", None, 0),
        ]
    )
    def test_get_accelerator_type_and_count(self, instance_type, expected_key, expected_count):
        key, count = _get_accelerator_type_and_count(instance_type)
        assert key == expected_key
        assert count == expected_count

    def test_get_resources_from_compute_quotas_no_resources(self):
        result = _get_resources_from_compute_quotas("ml.g5.xlarge", None, None, None)
        assert result is None

    def test_get_resources_from_compute_quotas_memory_only(self):
        # When only memory is set, CPU should be calculated based on memory ratio
        result = _get_resources_from_compute_quotas("ml.g5.xlarge", None, 8.0, None)
        # ml.g5.xlarge has 16GB memory and 4 CPUs, so 8GB should give us 2 CPUs
        assert result == {"cpu": "2.0", "memory": "8.0Gi"}

    def test_get_resources_from_compute_quotas_gpu_instance_with_accelerators_ratio_1(self):
        result = _get_resources_from_compute_quotas("ml.g5.xlarge", None, None, 1)
        # ml.g5.xlarge has 1 GPU, 4 CPUs, 16GiB memory
        assert result == {"cpu": "3.25", "memory": "11.7Gi", "nvidia.com/gpu": 1}

    def test_get_resources_from_compute_quotas_gpu_instance_with_accelerators_ratio_half(self):
        result = _get_resources_from_compute_quotas("ml.g6e.48xlarge", None, None, 4)
        # ml.g5.xlarge has 8 GPU, 192 CPUs, 1536GiB memory
        assert result == {"cpu": "96.0", "memory": "768.0Gi", "nvidia.com/gpu": 4}

    def test_get_resources_from_compute_quotas_gpu_instance_all_params(self):
        result = _get_resources_from_compute_quotas("ml.g5.xlarge", 2.0, 8.0, 1)
        assert result == {"cpu": "2.0", "memory": "8.0Gi", "nvidia.com/gpu": 1}

    def test_get_resources_from_compute_quotas_trainium_instance(self):
        result = _get_resources_from_compute_quotas("ml.trn1.32xlarge", None, None, 8)
        # ml.trn1.32xlarge has 16 trainium, 128 CPUs, 512GB memory
        # 8 trainium is half, so we should get half of CPU and memory
        assert result == {"cpu": "64.0", "memory": "256.0Gi", "aws.amazon.com/neurondevice": 8}

    def test_get_resources_from_compute_quotas_cpu_only_instance(self):
        result = _get_resources_from_compute_quotas("ml.c5.large", 1.0, 2.0, 1)
        # CPU-only instance should not include accelerator key even if accelerators specified
        assert result == {"cpu": "1.0", "memory": "2.0Gi"}

    def test_get_resources_from_compute_quotas_vcpu_only(self):
        result = _get_resources_from_compute_quotas("ml.g5.xlarge", 2.0, None, None)
        # ml.g5.xlarge has 4 CPUs and 16GB memory, so 2 CPUs should give us 8GB memory
        assert result == {"cpu": "2.0", "memory": "8.0Gi"}

    def test_get_resources_from_compute_quotas_accelerators_and_cpu_only(self):
        result = _get_resources_from_compute_quotas("ml.g5.xlarge", 2.0, None, 1)
        # ml.g5.xlarge has 1 gpu, 4 CPUs and 16GB memory, and memory calculated as accelerator ratio
        assert result == {'cpu': '2.0', 'memory': '11.7Gi', 'nvidia.com/gpu': 1}

    # Tests for _get_resources_from_instance method
    @pytest.mark.parametrize(
        "instance_type,node_count,expected",
        [
            # GPU instances
            ("ml.p4d.24xlarge", 1, {"cpu": "96", "memory": "1152Gi", "nvidia.com/gpu": 8}),
            ("ml.p4d.24xlarge", 2, {"cpu": "192", "memory": "2304Gi", "nvidia.com/gpu": 16}),
            ("ml.g5.xlarge", 1, {"cpu": "4", "memory": "16Gi", "nvidia.com/gpu": 1}),
            ("ml.g5.xlarge", 3, {"cpu": "12", "memory": "48Gi", "nvidia.com/gpu": 3}),
            # Trainium instances
            ("ml.trn1.32xlarge", 1, {"cpu": "128", "memory": "512Gi", "aws.amazon.com/neurondevice": 16}),
            ("ml.trn1.32xlarge", 2, {"cpu": "256", "memory": "1024Gi", "aws.amazon.com/neurondevice": 32}),
            # CPU-only instances
            ("ml.c5.large", 1, {"cpu": "2", "memory": "4Gi"}),
            ("ml.c5.large", 5, {"cpu": "10", "memory": "20Gi"}),
            ("ml.m5.xlarge", 1, {"cpu": "4", "memory": "16Gi"}),
            ("ml.m5.xlarge", 2, {"cpu": "8", "memory": "32Gi"}),
            # Invalid instance
            ("invalid-instance", 1, {"cpu": "0", "memory": "0Gi"}),
            (None, 1, {"cpu": "0", "memory": "0Gi"}),
            ("", 1, {"cpu": "0", "memory": "0Gi"}),
        ]
    )
    def test_get_resources_from_instance(self, instance_type, node_count, expected):
        result = _get_resources_from_instance(instance_type, node_count)
        assert result == expected

    # Tests for _get_limits method
    def test_get_limits_all_none(self):
        result = _get_limits("ml.g5.xlarge", None, None, None)
        assert result == {}

    def test_get_limits_all_values(self):
        result = _get_limits("ml.g5.xlarge", 8.0, 32.0, 2)
        assert result == {"cpu": "8.0", "memory": "32.0Gi", "nvidia.com/gpu": 2}

    def test_get_limits_partial_values(self):
        result = _get_limits("ml.g5.xlarge", 4.0, None, 1)
        assert result == {"cpu": "4.0", "nvidia.com/gpu": 1}

    def test_get_limits_memory_only(self):
        result = _get_limits("ml.g5.xlarge", None, 16.0, None)
        assert result == {"memory": "16.0Gi"}

    def test_get_limits_zero_values(self):
        result = _get_limits("ml.g5.xlarge", 0, 0, 0)
        assert result == {"cpu": "0", "memory": "0Gi", "nvidia.com/gpu": 0}

    def test_get_limits_trainium_instance(self):
        result = _get_limits("ml.trn1.32xlarge", 8.0, 32.0, 4)
        assert result == {"cpu": "8.0", "memory": "32.0Gi", "aws.amazon.com/neurondevice": 4}

    def test_get_limits_cpu_only_instance(self):
        result = _get_limits("ml.c5.large", 2.0, 8.0, 1)
        # CPU-only instance should set accelerator limit to 0 as precaution
        assert result == {"cpu": "2.0", "memory": "8.0Gi", "nvidia.com/gpu": 0}

    def test_get_limits_invalid_instance_type(self):
        result = _get_limits("invalid-instance", 4.0, 16.0, 2)
        # Invalid instance type should set accelerator limit to 0 as precaution
        assert result == {"cpu": "4.0", "memory": "16.0Gi", "nvidia.com/gpu": 0}

    def test_get_limits_cpu_instance_r7i(self):
        result = _get_limits("ml.r7i.48xlarge", 16.0, 64.0, 2)
        # CPU-only instance (ml.r7i.48xlarge) should set accelerator limit to 0 as precaution
        assert result == {"cpu": "16.0", "memory": "64.0Gi", "nvidia.com/gpu": 0}

    def test_is_valid_no_instance_type_with_resources(self):
        valid, message = _is_valid(4.0, 16.0, None, None, None)
        assert not valid
        assert message == "Instance-type must be specified when accelerators, vcpu, or memory-in-gib specified"

    def test_is_valid_invalid_instance_type(self):
        valid, message = _is_valid(None, None, None, 1, "ml-123")
        assert not valid
        assert message == "Invalid instance-type ml-123. Please re-check the instance type and contact AWS for support."

    def test_is_valid_both_node_count_and_resources(self):
        valid, message = _is_valid(4.0, None, None, 2, "ml.g5.xlarge")
        assert not valid
        assert message == "Either node-count OR a combination of accelerators, vcpu, memory-in-gib must be specified for instance-type ml.g5.xlarge"

    def test_is_valid_both_node_count_and_limits(self):
        valid, message = _is_valid(None, None, None, 2, "ml.g5.xlarge")
        assert valid
        assert message == ""

    def test_is_valid_node_count_only(self):
        valid, message = _is_valid(None, None, None, 2, "ml.g5.xlarge")
        assert valid
        assert message == ""

    def test_is_valid_resources_only(self):
        valid, message = _is_valid(4.0, 16.0, 1, None, "ml.g5.xlarge")
        assert valid
        assert message == ""

    def test_is_valid_single_resource(self):
        valid, message = _is_valid(None, 16.0, None, None, "ml.g5.xlarge")
        assert valid
        assert message == ""

    # Test instance resources dictionary
    def test_instance_resources_structure(self):
        assert isinstance(INSTANCE_RESOURCES, dict)
        assert len(INSTANCE_RESOURCES) > 0
        
        # Check a few known instances
        assert "ml.g5.xlarge" in INSTANCE_RESOURCES
        assert "ml.trn1.32xlarge" in INSTANCE_RESOURCES
        assert "ml.c5.large" in INSTANCE_RESOURCES

    def test_instance_resources_keys(self):
        # Test that all entries have required keys
        for instance_type, resources in INSTANCE_RESOURCES.items():
            assert isinstance(instance_type, str)
            assert isinstance(resources, dict)
            assert "cpu" in resources
            assert "gpu" in resources
            assert "trainium" in resources
            assert "memory" in resources
            assert isinstance(resources["cpu"], int)
            assert isinstance(resources["gpu"], int)
            assert isinstance(resources["trainium"], int)
            assert isinstance(resources["memory"], int)
            # Ensure no instance has both GPU and Trainium
            assert not (resources["gpu"] > 0 and resources["trainium"] > 0)

    # Edge cases
    def test_get_resources_from_compute_quotas_zero_accelerators(self):
        result = _get_resources_from_compute_quotas("ml.g5.xlarge", 2.0, 8.0, 0)
        # Zero accelerators should not include accelerator key
        assert result == {"cpu": "2.0", "memory": "8.0Gi"}

    def test_get_resources_from_compute_quotas_float_values(self):
        result = _get_resources_from_compute_quotas("ml.g5.xlarge", 2.5, 8.5, 1)
        assert result == {"cpu": "2.5", "memory": "8.5Gi", "nvidia.com/gpu": 1}

    def test_get_resources_from_instance_zero_nodes(self):
        result = _get_resources_from_instance("ml.g5.xlarge", 0)
        assert result == {"cpu": "0", "memory": "0Gi", "nvidia.com/gpu": 0}

    # Tests for _validate_memory_limit
    def test_validate_memory_limit_within_bounds(self):
        requests = {"memory": "8Gi"}
        limits = {"memory": "12Gi"}
        _resolve_default_memory_values("ml.g5.xlarge", requests, limits)
        assert requests["memory"] == "8.0Gi"
        assert limits["memory"] == "12.0Gi"

    def test_validate_memory_limit_missing_values(self):
        requests = {}
        limits = {"memory": "8Gi"}
        with pytest.raises(TypeError):
            _resolve_default_memory_values("ml.g5.xlarge", requests, limits)

    def test_validate_memory_limit_invalid_format(self):
        requests = {"memory": "invalid"}
        limits = {"memory": "8Gi"}
        with pytest.raises(ValueError, match="Invalid memory format"):
            _resolve_default_memory_values("ml.g5.xlarge", requests, limits)

    def test_resolve_default_memory_values_set_to_request(self):
        requests = {"memory": "10Gi"}
        limits = {}
        _resolve_default_memory_values("ml.g5.xlarge", requests, limits)
        assert requests["memory"] == "10.0Gi"
        assert limits["memory"] == "10.0Gi"

    def test_resolve_default_memory_values_set_to_allocatable(self):
        requests = {"memory": "16Gi"}
        limits = {}
        _resolve_default_memory_values("ml.g5.xlarge", requests, limits)
        assert requests["memory"] == "11Gi"
        assert limits["memory"] == "11Gi"

    # Tests for _validate_accelerators_inputs
    def test_validate_accelerators_inputs_valid_equal_values(self):
        # Should not raise exception
        _validate_accelerators_inputs("ml.g5.xlarge", 1, 1)

    def test_validate_accelerators_inputs_unequal_values(self):
        with pytest.raises(ValueError, match="Accelerator request must equal accelerator limit"):
            _validate_accelerators_inputs("ml.g5.xlarge", 1, 2)

    def test_validate_accelerators_inputs_exceeds_capacity_request(self):
        with pytest.raises(ValueError, match="Requested accelerators exceeds capacity"):
            _validate_accelerators_inputs("ml.g5.xlarge", 2, 2)

    def test_validate_accelerators_inputs_exceeds_capacity_limit(self):
        with pytest.raises(ValueError, match="Accelerator request must equal accelerator limit"):
            _validate_accelerators_inputs("ml.g5.xlarge", 1, 2)

    def test_validate_accelerators_inputs_cpu_only_instance(self):
        with pytest.raises(ValueError, match="Instance type ml.c5.large does not support accelerators, but accelerator values were provided."):
            _validate_accelerators_inputs("ml.c5.large", 1, 1)

    # Tests for _set_default_accelerators_val
    def test_set_default_accelerators_val_both_none(self):
        request, limit = _set_default_accelerators_val("ml.g5.xlarge", None, None)
        assert request is None
        assert limit is None

    def test_set_default_accelerators_val_request_only(self):
        request, limit = _set_default_accelerators_val("ml.g5.xlarge", 1, None)
        assert request == 1
        assert limit == 1

    def test_set_default_accelerators_val_limit_only(self):
        request, limit = _set_default_accelerators_val("ml.g5.xlarge", None, 1)
        assert request == 1
        assert limit == 1

    def test_set_default_accelerators_val_both_provided(self):
        request, limit = _set_default_accelerators_val("ml.g5.xlarge", 1, 1)
        assert request == 1
        assert limit == 1

    def test_set_default_accelerators_val_cpu_only_instance(self):
        request, limit = _set_default_accelerators_val("ml.c5.large", 1, 1)
        assert request is None
        assert limit is None

    def test_resolve_default_cpu_request_exceeds_capacity(self):
        requests_values = {"cpu": "10.0"}
        limits_values = {}
        with pytest.raises(ValueError, match=re.escape("Specified CPU request (10.0) exceeds instance capacity. Maximum available CPU for ml.g5.2xlarge is 8.")):
            _resolve_default_cpu_values("ml.g5.2xlarge", requests_values)

    # Tests for _resolve_default_cpu_values
    def test_resolve_default_cpu_values_request_only(self):
        requests_values = {"cpu": "2.0"}
        limits_values = {}
        _resolve_default_cpu_values("ml.c5.large", requests_values)
        assert requests_values["cpu"] == "1"
        assert "cpu" not in limits_values

    def test_resolve_default_cpu_values_both_provided(self):
        requests_values = {"cpu": "2.0"}
        limits_values = {"cpu": "4.0"}
        _resolve_default_cpu_values("ml.c5.large", requests_values)
        assert requests_values["cpu"] == "1"
        assert limits_values["cpu"] == "4.0"

    def test_resolve_default_cpu_values_exceeds_instance_capacity(self):
        requests_values = {"cpu": "10.0"}
        limits_values = {}
        with pytest.raises(ValueError, match=re.escape("Specified CPU request (10.0) exceeds instance capacity. Maximum available CPU for ml.c5.large is 2.")):
            _resolve_default_cpu_values("ml.c5.large", requests_values)

    # Tests for trimming request values
    def test_normal_case(self):
        requests = {"cpu": "2", "memory": "8Gi"}
        result = _trim_resource_requests("ml.g5.12xlarge", requests)
        assert result["cpu"] == "2.0"
        assert result["memory"] == "8.0Gi"

    def test_missing_requests(self):
        requests = {}
        result = _trim_resource_requests("ml.g5.12xlarge", requests)
        assert result["cpu"] == "0.0"
        assert result["memory"] == "0.0Gi"

    def test_decimal_values(self):
        requests = {"cpu": "2.5", "memory": "8.5Gi"}
        result = _trim_resource_requests("ml.g5.12xlarge", requests)
        assert result["cpu"] == "2.5"
        assert result["memory"] == "8.5Gi"

    def test_request_modification(self):
        requests = {"cpu": "2", "memory": "8Gi"}
        original_id = id(requests)
        result = _trim_resource_requests("ml.g5.12xlarge", requests)
        assert id(result) == original_id  # Verify it's the same dict object


    # Regressive scaling tests
    def test_memory_reservation_small_instance(self):
        memory_gb = 4
        reserved = _calculate_memory_reservation(memory_gb)
        assert float_equals(reserved, 1.7)

    def test_memory_reservation_medium_instance(self):
        memory_gb = 16
        reserved = _calculate_memory_reservation(memory_gb)
        assert (float_equals(reserved, 4.3))

    def test_memory_reservation_large_instance(self):
        memory_gb = 2048
        reserved = _calculate_memory_reservation(memory_gb)
        assert (float_equals(reserved, 157.74))

    def test_memory_reservation_zero(self):
        memory_gb = 0
        reserved = _calculate_memory_reservation(memory_gb)
        assert (float_equals(reserved, 0.5))

    def test_cpu_reservation_single_core(self):
        """Test CPU reservation for single core"""
        cpu_count = 1
        reserved = _calculate_cpu_reservation(cpu_count)
        assert (float_equals(reserved, 0.4))

    def test_cpu_reservation_dual_core(self):
        cpu_count = 2
        reserved = _calculate_cpu_reservation(cpu_count)
        assert (float_equals(reserved, 0.55))

    def test_cpu_reservation_quad_core(self):
        cpu_count = 4
        reserved = _calculate_cpu_reservation(cpu_count)
        assert (float_equals(reserved, 0.75))

    def test_cpu_reservation_many_cores(self):
        """Test CPU reservation for 96 cores"""
        cpu_count = 96
        reserved = _calculate_cpu_reservation(cpu_count)
        assert (float_equals(reserved, 6.27))

    def test_cpu_reservation_zero(self):
        """Test CPU reservation with 0 cores"""
        cpu_count = 0
        reserved = _calculate_cpu_reservation(cpu_count)
        # Should only return static overhead
        assert (float_equals(reserved, 0.1))