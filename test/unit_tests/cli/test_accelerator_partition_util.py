from sagemaker.hyperpod.training.accelerator_partition_util import (
    _extract_gpu_slices_from_accelerator_partition_type,
    _get_accelerator_partition,
    _get_accelerator_partition_defaults,
    _set_default_accelerator_partition_val,
    _validate_accelerator_partition,
)
from sagemaker.hyperpod.training.constants import INSTANCE_TYPE_MIG_PROFILES
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


class TestB300MigProfiles:
    """Tests for B300 (Blackwell Ultra) MIG profile constants and defaults."""

    def test_b300_profiles_complete(self):
        profiles = INSTANCE_TYPE_MIG_PROFILES["ml.p6-b300.48xlarge"]
        expected = [
            "mig-1g.34gb",
            "mig-1g.67gb",
            "mig-2g.67gb",
            "mig-3g.135gb",
            "mig-4g.135gb",
            "mig-7g.269gb",
        ]
        assert profiles == expected

    @pytest.mark.parametrize(
        "partition_type,partition_count,expected_cpu,expected_memory",
        [
            ("mig-1g.34gb", 7, "24.0", "512.0Gi"),
            ("mig-1g.67gb", 4, "13.0", "292.0Gi"),
            ("mig-2g.67gb", 3, "20.0", "438.0Gi"),
            ("mig-3g.135gb", 2, "20.0", "438.0Gi"),
            ("mig-4g.135gb", 1, "13.0", "292.0Gi"),
            ("mig-7g.269gb", 1, "24.0", "512.0Gi"),
        ],
    )
    def test_accelerator_partition_defaults_b300(self, partition_type, partition_count, expected_cpu, expected_memory):
        """Verify CPU/memory defaults match the deterministic ratio formula for B300."""
        defaults = _get_accelerator_partition_defaults(
            "ml.p6-b300.48xlarge", partition_type, partition_count
        )
        assert defaults["cpu"] == expected_cpu
        assert defaults["memory"] == expected_memory

    @pytest.mark.parametrize(
        "partition_type,expected_valid,error_check",
        [
            ("mig-1g.34gb", True, lambda e: e == ""),
            ("mig-3g.135gb", True, lambda e: e == ""),
            ("mig-7g.269gb", True, lambda e: e == ""),
            ("mig-1g.5gb", False, lambda e: "not supported on instance type" in e),
        ],
    )
    @patch("sagemaker.hyperpod.training.accelerator_partition_util.KubernetesClient")
    def test_validate_b300_partition(
        self, mock_k8s_client, partition_type, expected_valid, error_check
    ):
        mock_node = MagicMock()
        allocatable = {f"nvidia.com/{partition_type}": "1"} if expected_valid else {}
        mock_node.status.allocatable = allocatable
        mock_k8s_client.return_value.get_core_v1_api.return_value.list_node.return_value.items = [
            mock_node
        ]

        valid, error = _validate_accelerator_partition(
            partition_type, None, None, None, "ml.p6-b300.48xlarge"
        )
        assert valid is expected_valid
        assert error_check(error)
