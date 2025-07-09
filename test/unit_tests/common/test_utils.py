import unittest
import logging
import io
from sagemaker.hyperpod.common.utils import (
    handle_exception,
    get_eks_name_from_arn,
    get_region_from_eks_arn,
    validate_cluster_connection,
    get_default_namespace,
    setup_logging,
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

    def test_setup_logging_debug_mode(self):
        """Test logger configuration in debug mode"""
        logger = logging.getLogger('test_logger')
        try:
            configured_logger = setup_logging(logger, debug=True)

            # Verify debug configuration
            self.assertEqual(configured_logger.level, logging.DEBUG)
            self.assertEqual(len(configured_logger.handlers), 1)

            # Verify debug formatter
            handler = configured_logger.handlers[0]
            formatter = handler.formatter
            self.assertIn("asctime", formatter._fmt)
            self.assertIn("levelname", formatter._fmt)
            self.assertFalse(configured_logger.propagate)
        finally:
            # Cleanup
            logger.handlers.clear()

    def test_setup_logging_info_mode(self):
        """Test logger configuration in info mode"""
        logger = logging.getLogger('test_logger')
        # Add an initial handler to test removal
        logger.addHandler(logging.StreamHandler())

        try:
            configured_logger = setup_logging(logger, debug=False)

            # Verify info configuration
            self.assertEqual(configured_logger.level, logging.INFO)
            self.assertEqual(len(configured_logger.handlers), 1)

            # Verify simple formatter
            handler = configured_logger.handlers[0]
            self.assertEqual(handler.formatter._fmt, "%(message)s")
            self.assertFalse(configured_logger.propagate)
        finally:
            # Cleanup
            logger.handlers.clear()

    def test_setup_logging_output(self):
        """Test actual logging output"""
        # Create StringIO object to capture output
        stream = io.StringIO()
        logger = logging.getLogger('test_logger')

        try:
            # Create handler with our StringIO object
            handler = logging.StreamHandler(stream)
            configured_logger = setup_logging(logger, debug=True)

            # Replace the handler with our capturing handler
            configured_logger.handlers = [handler]

            test_message = "Test debug message"
            configured_logger.debug(test_message)

            # Get the output
            output = stream.getvalue()

            # Verify output format
            self.assertIn(test_message, output)
        finally:
            # Cleanup
            logger.handlers.clear()
            stream.close()
