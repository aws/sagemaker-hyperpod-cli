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

import pytest
from sagemaker.hyperpod.training.quota_allocation_util import (
    _get_resources_from_instance,
    _get_limits,
    _is_valid,
    _get_accelerator_type_and_count,
    _get_resources_from_compute_quotas,
    _has_compute_resource_quota_allocation_resources,
    INSTANCE_RESOURCES
)

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
        assert result == {"cpu": "4.0", "memory": "16.0Gi", "nvidia.com/gpu": 1}

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
        assert result == {"cpu": "2.0", "memory": "16.0Gi", "nvidia.com/gpu": 1}

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
        assert message == "Either node-count or a combination of accelerators, vcpu, memory-in-gib must be specified for instance-type ml.g5.xlarge"

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
