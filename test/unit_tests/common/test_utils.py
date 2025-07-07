import unittest
from sagemaker.hyperpod.common.utils import (
    handle_exception,
    append_uuid,
    get_eks_name_from_arn,
    get_region_from_eks_arn,
    validate_cluster_connection,
    get_default_namespace,
)
from kubernetes.client.exceptions import ApiException
from pydantic import ValidationError
from unittest.mock import patch, MagicMock


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

    def test_append_uuid(self):
        """Test append_uuid function"""
        result = append_uuid("test-job")
        self.assertTrue(result.startswith("test-job-"))
        self.assertEqual(len(result.split("-")[-1]), 4)

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
