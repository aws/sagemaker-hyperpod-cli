import unittest
import subprocess
import logging
from unittest.mock import patch, MagicMock, mock_open, call
from sagemaker.hyperpod.common.utils import (
    handle_exception,
    get_eks_name_from_arn,
    get_region_from_eks_arn,
    is_eks_orchestrator,
    update_kube_config,
    set_eks_context,
    list_clusters,
    set_cluster_context,
    get_cluster_context,
    parse_kubernetes_version,
    is_kubernetes_version_compatible,
)
from kubernetes.client.exceptions import ApiException
from pydantic import ValidationError


class TestHandleException(unittest.TestCase):
    """Test the handle_exception function"""

    def test_handle_api_exception_401(self):
        """Test handling 401 API exception"""
        exception = ApiException(status=401)
        with self.assertRaises(Exception) as context:
            handle_exception(exception, "test-job", "default")
        self.assertIn("Credentials unauthorized", str(context.exception))

    def test_handle_api_exception_403(self):
        """Test handling 403 API exception"""
        exception = ApiException(status=403)
        with self.assertRaises(Exception) as context:
            handle_exception(exception, "test-job", "default")
        self.assertIn(
            "Access denied to resource 'test-job' in namespace 'default'",
            str(context.exception),
        )

    def test_handle_api_exception_404(self):
        """Test handling 404 API exception"""
        exception = ApiException(status=404)
        with self.assertRaises(Exception) as context:
            handle_exception(exception, "test-job", "default")
        self.assertIn(
            "Resource 'test-job' not found in namespace 'default'",
            str(context.exception),
        )

    def test_handle_api_exception_409(self):
        """Test handling 409 API exception"""
        exception = ApiException(status=409)
        with self.assertRaises(Exception) as context:
            handle_exception(exception, "test-job", "default")
        self.assertIn(
            "Resource 'test-job' already exists in namespace 'default'",
            str(context.exception),
        )

    def test_handle_api_exception_500(self):
        """Test handling 500 API exception"""
        exception = ApiException(status=500)
        with self.assertRaises(Exception) as context:
            handle_exception(exception, "test-job", "default")
        self.assertIn("Kubernetes API internal server error", str(context.exception))

    def test_handle_api_exception_unhandled(self):
        """Test handling unhandled API exception"""
        exception = ApiException(status=418, reason="I'm a teapot")
        with self.assertRaises(Exception) as context:
            handle_exception(exception, "test-job", "default")
        self.assertIn(
            "Unhandled Kubernetes error: 418 I'm a teapot", str(context.exception)
        )

    def test_handle_validation_error(self):
        """Test handling validation error"""
        exception = ValidationError.from_exception_data("test", [])
        with self.assertRaises(Exception) as context:
            handle_exception(exception, "test-job", "default")
        self.assertIn("Response did not match expected schema", str(context.exception))

    def test_handle_generic_exception(self):
        """Test handling generic exception"""
        exception = ValueError("test error")
        with self.assertRaises(ValueError):
            handle_exception(exception, "test-job", "default")


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""

    def test_get_eks_name_from_arn_valid(self):
        """Test get_eks_name_from_arn with valid ARN"""
        arn = "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"
        result = get_eks_name_from_arn(arn)
        self.assertEqual(result, "my-cluster")

    def test_get_eks_name_from_arn_invalid(self):
        """Test get_eks_name_from_arn with invalid ARN"""
        with self.assertRaises(RuntimeError) as context:
            get_eks_name_from_arn("invalid:arn:format")
        self.assertIn("cannot get EKS cluster name", str(context.exception))

    def test_get_region_from_eks_arn_valid(self):
        """Test get_region_from_eks_arn with valid ARN"""
        arn = "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"
        result = get_region_from_eks_arn(arn)
        self.assertEqual(result, "us-west-2")

    def test_get_region_from_eks_arn_invalid(self):
        """Test get_region_from_eks_arn with invalid ARN"""
        with self.assertRaises(RuntimeError) as context:
            get_region_from_eks_arn("invalid:arn:format")
        self.assertIn("cannot get region from EKS ARN", str(context.exception))
        
    def test_parse_kubernetes_version_standard_format(self):
        """Test parsing standard Kubernetes version format (1.x.y)"""
        # Test standard format
        self.assertEqual(parse_kubernetes_version("1.24.0"), (1, 24))
        self.assertEqual(parse_kubernetes_version("v1.26.3"), (1, 26))
        
    def test_parse_kubernetes_version_old_client_format(self):
        """Test parsing old client version format (v12 and before)"""
        # Test old client format (v12 and before)
        # v12.0.0 corresponds to Kubernetes v1.16
        self.assertEqual(parse_kubernetes_version("12.0.0"), (1, 16))
        self.assertEqual(parse_kubernetes_version("11.0.0"), (1, 15))
        self.assertEqual(parse_kubernetes_version("10.0.0"), (1, 14))
        
    def test_parse_kubernetes_version_new_client_format(self):
        """Test parsing new homogenized client version format (v17+)"""
        # Test new homogenized format (v17+)
        # v17.0.0 corresponds to Kubernetes v1.17
        self.assertEqual(parse_kubernetes_version("17.0.0"), (1, 17))
        self.assertEqual(parse_kubernetes_version("18.0.0"), (1, 18))
        self.assertEqual(parse_kubernetes_version("24.0.0"), (1, 24))
        
    def test_parse_kubernetes_version_with_suffix(self):
        """Test parsing version with suffix"""
        # Test with suffix
        self.assertEqual(parse_kubernetes_version("24.0.0+snapshot"), (1, 24))
        self.assertEqual(parse_kubernetes_version("1.26.0+custom"), (1, 26))
        
    def test_parse_kubernetes_version_invalid_format(self):
        """Test parsing invalid version format"""
        # Test invalid format
        self.assertEqual(parse_kubernetes_version(""), (0, 0))
        self.assertEqual(parse_kubernetes_version("invalid"), (0, 0))
        self.assertEqual(parse_kubernetes_version("a.b.c"), (0, 0))
        
    def test_is_kubernetes_version_compatible_same_version(self):
        """Test compatibility check with same versions"""
        # Same versions should be compatible
        self.assertTrue(is_kubernetes_version_compatible((1, 24), (1, 24)))
        
    def test_is_kubernetes_version_compatible_within_range(self):
        """Test compatibility check with versions within supported range"""
        # Client within 3 minor versions behind server
        self.assertTrue(is_kubernetes_version_compatible((1, 23), (1, 24)))
        self.assertTrue(is_kubernetes_version_compatible((1, 22), (1, 24)))
        self.assertTrue(is_kubernetes_version_compatible((1, 21), (1, 24)))
        
        # Client within 1 minor version ahead of server
        self.assertTrue(is_kubernetes_version_compatible((1, 25), (1, 24)))
        
    def test_is_kubernetes_version_compatible_outside_range(self):
        """Test compatibility check with versions outside supported range"""
        # Client too old (more than 3 minor versions behind)
        self.assertFalse(is_kubernetes_version_compatible((1, 20), (1, 24)))
        
        # Client too new (more than 1 minor version ahead)
        self.assertFalse(is_kubernetes_version_compatible((1, 26), (1, 24)))
        
    def test_is_kubernetes_version_compatible_different_major(self):
        """Test compatibility check with different major versions"""
        # Different major versions should be incompatible
        self.assertFalse(is_kubernetes_version_compatible((2, 0), (1, 0)))
        
    def test_is_kubernetes_version_compatible_default_versions(self):
        """Test compatibility check with default versions (0, 0)"""
        # Default versions should be treated as compatible
        self.assertTrue(is_kubernetes_version_compatible((0, 0), (1, 24)))
        self.assertTrue(is_kubernetes_version_compatible((1, 24), (0, 0)))
        self.assertTrue(is_kubernetes_version_compatible((0, 0), (0, 0)))

    def test_is_eks_orchestrator_true(self):
        mock_client = MagicMock()
        mock_client.describe_cluster.return_value = {"Orchestrator": {"Eks": {}}}
        
        result = is_eks_orchestrator(mock_client, "my-cluster")
        
        self.assertTrue(result)
        mock_client.describe_cluster.assert_called_once_with(ClusterName="my-cluster")

    def test_is_eks_orchestrator_false(self):
        mock_client = MagicMock()
        mock_client.describe_cluster.return_value = {"Orchestrator": {"Slurm": {}}}
        
        result = is_eks_orchestrator(mock_client, "my-cluster")
        
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_update_kube_config_success(self, mock_run):
        update_kube_config("my-cluster")
        
        mock_run.assert_called_once_with(
            ["aws", "eks", "update-kubeconfig", "--name", "my-cluster"], check=True
        )

    @patch("subprocess.run")
    def test_update_kube_config_with_region_and_config(self, mock_run):
        update_kube_config("my-cluster", "us-west-2", "/path/to/config")
        
        mock_run.assert_called_once_with(
            ["aws", "eks", "update-kubeconfig", "--name", "my-cluster", 
             "--region", "us-west-2", "--kubeconfig", "/path/to/config"],
            check=True
        )

    @patch("subprocess.run")
    def test_update_kube_config_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "aws eks update-kubeconfig")
        
        with self.assertRaises(RuntimeError):
            update_kube_config("my-cluster")

    @patch("yaml.safe_dump")
    @patch("yaml.safe_load")
    @patch("builtins.open", new_callable=mock_open)
    @patch("kubernetes.config.load_kube_config")
    def test_set_eks_context(self, mock_load_config, mock_file, mock_safe_load, mock_safe_dump):
        mock_kubeconfig = {
            "contexts": [{"name": "test-context", "context": {}}],
            "current-context": "old-context"
        }
        mock_safe_load.return_value = mock_kubeconfig
        
        set_eks_context("test-context", "test-namespace")
        
        mock_safe_load.assert_called_once()
        mock_safe_dump.assert_called_once()
        mock_load_config.assert_called_once()

    @patch("boto3.client")
    @patch("sagemaker.hyperpod.common.utils.is_eks_orchestrator")
    def test_list_clusters(self, mock_is_eks, mock_boto3_client):
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        mock_client.list_clusters.return_value = {
            "ClusterSummaries": [
                {"ClusterName": "eks-cluster"},
            ]
        }
        mock_is_eks.return_value = True
        
        result = list_clusters()

        self.assertEqual(result["Eks"], ["eks-cluster"])

    @patch("boto3.client")
    @patch("sagemaker.hyperpod.common.utils.get_eks_name_from_arn")
    @patch("sagemaker.hyperpod.common.utils.update_kube_config")
    @patch("sagemaker.hyperpod.common.utils.set_eks_context")
    def test_set_cluster_context(self, mock_set_context_func, mock_update_config, mock_get_name, mock_boto3_client):
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        mock_client.describe_cluster.return_value = {
            "Orchestrator": {"Eks": {"ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"}}
        }
        mock_get_name.return_value = "my-cluster"
        
        set_cluster_context("my-cluster", "us-west-2", "test-namespace")
        
        mock_client.describe_cluster.assert_called_once_with(ClusterName="my-cluster")
        mock_get_name.assert_called_once()
        mock_update_config.assert_called_once()
        mock_set_context_func.assert_called_once()
    
    @patch("kubernetes.config.list_kube_config_contexts")
    def test_get_cluster_context_success(self, mock_list_contexts):
        mock_list_contexts.return_value = [
            None,
            {
                "context": {
                    "cluster": "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"
                }
            },
        ]
        result = get_cluster_context()
        
        self.assertEqual(result, "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster")
        mock_list_contexts.assert_called_once()