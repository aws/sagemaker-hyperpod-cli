"""
Unit tests for cli_decorators module.
Tests template-agnostic CLI exception handling decorators and auto-detection functionality.
"""

import pytest
import sys
import click
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from kubernetes.client.exceptions import ApiException

from sagemaker.hyperpod.common.cli_decorators import (
    handle_cli_exceptions,
    _extract_resource_from_command,
    _detect_operation_type_from_function,
    _get_list_command_from_resource_type
)


class TestHandleCliExceptions:
    """Test template-agnostic handle_cli_exceptions decorator."""
    
    def test_successful_function_execution(self):
        """Test decorator allows successful function execution."""
        @handle_cli_exceptions()
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_exception_handling(self, mock_sys, mock_click):
        """Test decorator handles exceptions correctly."""
        @handle_cli_exceptions()
        def failing_function():
            raise Exception("Test error")
        
        failing_function()
        
        mock_click.echo.assert_called_once_with("Test error")
        mock_sys.exit.assert_called_once_with(1)
    
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_preserves_function_metadata(self, mock_sys, mock_click):
        """Test decorator preserves original function metadata."""
        @handle_cli_exceptions()
        def documented_function():
            """This is a test function."""
            pass
        
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a test function."


class TestTemplateAgnosticDetection:
    """Test template-agnostic resource and operation detection."""
    
    def test_extract_resource_from_command(self):
        """Test resource type extraction from Click command names."""
        # Mock function with Click command name
        mock_func = Mock()
        mock_func.name = "hyp-jumpstart-endpoint"
        
        raw_resource_type, display_name = _extract_resource_from_command(mock_func)
        assert raw_resource_type == "jumpstart-endpoint"
        assert display_name == "JumpStart Endpoint"
    
    def test_extract_resource_from_pytorch_command(self):
        """Test resource type extraction for PyTorch jobs."""
        mock_func = Mock()
        mock_func.name = "hyp-pytorch-job"
        
        raw_resource_type, display_name = _extract_resource_from_command(mock_func)
        assert raw_resource_type == "pytorch-job"
        assert display_name == "PyTorch Job"
    
    def test_extract_resource_from_custom_command(self):
        """Test resource type extraction for custom endpoints."""
        mock_func = Mock()
        mock_func.name = "hyp-custom-endpoint"
        
        raw_resource_type, display_name = _extract_resource_from_command(mock_func)
        assert raw_resource_type == "custom-endpoint"
        assert display_name == "Custom Endpoint"
    
    def test_extract_resource_from_future_template(self):
        """Test resource type extraction works with future templates."""
        mock_func = Mock()
        mock_func.name = "hyp-llama-job"
        
        raw_resource_type, display_name = _extract_resource_from_command(mock_func)
        assert raw_resource_type == "llama-job"
        assert display_name == "Llama Job"
    
    def test_extract_resource_fallback(self):
        """Test resource type extraction fallback."""
        mock_func = Mock()
        mock_func.name = None
        mock_func.__name__ = "js_delete"
        
        raw_resource_type, display_name = _extract_resource_from_command(mock_func)
        assert raw_resource_type == "resource"
        assert display_name == "Resource"
    
    def test_detect_operation_from_function_name(self):
        """Test operation type detection from function names."""
        mock_func = Mock()
        mock_func.__name__ = "js_delete"
        
        result = _detect_operation_type_from_function(mock_func)
        assert result == "delete"
    
    def test_detect_operation_describe(self):
        """Test operation type detection for describe operations."""
        mock_func = Mock()
        mock_func.__name__ = "pytorch_describe"
        
        result = _detect_operation_type_from_function(mock_func)
        assert result == "describe"
    
    def test_detect_operation_list(self):
        """Test operation type detection for list operations."""
        mock_func = Mock()
        mock_func.__name__ = "custom_list_pods"
        
        result = _detect_operation_type_from_function(mock_func)
        assert result == "list"
    
    def test_get_list_command_generation(self):
        """Test list command generation from resource types."""
        result = _get_list_command_from_resource_type("jumpstart-endpoint")
        assert result == "hyp list hyp-jumpstart-endpoint"
        
        result = _get_list_command_from_resource_type("pytorch-job")
        assert result == "hyp list hyp-pytorch-job"
        
        result = _get_list_command_from_resource_type("future-template")
        assert result == "hyp list hyp-future-template"


class TestTemplateAgnostic404Handling:
    """Test template-agnostic 404 handling functionality."""
    
    @patch('sagemaker.hyperpod.common.cli_decorators._get_available_resource_count')
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_404_exception_with_dynamic_detection(self, mock_sys, mock_click, mock_get_count):
        """Test 404 exception handling with dynamic resource/operation detection."""
        # Mock the resource count to avoid actual API calls
        mock_get_count.return_value = 3
        
        api_exception = ApiException(status=404, reason="Not Found")
        
        # Test the decorator directly
        @handle_cli_exceptions()
        def js_delete(name, namespace="default"):
            raise api_exception
        
        # Manually set the function attributes to simulate Click command
        js_delete.name = "hyp-jumpstart-endpoint"
        
        js_delete(name="test", namespace="default")
        
        # With mocked sys.exit, both enhanced and standard handling occur
        assert mock_click.echo.call_count == 2
        # First call should be our enhanced 404 message
        first_call_args = mock_click.echo.call_args_list[0][0][0]
        assert "'test' not found" in first_call_args
        assert "namespace 'default'" in first_call_args
        assert "There are 3 resources" in first_call_args
        assert "hyp list" in first_call_args
        mock_sys.exit.assert_called_with(1)
    
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_non_404_exception_handling(self, mock_sys, mock_click):
        """Test non-404 exceptions are handled normally."""
        @handle_cli_exceptions()
        def failing_function():
            raise Exception("Generic error")
        
        failing_function()
        
        mock_click.echo.assert_called_once_with("Generic error")
        mock_sys.exit.assert_called_once_with(1)
    
    @patch('sagemaker.hyperpod.common.cli_decorators._get_available_resource_count')
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_fallback_404_message(self, mock_sys, mock_click, mock_get_count):
        """Test fallback message when dynamic detection fails."""
        # Mock the resource count to fail and trigger fallback
        mock_get_count.side_effect = Exception("Count failed")
        
        api_exception = ApiException(status=404, reason="Not Found")
        
        @handle_cli_exceptions()
        def unknown_function(name, namespace):
            raise api_exception
        
        unknown_function(name="test", namespace="default")
        
        # Should display fallback message - expecting 2 calls due to mocked sys.exit
        assert mock_click.echo.call_count == 2
        # First call should be the fallback message
        first_call_args = mock_click.echo.call_args_list[0][0][0]
        assert "'test' not found" in first_call_args
        assert "namespace 'default'" in first_call_args
        assert "Unknown" in first_call_args or "Resource" in first_call_args
        mock_sys.exit.assert_called_with(1)
