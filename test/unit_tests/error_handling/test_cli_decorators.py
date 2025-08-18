"""
Unit tests for cli_decorators module.
Tests all CLI exception handling decorators and auto-detection functionality.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from kubernetes.client.exceptions import ApiException

from sagemaker.hyperpod.common.cli_decorators import (
    handle_cli_exceptions,
    handle_cli_exceptions_with_debug,
    smart_cli_exception_handler,
    _detect_resource_type,
    _detect_operation_type
)
from sagemaker.hyperpod.common.error_constants import ResourceType, OperationType


class TestHandleCliExceptions:
    """Test handle_cli_exceptions decorator."""
    
    def test_successful_function_execution(self):
        """Test decorator allows successful function execution."""
        @handle_cli_exceptions
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_exception_handling(self, mock_sys, mock_click):
        """Test decorator handles exceptions correctly."""
        @handle_cli_exceptions
        def failing_function():
            raise Exception("Test error")
        
        failing_function()
        
        mock_click.echo.assert_called_once_with("Test error")
        mock_sys.exit.assert_called_once_with(1)
    
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_preserves_function_metadata(self, mock_sys, mock_click):
        """Test decorator preserves original function metadata."""
        @handle_cli_exceptions
        def documented_function():
            """This is a test function."""
            pass
        
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a test function."


class TestHandleCliExceptionsWithDebug:
    """Test handle_cli_exceptions_with_debug decorator."""
    
    def test_successful_function_execution(self):
        """Test decorator allows successful function execution."""
        @handle_cli_exceptions_with_debug
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    @patch('sagemaker.hyperpod.common.cli_decorators.logger')
    def test_exception_handling_with_debug(self, mock_logger, mock_sys, mock_click):
        """Test decorator handles exceptions with debug logging."""
        @handle_cli_exceptions_with_debug
        def failing_function():
            raise Exception("Debug test error")
        
        failing_function()
        
        mock_logger.debug.assert_called_once()
        mock_click.echo.assert_called_once_with("Debug test error")
        mock_sys.exit.assert_called_once_with(1)
    
    def test_preserves_function_metadata(self):
        """Test decorator preserves original function metadata."""
        @handle_cli_exceptions_with_debug
        def documented_function():
            """This is a debug test function."""
            pass
        
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a debug test function."


class TestSmartCliExceptionHandler:
    """Test smart_cli_exception_handler decorator."""
    
    def test_successful_function_execution(self):
        """Test decorator allows successful function execution."""
        @smart_cli_exception_handler
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
        
        @smart_cli_exception_handler
        def js_delete(name, namespace):
            raise api_exception
        
        # Mock handle_404 to raise Exception with enhanced message
        mock_handle_404.side_effect = Exception("❓ JumpStart endpoint 'test' not found...")
        
        js_delete(name="test", namespace="default")
        
        # Should call handle_404 with detected parameters
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
        @smart_cli_exception_handler
        def failing_function():
            raise Exception("Generic error")
        
        failing_function()
        
        mock_click.echo.assert_called_once_with("Generic error")
        mock_sys.exit.assert_called_once_with(1)
    
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_non_api_exception_handling(self, mock_sys, mock_click):
        """Test decorator handles non-ApiException errors normally."""
        @smart_cli_exception_handler
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
        
        @smart_cli_exception_handler
        def unknown_function(name, namespace):
            raise api_exception
        
        unknown_function(name="test", namespace="default")
        
        # Should not call handle_404 since detection failed
        mock_handle_404.assert_not_called()
        mock_click.echo.assert_called_once_with("(404)\nReason: Not Found\n")
        mock_sys.exit.assert_called_once_with(1)
    
    def test_preserves_function_metadata(self):
        """Test decorator preserves original function metadata."""
        @smart_cli_exception_handler
        def documented_function():
            """This is a smart test function."""
            pass
        
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a smart test function."


class TestDetectResourceType:
    """Test _detect_resource_type function."""
    
    def test_detect_jumpstart_from_js_prefix(self):
        """Test detection of JumpStart endpoint from 'js_' prefix."""
        mock_func = Mock()
        mock_func.__name__ = "js_delete"
        
        result = _detect_resource_type(mock_func)
        assert result == ResourceType.HYP_JUMPSTART_ENDPOINT
    
    def test_detect_jumpstart_from_jumpstart_keyword(self):
        """Test detection of JumpStart endpoint from 'jumpstart' keyword."""
        mock_func = Mock()
        mock_func.__name__ = "delete_jumpstart_endpoint"
        
        result = _detect_resource_type(mock_func)
        assert result == ResourceType.HYP_JUMPSTART_ENDPOINT
    
    def test_detect_custom_endpoint(self):
        """Test detection of custom endpoint."""
        mock_func = Mock()
        mock_func.__name__ = "custom_delete"
        
        result = _detect_resource_type(mock_func)
        assert result == ResourceType.HYP_CUSTOM_ENDPOINT
    
    def test_detect_pytorch_job_from_pytorch(self):
        """Test detection of PyTorch job from 'pytorch' keyword."""
        mock_func = Mock()
        mock_func.__name__ = "pytorch_job_delete"
        
        result = _detect_resource_type(mock_func)
        assert result == ResourceType.HYP_PYTORCH_JOB
    
    def test_detect_pytorch_job_from_training(self):
        """Test detection of PyTorch job from 'training' keyword."""
        mock_func = Mock()
        mock_func.__name__ = "training_delete"
        
        result = _detect_resource_type(mock_func)
        assert result == ResourceType.HYP_PYTORCH_JOB
    
    def test_detect_from_function_name_attribute(self):
        """Test detection using function.name attribute."""
        mock_func = Mock()
        mock_func.__name__ = "some_function"
        mock_func.name = "jumpstart-command"
        
        result = _detect_resource_type(mock_func)
        assert result == ResourceType.HYP_JUMPSTART_ENDPOINT
    
    def test_detection_failure_returns_none(self):
        """Test detection returns None for unknown patterns."""
        mock_func = Mock()
        mock_func.__name__ = "unknown_function"
        
        result = _detect_resource_type(mock_func)
        assert result is None

class TestDetectOperationType:
    """Test _detect_operation_type function."""
    
    def test_detect_delete_operation(self):
        """Test detection of DELETE operation."""
        mock_func = Mock()
        mock_func.__name__ = "js_delete"
        
        result = _detect_operation_type(mock_func)
        assert result == OperationType.DELETE
    
    def test_detect_describe_operation(self):
        """Test detection of DESCRIBE operation."""
        mock_func = Mock()
        mock_func.__name__ = "js_describe"
        
        result = _detect_operation_type(mock_func)
        assert result == OperationType.DESCRIBE
    
    def test_detect_get_operation(self):
        """Test detection of DESCRIBE operation from 'get'."""
        mock_func = Mock()
        mock_func.__name__ = "get_endpoint"
        
        result = _detect_operation_type(mock_func)
        assert result == OperationType.DESCRIBE
    
    def test_detect_list_operation(self):
        """Test detection of LIST operation."""
        mock_func = Mock()
        mock_func.__name__ = "list_endpoints"
        
        result = _detect_operation_type(mock_func)
        assert result == OperationType.LIST
    
    def test_fallback_to_get(self):
        """Test fallback to GET operation for unknown patterns."""
        mock_func = Mock()
        mock_func.__name__ = "unknown_operation"
        
        result = _detect_operation_type(mock_func)
        assert result == OperationType.GET


class TestIntegrationSmartHandler:
    """Integration tests for smart CLI exception handler."""
    
    @patch('sagemaker.hyperpod.common.cli_decorators.handle_404')
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_complete_jumpstart_delete_flow(self, mock_sys, mock_click, mock_handle_404):
        """Test complete flow for JumpStart endpoint delete."""
        api_exception = ApiException(status=404, reason="Not Found")
        mock_handle_404.side_effect = Exception("Enhanced 404 message")
        
        @smart_cli_exception_handler
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
        
        @smart_cli_exception_handler
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
        
        @smart_cli_exception_handler
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
        @smart_cli_exception_handler
        def js_delete(name, namespace="default"):
            raise ValueError("Invalid configuration")
        
        js_delete(name="test-endpoint")
        
        mock_click.echo.assert_called_once_with("Invalid configuration")
        mock_sys.exit.assert_called_once_with(1)
    
    def test_function_with_no_exceptions(self):
        """Test function that completes successfully."""
        @smart_cli_exception_handler
        def successful_function(name, namespace="default"):
            return f"Success: {name} in {namespace}"
        
        result = successful_function(name="test", namespace="production")
        assert result == "Success: test in production"
