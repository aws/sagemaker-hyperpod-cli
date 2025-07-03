import unittest
from unittest.mock import patch, MagicMock, mock_open
import subprocess
from sagemaker.hyperpod.hyperpod_manager import HyperPodManager


class TestHyperPodManager(unittest.TestCase):
    def setUp(self):
        self.manager = HyperPodManager()

    def test_get_eks_name_from_arn_valid(self):
        arn = "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"
        result = self.manager._get_eks_name_from_arn(arn)
        self.assertEqual(result, "my-cluster")

    def test_get_eks_name_from_arn_invalid(self):
        with self.assertRaises(RuntimeError):
            self.manager._get_eks_name_from_arn("invalid:arn:format")

    def test_is_eks_orchestrator_true(self):
        mock_client = MagicMock()
        mock_client.describe_cluster.return_value = {"Orchestrator": {"Eks": {}}}
        
        result = HyperPodManager._is_eks_orchestrator(mock_client, "my-cluster")
        
        self.assertTrue(result)
        mock_client.describe_cluster.assert_called_once_with(ClusterName="my-cluster")

    def test_is_eks_orchestrator_false(self):
        mock_client = MagicMock()
        mock_client.describe_cluster.return_value = {"Orchestrator": {"Slurm": {}}}
        
        result = HyperPodManager._is_eks_orchestrator(mock_client, "my-cluster")
        
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_update_kube_config_success(self, mock_run):
        self.manager._update_kube_config("my-cluster")
        
        mock_run.assert_called_once_with(
            ["aws", "eks", "update-kubeconfig", "--name", "my-cluster"], check=True
        )

    @patch("subprocess.run")
    def test_update_kube_config_with_region_and_config(self, mock_run):
        self.manager._update_kube_config("my-cluster", "us-west-2", "/path/to/config")
        
        mock_run.assert_called_once_with(
            ["aws", "eks", "update-kubeconfig", "--name", "my-cluster", 
             "--region", "us-west-2", "--kubeconfig", "/path/to/config"],
            check=True
        )

    @patch("subprocess.run")
    def test_update_kube_config_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "aws eks update-kubeconfig")
        
        with self.assertRaises(RuntimeError):
            self.manager._update_kube_config("my-cluster")

    @patch("yaml.safe_dump")
    @patch("yaml.safe_load")
    @patch("builtins.open", new_callable=mock_open)
    @patch("kubernetes.config.load_kube_config")
    def test_set_current_context(self, mock_load_config, mock_file, mock_safe_load, mock_safe_dump):
        mock_kubeconfig = {
            "contexts": [{"name": "test-context", "context": {}}],
            "current-context": "old-context"
        }
        mock_safe_load.return_value = mock_kubeconfig
        
        self.manager._set_current_context("test-context", "test-namespace")
        
        mock_safe_load.assert_called_once()
        mock_safe_dump.assert_called_once()
        mock_load_config.assert_called_once()

    @patch("boto3.client")
    def test_list_clusters(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        mock_client.list_clusters.return_value = {
            "ClusterSummaries": [
                {"ClusterName": "eks-cluster"},
            ]
        }
        
        with patch.object(HyperPodManager, '_is_eks_orchestrator') as mock_is_eks:
            mock_is_eks.return_value = True
            
            result = HyperPodManager.list_clusters()

            self.assertEqual(result["Eks"], ["eks-cluster"])

    @patch("boto3.client")
    @patch.object(HyperPodManager, "_get_eks_name_from_arn")
    @patch.object(HyperPodManager, "_update_kube_config")
    @patch.object(HyperPodManager, "_set_current_context")
    def test_set_context(self, mock_set_context, mock_update_config, mock_get_name, mock_boto3_client):
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        mock_client.describe_cluster.return_value = {
            "Orchestrator": {"Eks": {"ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"}}
        }
        mock_get_name.return_value = "my-cluster"
        
        HyperPodManager.set_context("my-cluster", "us-west-2", "test-namespace")
        
        mock_client.describe_cluster.assert_called_once_with(ClusterName="my-cluster")
        mock_get_name.assert_called_once()
        mock_update_config.assert_called_once()
        mock_set_context.assert_called_once()
    
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
