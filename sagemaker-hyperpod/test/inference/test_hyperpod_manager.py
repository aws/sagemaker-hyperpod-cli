import unittest
from unittest.mock import patch, MagicMock, mock_open
import pytest
import subprocess
from sagemaker.hyperpod.hyperpod_manager import HyperPodManager


class TestHyperPodManager(unittest.TestCase):
    def setUp(self):
        self.manager = HyperPodManager()

    def test_get_eks_name_from_arn_valid(self):
        # Test with valid ARN
        arn = "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"
        result = self.manager._get_eks_name_from_arn(arn)
        self.assertEqual(result, "my-cluster")

    def test_get_eks_name_from_arn_invalid(self):
        # Test with invalid ARN format
        with pytest.raises(RuntimeError, match="cannot get EKS cluster name"):
            self.manager._get_eks_name_from_arn("invalid:arn:format")

    @patch("boto3.client")
    def test_is_eks_orchestrator_true(self, mock_boto3_client):
        # Setup mock
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        mock_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"
                }
            }
        }

        result = self.manager._is_eks_orchestrator(mock_client, "my-cluster")
        self.assertTrue(result)
        mock_client.describe_cluster.assert_called_once_with(ClusterName="my-cluster")

    @patch("boto3.client")
    def test_is_eks_orchestrator_false(self, mock_boto3_client):
        # Setup mock
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        mock_client.describe_cluster.return_value = {"Orchestrator": {"Slurm": {}}}

        result = self.manager._is_eks_orchestrator(mock_client, "my-cluster")
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_update_kube_config_success(self, mock_run):
        # Test with minimal parameters
        self.manager._update_kube_config("my-cluster")
        mock_run.assert_called_once_with(
            ["aws", "eks", "update-kubeconfig", "--name", "my-cluster"], check=True
        )

        mock_run.reset_mock()

        # Test with all parameters
        self.manager._update_kube_config("my-cluster", "us-west-2", "/path/to/config")
        mock_run.assert_called_once_with(
            [
                "aws",
                "eks",
                "update-kubeconfig",
                "--name",
                "my-cluster",
                "--region",
                "us-west-2",
                "--kubeconfig",
                "/path/to/config",
            ],
            check=True,
        )

    @patch("subprocess.run")
    def test_update_kube_config_failure(self, mock_run):
        # Setup mock to raise exception
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "aws eks update-kubeconfig"
        )

        # Test
        with pytest.raises(RuntimeError, match="Failed to update kubeconfig"):
            self.manager._update_kube_config("my-cluster")

    @patch("sagemaker.hyperpod.hyperpod_manager.KUBE_CONFIG_PATH", "/mock/path")
    @patch("yaml.safe_load")
    @patch("yaml.safe_dump")
    @patch("builtins.open", new_callable=mock_open)
    @patch("kubernetes.config.load_kube_config")
    def test_set_current_context_with_namespace(
        self, mock_load_config, mock_file, mock_safe_dump, mock_safe_load
    ):
        # Setup mock
        mock_kubeconfig = {
            "contexts": [
                {"name": "context1", "context": {}},
                {
                    "name": "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster",
                    "context": {},
                },
            ]
        }
        mock_safe_load.return_value = mock_kubeconfig

        # Test
        self.manager._set_current_context(
            "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster", "default"
        )

        # Verify
        mock_file.assert_any_call("/mock/path", "r")
        mock_file.assert_any_call("/mock/path", "w")

        # Check that namespace was set
        expected_kubeconfig = {
            "contexts": [
                {"name": "context1", "context": {}},
                {
                    "name": "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster",
                    "context": {"namespace": "default"},
                },
            ],
            "current-context": "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster",
        }
        mock_safe_dump.assert_called_once_with(expected_kubeconfig, mock_file())
        mock_load_config.assert_called_once_with(config_file="/mock/path")

    @patch("boto3.client")
    def test_list_clusters(self, mock_boto3_client):
        # Setup mock
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        mock_client.list_clusters.return_value = {
            "ClusterSummaries": [
                {"ClusterName": "eks-cluster"},
                {"ClusterName": "slurm-cluster"},
            ]
        }

        # Mock _is_eks_orchestrator to return True for eks-cluster and False for slurm-cluster
        self.manager._is_eks_orchestrator = MagicMock()
        self.manager._is_eks_orchestrator.side_effect = (
            lambda client, name: name == "eks-cluster"
        )

        self.manager.list_clusters()

        # Verify
        mock_boto3_client.assert_called_once_with("sagemaker", region_name=None)
        mock_client.list_clusters.assert_called_once()
        self.manager._is_eks_orchestrator.assert_any_call(mock_client, "eks-cluster")
        self.manager._is_eks_orchestrator.assert_any_call(mock_client, "slurm-cluster")

    @patch("boto3.client")
    @patch.object(HyperPodManager, "_get_eks_name_from_arn")
    @patch.object(HyperPodManager, "_update_kube_config")
    @patch.object(HyperPodManager, "_set_current_context")
    def test_set_context_cluster(
        self, mock_set_context, mock_update_config, mock_get_name, mock_boto3_client
    ):
        # Setup mocks
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        mock_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"
                }
            }
        }
        mock_get_name.return_value = "my-cluster"
        self.manager.set_context_cluster("my-cluster", "us-west-2", "default")

        # Verify
        mock_boto3_client.assert_called_once_with("sagemaker", region_name="us-west-2")
        mock_client.describe_cluster.assert_called_once_with(ClusterName="my-cluster")
        mock_get_name.assert_called_once_with(
            "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"
        )
        mock_update_config.assert_called_once_with(
            "my-cluster", "us-west-2", "/tmp/kubeconfig"
        )
        mock_set_context.assert_called_once_with(
            "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster", "default"
        )

    @patch("kubernetes.config.list_kube_config_contexts")
    def test_get_context_success(self, mock_list_contexts):
        # Setup mock
        mock_list_contexts.return_value = [
            None,
            {
                "context": {
                    "cluster": "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"
                }
            },
        ]
        self.manager.get_context()

        # Verify
        mock_list_contexts.assert_called_once()
