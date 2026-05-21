"""Unit tests for space utils module."""

import os
import warnings
import unittest
from unittest.mock import Mock, patch
from kubernetes import client
from sagemaker.hyperpod.space.utils import (
    camel_to_snake,
    get_model_fields,
    map_kubernetes_response_to_model,
    get_pod_instance_type,
    validate_space_mig_resources,
    validate_mig_profile_in_cluster,
    _parse_version,
    get_spaces_addon_version,
    warn_if_addon_version_incompatible,
    SPACES_ADDON_NAME,
)
from hyperpod_space_template.v1_0.model import SpaceConfig


class TestSpaceUtils(unittest.TestCase):
    """Test cases for space utils functions."""

    def test_camel_to_snake(self):
        """Test camelCase to snake_case conversion."""
        self.assertEqual(camel_to_snake("displayName"), "display_name")
        self.assertEqual(camel_to_snake("desiredStatus"), "desired_status")
        self.assertEqual(camel_to_snake("ownershipType"), "ownership_type")
        self.assertEqual(camel_to_snake("image"), "image")
        self.assertEqual(camel_to_snake("name"), "name")

    def test_get_model_fields(self):
        """Test model fields extraction."""
        fields = get_model_fields(SpaceConfig)
        expected_fields = {
            'name', 'display_name', 'namespace', 'image', 'desired_status',
            'ownership_type', 'resources', 'storage', 'volumes', 'container_config',
            'node_selector', 'affinity', 'tolerations', 'lifecycle', 'template_ref'
        }
        self.assertTrue(expected_fields.issubset(fields))

    def test_map_kubernetes_response_to_model(self):
        """Test Kubernetes response mapping to model format."""
        k8s_data = {
            'metadata': {'name': 'test-space', 'namespace': 'default'},
            'spec': {
                'image': 'test:latest',
                'displayName': 'Test Space',
                'desiredStatus': 'Running',
                'unknownField': 'should be ignored'
            },
            'status': {
                'currentStatus': 'Running',
                'anotherUnknownField': 'also ignored'
            }
        }
        
        mapped = map_kubernetes_response_to_model(k8s_data, SpaceConfig)
        
        # Check that expected fields are mapped correctly
        self.assertEqual(mapped['name'], 'test-space')
        self.assertEqual(mapped['namespace'], 'default')
        self.assertEqual(mapped['image'], 'test:latest')
        self.assertEqual(mapped['display_name'], 'Test Space')
        self.assertEqual(mapped['desired_status'], 'Running')
        
        # Check that unknown fields are filtered out
        self.assertNotIn('unknownField', mapped)
        self.assertNotIn('anotherUnknownField', mapped)
        self.assertNotIn('currentStatus', mapped)

    def test_map_kubernetes_response_creates_valid_config(self):
        """Test that mapped data creates valid SpaceConfig."""
        k8s_data = {
            'metadata': {'name': 'valid-space', 'namespace': 'test'},
            'spec': {
                'image': 'valid:latest',
                'displayName': 'Valid Space',
                'desiredStatus': 'Running'
            }
        }
        
        mapped = map_kubernetes_response_to_model(k8s_data, SpaceConfig)
        config = SpaceConfig(**mapped)
        
        self.assertEqual(config.name, 'valid-space')
        self.assertEqual(config.display_name, 'Valid Space')
        self.assertEqual(config.namespace, 'test')
        self.assertEqual(config.image, 'valid:latest')

    @patch('sagemaker.hyperpod.space.utils.client.CoreV1Api')
    def test_get_pod_instance_type_success(self, mock_core_v1):
        """Test successful retrieval of pod instance type."""
        # Mock pod with node assignment
        mock_pod = Mock()
        mock_pod.spec.node_name = 'test-node'
        
        # Mock node with instance type label
        mock_node = Mock()
        mock_node.metadata.labels = {'node.kubernetes.io/instance-type': 'ml.p4d.24xlarge'}
        
        # Setup API mock
        mock_api = Mock()
        mock_api.read_namespaced_pod.return_value = mock_pod
        mock_api.read_node.return_value = mock_node
        mock_core_v1.return_value = mock_api
        
        result = get_pod_instance_type('test-pod', 'default')
        
        self.assertEqual(result, 'ml.p4d.24xlarge')
        mock_api.read_namespaced_pod.assert_called_once_with(name='test-pod', namespace='default')
        mock_api.read_node.assert_called_once_with(name='test-node')

    @patch('sagemaker.hyperpod.space.utils.client.CoreV1Api')
    def test_get_pod_instance_type_pod_not_scheduled(self, mock_core_v1):
        """Test error when pod is not scheduled on any node."""
        mock_pod = Mock()
        mock_pod.spec.node_name = None
        
        mock_api = Mock()
        mock_api.read_namespaced_pod.return_value = mock_pod
        mock_core_v1.return_value = mock_api
        
        with self.assertRaises(RuntimeError) as context:
            get_pod_instance_type('unscheduled-pod')
        
        self.assertIn("Pod 'unscheduled-pod' is not scheduled", str(context.exception))

    @patch('sagemaker.hyperpod.space.utils.client.CoreV1Api')
    def test_get_pod_instance_type_no_instance_type_label(self, mock_core_v1):
        """Test error when node has no instance type label."""
        mock_pod = Mock()
        mock_pod.spec.node_name = 'test-node'
        
        mock_node = Mock()
        mock_node.metadata.labels = {'other.label': 'value'}
        
        mock_api = Mock()
        mock_api.read_namespaced_pod.return_value = mock_pod
        mock_api.read_node.return_value = mock_node
        mock_core_v1.return_value = mock_api
        
        with self.assertRaises(RuntimeError) as context:
            get_pod_instance_type('test-pod')
        
        self.assertIn("Instance type not found for node 'test-node'", str(context.exception))

    def test_validate_space_mig_resources_none(self):
        """Test validation with None resources."""
        valid, err = validate_space_mig_resources(None)
        self.assertTrue(valid)
        self.assertEqual(err, "")

    def test_validate_space_mig_resources_empty(self):
        """Test validation with empty resources."""
        valid, err = validate_space_mig_resources({})
        self.assertTrue(valid)
        self.assertEqual(err, "")

    def test_validate_space_mig_resources_single_mig_profile(self):
        """Test validation with single MIG profile."""
        resources = {"nvidia.com/mig-1g.5gb": "2", "cpu": "4"}
        valid, err = validate_space_mig_resources(resources)
        self.assertTrue(valid)
        self.assertEqual(err, "")

    def test_validate_space_mig_resources_multiple_mig_profiles(self):
        """Test validation fails with multiple MIG profiles."""
        resources = {
            "nvidia.com/mig-1g.5gb": "2",
            "nvidia.com/mig-2g.10gb": "1",
            "cpu": "4"
        }
        valid, err = validate_space_mig_resources(resources)
        self.assertFalse(valid)
        self.assertEqual(err, "Space only supports one MIG profile")

    def test_validate_space_mig_resources_mixed_gpu_and_mig(self):
        """Test validation fails when mixing full GPU with MIG."""
        resources = {
            "nvidia.com/gpu": "1",
            "nvidia.com/mig-1g.5gb": "2",
            "cpu": "4"
        }
        valid, err = validate_space_mig_resources(resources)
        self.assertFalse(valid)
        self.assertEqual(err, "Cannot mix full GPU (nvidia.com/gpu) with MIG partitions (nvidia.com/mig-*)")

    def test_validate_space_mig_resources_full_gpu_only(self):
        """Test validation passes with full GPU only."""
        resources = {"nvidia.com/gpu": "1", "cpu": "4", "memory": "8Gi"}
        valid, err = validate_space_mig_resources(resources)
        self.assertTrue(valid)
        self.assertEqual(err, "")

    @patch.dict(os.environ, {"VALIDATE_PROFILE_IN_CLUSTER": "false"})
    def test_validate_mig_profile_in_cluster_disabled(self):
        """Test validation skipped when env var is false."""
        valid, err = validate_mig_profile_in_cluster("nvidia.com/mig-1g.5gb")
        self.assertTrue(valid)
        self.assertEqual(err, "")

    @patch('sagemaker.hyperpod.space.utils.client.CoreV1Api')
    def test_validate_mig_profile_in_cluster_found(self, mock_core_v1):
        """Test validation succeeds when MIG profile exists on a node."""
        # Mock node with MIG profile
        mock_node1 = Mock()
        mock_node1.status.allocatable = {"nvidia.com/mig-1g.5gb": "7"}
        
        mock_node2 = Mock()
        mock_node2.status.allocatable = {"nvidia.com/gpu": "8"}
        
        mock_nodes = Mock()
        mock_nodes.items = [mock_node1, mock_node2]
        
        mock_api = Mock()
        mock_api.list_node.return_value = mock_nodes
        mock_core_v1.return_value = mock_api
        
        valid, err = validate_mig_profile_in_cluster("nvidia.com/mig-1g.5gb")
        
        self.assertTrue(valid)
        self.assertEqual(err, "")

    @patch('sagemaker.hyperpod.space.utils.client.CoreV1Api')
    def test_validate_mig_profile_in_cluster_not_found(self, mock_core_v1):
        """Test validation fails when MIG profile doesn't exist on any node."""
        # Mock nodes without the requested MIG profile
        mock_node1 = Mock()
        mock_node1.status.allocatable = {"nvidia.com/mig-2g.10gb": "4"}
        
        mock_node2 = Mock()
        mock_node2.status.allocatable = {"nvidia.com/gpu": "8"}
        
        mock_nodes = Mock()
        mock_nodes.items = [mock_node1, mock_node2]
        
        mock_api = Mock()
        mock_api.list_node.return_value = mock_nodes
        mock_core_v1.return_value = mock_api
        
        valid, err = validate_mig_profile_in_cluster("nvidia.com/mig-1g.5gb")
        
        self.assertFalse(valid)
        self.assertIn("Accelerator partition type 'nvidia.com/mig-1g.5gb' does not exist", err)
        self.assertIn("Use 'hyp list-accelerator-partition-type'", err)

    @patch('sagemaker.hyperpod.space.utils.client.CoreV1Api')
    def test_validate_mig_profile_in_cluster_zero_allocatable(self, mock_core_v1):
        """Test validation fails when MIG profile exists but has zero allocatable."""
        mock_node = Mock()
        mock_node.status.allocatable = {"nvidia.com/mig-1g.5gb": "0"}
        
        mock_nodes = Mock()
        mock_nodes.items = [mock_node]
        
        mock_api = Mock()
        mock_api.list_node.return_value = mock_nodes
        mock_core_v1.return_value = mock_api
        
        valid, err = validate_mig_profile_in_cluster("nvidia.com/mig-1g.5gb")
        
        self.assertFalse(valid)
        self.assertIn("does not exist in this cluster", err)

    @patch('sagemaker.hyperpod.space.utils.client.CoreV1Api')
    def test_validate_mig_profile_in_cluster_no_status(self, mock_core_v1):
        """Test validation handles nodes without status."""
        mock_node1 = Mock()
        mock_node1.status = None
        
        mock_node2 = Mock()
        mock_node2.status.allocatable = {"nvidia.com/mig-1g.5gb": "7"}
        
        mock_nodes = Mock()
        mock_nodes.items = [mock_node1, mock_node2]
        
        mock_api = Mock()
        mock_api.list_node.return_value = mock_nodes
        mock_core_v1.return_value = mock_api
        
        valid, err = validate_mig_profile_in_cluster("nvidia.com/mig-1g.5gb")
        
        self.assertTrue(valid)
        self.assertEqual(err, "")

    def test_parse_version_standard(self):
        self.assertEqual(_parse_version("0.1.6"), (0, 1, 6))

    def test_parse_version_major(self):
        self.assertEqual(_parse_version("1.0.0"), (1, 0, 0))

    def test_parse_version_comparison_less_than(self):
        self.assertTrue(_parse_version("0.1.1") < _parse_version("0.1.6"))

    def test_parse_version_comparison_equal(self):
        self.assertEqual(_parse_version("0.1.6"), _parse_version("0.1.6"))

    def test_parse_version_comparison_greater_than(self):
        self.assertTrue(_parse_version("0.2.0") > _parse_version("0.1.6"))

    @patch("sagemaker.hyperpod.cli.utils.get_hyperpod_cluster_region", return_value="us-west-2")
    @patch("sagemaker.hyperpod.common.utils.create_boto3_client")
    def test_get_addon_version_parses_eksbuild_suffix(self, mock_client_factory, mock_region):
        mock_client = Mock()
        mock_client.describe_addon.return_value = {
            "addon": {"addonVersion": "v0.1.6-eksbuild.1"}
        }
        mock_client_factory.return_value = mock_client

        result = get_spaces_addon_version("my-cluster")
        self.assertEqual(result, "0.1.6")
        mock_client.describe_addon.assert_called_once_with(
            clusterName="my-cluster", addonName=SPACES_ADDON_NAME
        )

    @patch("sagemaker.hyperpod.cli.utils.get_hyperpod_cluster_region", return_value="us-west-2")
    @patch("sagemaker.hyperpod.common.utils.create_boto3_client")
    def test_get_addon_version_without_v_prefix(self, mock_client_factory, mock_region):
        mock_client = Mock()
        mock_client.describe_addon.return_value = {
            "addon": {"addonVersion": "0.1.1-eksbuild.2"}
        }
        mock_client_factory.return_value = mock_client

        result = get_spaces_addon_version("my-cluster")
        self.assertEqual(result, "0.1.1")

    @patch("sagemaker.hyperpod.cli.utils.get_hyperpod_cluster_region", return_value="us-west-2")
    @patch("sagemaker.hyperpod.common.utils.create_boto3_client")
    def test_get_addon_version_returns_none_on_exception(self, mock_client_factory, mock_region):
        mock_client = Mock()
        mock_client.describe_addon.side_effect = Exception("Not found")
        mock_client_factory.return_value = mock_client

        result = get_spaces_addon_version("my-cluster")
        self.assertIsNone(result)

    @patch("sagemaker.hyperpod.cli.utils.get_hyperpod_cluster_region", return_value="us-west-2")
    @patch("sagemaker.hyperpod.common.utils.create_boto3_client")
    def test_get_addon_version_returns_none_on_unparseable(self, mock_client_factory, mock_region):
        mock_client = Mock()
        mock_client.describe_addon.return_value = {
            "addon": {"addonVersion": "invalid-version"}
        }
        mock_client_factory.return_value = mock_client

        result = get_spaces_addon_version("my-cluster")
        self.assertIsNone(result)

    def _make_decorated_class(self):
        class FakeSpace:
            def __init__(self):
                self.called = False

            @warn_if_addon_version_incompatible
            def create(self):
                self.called = True
                return "created"

        return FakeSpace

    @patch("sagemaker.hyperpod.space.utils.get_spaces_addon_version", return_value="0.1.1")
    @patch("sagemaker.hyperpod.space.utils.get_eks_cluster_name", return_value="my-cluster")
    def test_decorator_warns_when_version_too_old(self, mock_cluster, mock_version):
        space = self._make_decorated_class()()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = space.create()

        self.assertEqual(result, "created")
        self.assertTrue(space.called)
        self.assertEqual(len(w), 1)
        self.assertIn("0.1.1", str(w[0].message))
        self.assertIn("0.1.6", str(w[0].message))

    @patch("sagemaker.hyperpod.space.utils.get_spaces_addon_version", return_value="0.1.6")
    @patch("sagemaker.hyperpod.space.utils.get_eks_cluster_name", return_value="my-cluster")
    def test_decorator_no_warning_when_version_sufficient(self, mock_cluster, mock_version):
        space = self._make_decorated_class()()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = space.create()

        self.assertEqual(result, "created")
        self.assertEqual(len(w), 0)

    @patch("sagemaker.hyperpod.space.utils.get_spaces_addon_version", return_value=None)
    @patch("sagemaker.hyperpod.space.utils.get_eks_cluster_name", return_value="my-cluster")
    def test_decorator_no_warning_when_version_unknown(self, mock_cluster, mock_version):
        space = self._make_decorated_class()()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = space.create()

        self.assertEqual(result, "created")
        self.assertEqual(len(w), 0)

    @patch("sagemaker.hyperpod.space.utils.get_eks_cluster_name", side_effect=Exception("no context"))
    def test_decorator_no_warning_when_cluster_unavailable(self, mock_cluster):
        space = self._make_decorated_class()()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = space.create()

        self.assertEqual(result, "created")
        self.assertTrue(space.called)
        self.assertEqual(len(w), 0)
