"""
Unit tests for cli_decorators module.
Tests all CLI exception handling decorators and auto-detection functionality.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from kubernetes.client.exceptions import ApiException

from sagemaker.hyperpod.common.cli_decorators import handle_cli_exceptions
from sagemaker.hyperpod.common.exceptions.error_constants import ResourceType, OperationType


class TestHandleCliExceptions:
    """Test handle_cli_exceptions decorator."""
    
    def test_successful_function_execution(self):
        """Test decorator allows successful function execution."""
        @handle_cli_exceptions(
            resource_type=ResourceType.HYP_JUMPSTART_ENDPOINT,
            operation_type=OperationType.DELETE
        )
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_exception_handling(self, mock_sys, mock_click):
        """Test decorator handles exceptions correctly."""
        @handle_cli_exceptions(
            resource_type=ResourceType.HYP_JUMPSTART_ENDPOINT,
            operation_type=OperationType.DELETE
        )
        def failing_function():
            raise Exception("Test error")
        
        failing_function()
        
        mock_click.echo.assert_called_once_with("Test error")
        mock_sys.exit.assert_called_once_with(1)
    
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_preserves_function_metadata(self, mock_sys, mock_click):
        """Test decorator preserves original function metadata."""
        @handle_cli_exceptions(
            resource_type=ResourceType.HYP_JUMPSTART_ENDPOINT,
            operation_type=OperationType.DELETE
        )
        def documented_function():
            """This is a test function."""
            pass
        
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a test function."


class TestHandleCliExceptions404Handling:
    """Test handle_cli_exceptions decorator 404 handling functionality."""
    
    def test_successful_function_execution(self):
        """Test decorator allows successful function execution."""
        @handle_cli_exceptions(
            resource_type=ResourceType.HYP_JUMPSTART_ENDPOINT,
            operation_type=OperationType.DELETE
        )
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    @patch('sagemaker.hyperpod.common.cli_decorators.handle_404')
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_404_exception_handling(self, mock_sys, mock_click, mock_handle_404):
        """Test decorator handles 404 exceptions with enhanced messaging."""
        # Create 404 ApiException
        api_exception = ApiException(status=404, reason="Not Found")
        
        @handle_cli_exceptions(
            resource_type=ResourceType.HYP_JUMPSTART_ENDPOINT,
            operation_type=OperationType.DELETE
        )
        def js_delete(name, namespace):
            raise api_exception
        
        # Mock handle_404 to raise Exception with enhanced message
        mock_handle_404.side_effect = Exception("❓ JumpStart endpoint 'test' not found...")
        
        js_delete(name="test", namespace="default")
        
        # Should call handle_404 with explicit parameters
        mock_handle_404.assert_called_once_with(
            "test", "default", ResourceType.HYP_JUMPSTART_ENDPOINT, OperationType.DELETE
        )
        # Should call click.echo with the enhanced message (may be called multiple times)
        mock_click.echo.assert_any_call("❓ JumpStart endpoint 'test' not found...")
        # sys.exit may be called multiple times due to exception re-handling
        assert mock_sys.exit.call_count >= 1
        mock_sys.exit.assert_called_with(1)
    
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_non_404_exception_handling(self, mock_sys, mock_click):
        """Test decorator handles non-404 exceptions normally."""
        @handle_cli_exceptions(
            resource_type=ResourceType.HYP_JUMPSTART_ENDPOINT,
            operation_type=OperationType.DELETE
        )
        def failing_function():
            raise Exception("Generic error")
        
        failing_function()
        
        mock_click.echo.assert_called_once_with("Generic error")
        mock_sys.exit.assert_called_once_with(1)
    
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_non_api_exception_handling(self, mock_sys, mock_click):
        """Test decorator handles non-ApiException errors normally."""
        @handle_cli_exceptions(
            resource_type=ResourceType.HYP_JUMPSTART_ENDPOINT,
            operation_type=OperationType.DELETE
        )
        def failing_function():
            raise ValueError("Value error")
        
        failing_function()
        
        mock_click.echo.assert_called_once_with("Value error")
        mock_sys.exit.assert_called_once_with(1)
    
    @patch('sagemaker.hyperpod.common.cli_decorators.handle_404')
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_404_detection_failure_fallback(self, mock_sys, mock_click, mock_handle_404):
        """Test decorator falls back when resource/operation detection fails."""
        api_exception = ApiException(status=404, reason="Not Found")
        
        @handle_cli_exceptions()  # No parameters provided
        def unknown_function(name, namespace):
            raise api_exception
        
        unknown_function(name="test", namespace="default")
        
        # Should not call handle_404 since no parameters provided
        mock_handle_404.assert_not_called()
        mock_click.echo.assert_called_once_with("(404)\nReason: Not Found\n")
        mock_sys.exit.assert_called_once_with(1)
    
    def test_preserves_function_metadata(self):
        """Test decorator preserves original function metadata."""
        @handle_cli_exceptions(
            resource_type=ResourceType.HYP_JUMPSTART_ENDPOINT,
            operation_type=OperationType.DELETE
        )
        def documented_function():
            """This is a smart test function."""
            pass
        
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a smart test function."


class TestIntegrationSmartHandler:
    """Integration tests for smart CLI exception handler."""
    
    @patch('sagemaker.hyperpod.common.cli_decorators.handle_404')
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_complete_jumpstart_delete_flow(self, mock_sys, mock_click, mock_handle_404):
        """Test complete flow for JumpStart endpoint delete."""
        api_exception = ApiException(status=404, reason="Not Found")
        mock_handle_404.side_effect = Exception("Enhanced 404 message")
        
        @handle_cli_exceptions(
            resource_type=ResourceType.HYP_JUMPSTART_ENDPOINT,
            operation_type=OperationType.DELETE
        )
        def js_delete(name, namespace="default"):
            raise api_exception
        
        js_delete(name="missing-endpoint", namespace="production")
        
        mock_handle_404.assert_called_once_with(
            "missing-endpoint", "production", 
            ResourceType.HYP_JUMPSTART_ENDPOINT, OperationType.DELETE
        )
        # Should call click.echo with the enhanced message (may be called multiple times due to error re-handling)
        mock_click.echo.assert_any_call("Enhanced 404 message")
        # sys.exit may be called multiple times due to exception re-handling
        assert mock_sys.exit.call_count >= 1
        mock_sys.exit.assert_called_with(1)
    
    @patch('sagemaker.hyperpod.common.cli_decorators.handle_404')
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_complete_custom_describe_flow(self, mock_sys, mock_click, mock_handle_404):
        """Test complete flow for custom endpoint describe."""
        api_exception = ApiException(status=404, reason="Not Found")
        mock_handle_404.side_effect = Exception("Custom endpoint not found message")
        
        @handle_cli_exceptions(
            resource_type=ResourceType.HYP_CUSTOM_ENDPOINT,
            operation_type=OperationType.DESCRIBE
        )
        def custom_describe(name, namespace="default"):
            raise api_exception
        
        custom_describe(name="missing-custom", namespace="staging")
        
        mock_handle_404.assert_called_once_with(
            "missing-custom", "staging",
            ResourceType.HYP_CUSTOM_ENDPOINT, OperationType.DESCRIBE
        )
        # Should call click.echo with the enhanced message (may be called multiple times due to error re-handling)
        mock_click.echo.assert_any_call("Custom endpoint not found message")
        # sys.exit may be called multiple times due to exception re-handling
        assert mock_sys.exit.call_count >= 1
        mock_sys.exit.assert_called_with(1)
    
    @patch('sagemaker.hyperpod.common.cli_decorators.handle_404')
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_complete_training_list_flow(self, mock_sys, mock_click, mock_handle_404):
        """Test complete flow for training job list."""
        api_exception = ApiException(status=404, reason="Not Found")
        mock_handle_404.side_effect = Exception("Training job not found message")
        
        @handle_cli_exceptions(
            resource_type=ResourceType.HYP_PYTORCH_JOB,
            operation_type=OperationType.LIST
        )
        def training_list(name, namespace="default"):
            raise api_exception
        
        training_list(name="missing-job")  # Uses default namespace
        
        mock_handle_404.assert_called_once_with(
            "missing-job", "default",
            ResourceType.HYP_PYTORCH_JOB, OperationType.LIST
        )
        # Should call click.echo with the enhanced message (may be called multiple times due to error re-handling)
        mock_click.echo.assert_any_call("Training job not found message")
        # sys.exit may be called multiple times due to exception re-handling
        assert mock_sys.exit.call_count >= 1
        mock_sys.exit.assert_called_with(1)
    
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_non_404_exception_passthrough(self, mock_sys, mock_click):
        """Test non-404 exceptions are handled normally."""
        @handle_cli_exceptions(
            resource_type=ResourceType.HYP_JUMPSTART_ENDPOINT,
            operation_type=OperationType.DELETE
        )
        def js_delete(name, namespace="default"):
            raise ValueError("Invalid configuration")
        
        js_delete(name="test-endpoint")
        
        mock_click.echo.assert_called_once_with("Invalid configuration")
        mock_sys.exit.assert_called_once_with(1)
    
    def test_function_with_no_exceptions(self):
        """Test function that completes successfully."""
        @handle_cli_exceptions(
            resource_type=ResourceType.HYP_JUMPSTART_ENDPOINT,
            operation_type=OperationType.DELETE
        )
        def successful_function(name, namespace="default"):
            return f"Success: {name} in {namespace}"
        
        result = successful_function(name="test", namespace="production")
        assert result == "Success: test in production"
