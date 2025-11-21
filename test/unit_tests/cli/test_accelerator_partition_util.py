from sagemaker.hyperpod.training.accelerator_partition_util import (
    _extract_gpu_slices_from_accelerator_partition_type,
    _get_accelerator_partition,
    _set_default_accelerator_partition_val,
    _validate_accelerator_partition,
)
import pytest
from unittest.mock import patch, MagicMock

class TestAcceleratorPartitionUtil:
    @pytest.mark.parametrize(
        "partition_type,expected_result,should_raise,error_match",
        [
            ("mig-1g.5gb", 1, False, None),
            ("mig-7g.40gb", 7, False, None),
            ("invalid-partition", None, True, "Invalid MIG partition type"),
            ("mig-invalid-format", None, True, "Invalid MIG partition format"),
        ]
    )
    def test_extract_gpu_slices_from_accelerator_partition_type(self, partition_type, expected_result, should_raise, error_match):
        if should_raise:
            with pytest.raises(ValueError, match=error_match):
                _extract_gpu_slices_from_accelerator_partition_type(partition_type)
        else:
            result = _extract_gpu_slices_from_accelerator_partition_type(partition_type)
            assert result == expected_result

    @pytest.mark.parametrize(
        "requests,limits,expected_type,expected_count,expected_limit",
        [
            # From requests only
            ({"cpu": "4", "nvidia.com/mig-1g.5gb": "2"}, {"cpu": "8"}, "mig-1g.5gb", 2, None),
            # From limits only
            ({"cpu": "4"}, {"cpu": "8", "nvidia.com/mig-2g.10gb": "1"}, "mig-2g.10gb", None, 1),
            # From both requests and limits
            ({"nvidia.com/mig-1g.5gb": "2"}, {"nvidia.com/mig-1g.5gb": "2"}, "mig-1g.5gb", 2, 2),
        ]
    )
    def test_get_accelerator_partition(self, requests, limits, expected_type, expected_count, expected_limit):
        partition_type, partition_count, partition_limit = _get_accelerator_partition(requests, limits)

        assert partition_type == expected_type
        assert partition_count == expected_count
        assert partition_limit == expected_limit

    @pytest.mark.parametrize(
        "input_count,input_limit,expected_count,expected_limit",
        [
            (None, None, None, None),
            (2, None, 2, 2),
            (None, 3, 3, 3),
            (2, 4, 2, 4),
        ]
    )
    def test_set_default_accelerator_partition_values(self, input_count, input_limit, expected_count, expected_limit):
        """Test _set_default_accelerator_partition_val with various input combinations"""
        count, limit = _set_default_accelerator_partition_val(input_count, input_limit)
        assert count == expected_count
        assert limit == expected_limit

    @pytest.mark.parametrize(
        "partition_type,accelerators,accelerators_limit,node_count,instance_type,expected_valid,error_check",
        [
            # No fields - should return early
            (None, None, None, None, None, False, lambda e: "accelerator_partition_type must be specified to use accelerator partitions" in e),
            # Invalid partition type with valid instance
            ("invalid-mig", None, None, None, "ml.p4d.24xlarge", False, lambda e: "must be one of:" in e),
            # Mutual exclusivity with accelerators
            ("mig-1g.5gb", 2, None, None, "ml.p4d.24xlarge", False, lambda e: "accelerator_partition_type cannot be used together with accelerators." == e),
            # Mutual exclusivity with accelerators_limit
            ("mig-1g.5gb", None, 2, None, "ml.p4d.24xlarge", False, lambda e: "accelerator_partition_type cannot be used together with accelerators_limit." == e),
            # Mutual exclusivity with node_count
            ("mig-1g.5gb", None, None, 2, "ml.p4d.24xlarge", False, lambda e: "accelerator_partition_type cannot be used together with node_count." == e),
            # Invalid instance type combination
            ("mig-1g.5gb", None, None, None, "ml.c5.large", False, lambda e: "does not support accelerator partitions" in e),
        ]
    )
    @patch('sagemaker.hyperpod.training.accelerator_partition_util.KubernetesClient')
    def test_validate_accelerator_partition_fields(self, mock_k8s_client, partition_type, accelerators, accelerators_limit, node_count, instance_type, expected_valid, error_check):
        # Mock cluster to have no MIG resources for most tests
        mock_node = MagicMock()
        mock_node.status.allocatable = {}
        mock_k8s_client.return_value.get_core_v1_api.return_value.list_node.return_value.items = [mock_node]

        valid, error = _validate_accelerator_partition(partition_type, accelerators, accelerators_limit, node_count, instance_type)
        assert valid is expected_valid
        assert error_check(error)
