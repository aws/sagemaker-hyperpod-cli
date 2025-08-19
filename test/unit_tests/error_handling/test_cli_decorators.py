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
    _get_list_command_from_resource_type,
    _check_resources_exist
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
        mock_func.name = "hyp-resource-endpoint"
        
        raw_resource_type, display_name = _extract_resource_from_command(mock_func)
        assert raw_resource_type == "resource-endpoint"
        assert display_name == "Resource Endpoint"
    
    def test_extract_resource_from_job_command(self):
        """Test resource type extraction for job resources."""
        mock_func = Mock()
        mock_func.name = "hyp-training-job"
        
        raw_resource_type, display_name = _extract_resource_from_command(mock_func)
        assert raw_resource_type == "training-job"
        assert display_name == "Training Job"
    
    def test_extract_resource_from_service_command(self):
        """Test resource type extraction for service resources."""
        mock_func = Mock()
        mock_func.name = "hyp-ml-service"
        
        raw_resource_type, display_name = _extract_resource_from_command(mock_func)
        assert raw_resource_type == "ml-service"
        assert display_name == "Ml Service"
    
    def test_extract_resource_from_future_template(self):
        """Test resource type extraction works with future templates."""
        mock_func = Mock()
        mock_func.name = "hyp-new-resource"
        
        raw_resource_type, display_name = _extract_resource_from_command(mock_func)
        assert raw_resource_type == "new-resource"
        assert display_name == "New Resource"
    
    def test_extract_resource_fallback(self):
        """Test resource type extraction fallback."""
        mock_func = Mock()
        # Explicitly control what attributes exist
        del mock_func.name  # Remove the name attribute completely
        mock_func.__name__ = "resource_delete"
        
        # Ensure no callback or __wrapped__ attributes exist
        if hasattr(mock_func, 'callback'):
            del mock_func.callback
        if hasattr(mock_func, '__wrapped__'):
            del mock_func.__wrapped__
        
        raw_resource_type, display_name = _extract_resource_from_command(mock_func)
        assert raw_resource_type == "resource-resource"
        assert display_name == "Resource"
    
    
    def test_get_list_command_generation(self):
        """Test list command generation from resource types."""
        result = _get_list_command_from_resource_type("resource-endpoint")
        assert result == "hyp list hyp-resource-endpoint"
        
        result = _get_list_command_from_resource_type("training-job")
        assert result == "hyp list hyp-training-job"
        
        result = _get_list_command_from_resource_type("future-template")
        assert result == "hyp list hyp-future-template"


class TestTemplateAgnostic404Handling:
    """Test template-agnostic 404 handling functionality."""
    
    @patch('sagemaker.hyperpod.common.cli_decorators._check_resources_exist')
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_404_exception_with_dynamic_detection(self, mock_sys, mock_click, mock_check_resources):
        """Test 404 exception handling with dynamic resource/operation detection."""
        # Simulate resources exist in namespace
        mock_check_resources.return_value = True
        
        api_exception = ApiException(status=404, reason="Not Found")
        
        # Test the decorator directly
        @handle_cli_exceptions()
        def resource_delete(name, namespace="default"):
            raise api_exception
        
        # Manually set the function attributes to simulate Click command
        resource_delete.name = "hyp-resource-endpoint"
        
        resource_delete(name="test", namespace="default")
        
        # Should show enhanced message when resources exist
        mock_click.echo.assert_called_once()
        first_call_args = mock_click.echo.call_args[0][0]
        assert "'test' not found" in first_call_args
        assert "namespace 'default'" in first_call_args
        assert "other resources exist in this namespace" in first_call_args
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
    
    @patch('sagemaker.hyperpod.common.cli_decorators._check_resources_exist')
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_fallback_404_message(self, mock_sys, mock_click, mock_check_resources):
        """Test template-agnostic 404 message with generic resource detection."""
        # Simulate no resources exist
        mock_check_resources.return_value = False
        
        api_exception = ApiException(status=404, reason="Not Found")
        
        @handle_cli_exceptions()
        def unknown_function(name, namespace):
            raise api_exception
        
        unknown_function(name="test", namespace="default")
        
        # Should show message indicating no resources exist
        mock_click.echo.assert_called_once()
        first_call_args = mock_click.echo.call_args[0][0]
        assert "'test' not found" in first_call_args
        assert "namespace 'default'" in first_call_args
        assert "No resources of this type exist" in first_call_args
        assert "hyp list" in first_call_args
        mock_sys.exit.assert_called_with(1)
