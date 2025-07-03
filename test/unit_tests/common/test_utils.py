import unittest
from sagemaker.hyperpod.common.utils import handle_exception
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
            "Access denied to resource 'test-job' in 'default'", str(context.exception)
        )

    def test_handle_api_exception_404(self):
        """Test handling 404 API exception"""
        exception = ApiException(status=404)
        with self.assertRaises(Exception) as context:
            handle_exception(exception, "test-job", "default")
        self.assertIn(
            "Resource 'test-job' not found in namespace 'default'", str(context.exception)
        )

    def test_handle_api_exception_409(self):
        """Test handling 409 API exception"""
        exception = ApiException(status=409)
        with self.assertRaises(Exception) as context:
            handle_exception(exception, "test-job", "default")
        self.assertIn(
            "Resource 'test-job' already exists in 'default'", str(context.exception)
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
