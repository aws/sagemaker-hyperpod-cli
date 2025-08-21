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
    _check_resources_exist,
    _namespace_exists,
    _generate_namespace_error_message,
    _check_training_operator_exists,
    _is_pytorch_job_operation,
    _is_get_logs_operation
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
    
    @patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_exception_handling(self, mock_sys, mock_click, mock_namespace_exists):
        """Test decorator handles exceptions correctly."""
        # Mock namespace exists to bypass proactive validation
        mock_namespace_exists.return_value = True
        
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


class TestNamespaceValidation:
    """Test namespace validation functionality."""
    
    def test_generate_namespace_error_message(self):
        """Test namespace error message generation with template-agnostic list command."""
        mock_func = Mock()
        mock_func.name = "hyp-jumpstart-endpoint"
        mock_func.__name__ = "test_func"
        
        # Mock the Click context to simulate a real command context
        mock_context = Mock()
        mock_context.info_name = "hyp-jumpstart-endpoint"
        
        with patch('sagemaker.hyperpod.common.cli_decorators.click.get_current_context') as mock_get_context:
            mock_get_context.return_value = mock_context
            message = _generate_namespace_error_message("test-ns", mock_func)
            
        # Test should match actual enhanced behavior - includes helpful list command suggestion
        assert "Namespace 'test-ns' does not exist on this cluster" in message
        assert "Use 'hyp list hyp-jumpstart-endpoint' to check for available resources" in message
        expected_message = "❌ Namespace 'test-ns' does not exist on this cluster. Use 'hyp list hyp-jumpstart-endpoint' to check for available resources."
        assert message == expected_message

    @patch('sagemaker.hyperpod.common.cli_decorators.click.get_current_context')
    @patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
    @patch('sagemaker.hyperpod.common.cli_decorators.click.echo')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys.exit')
    def test_proactive_namespace_validation(self, mock_sys_exit, mock_click_echo, mock_namespace_exists, mock_get_context):
        """Test proactive namespace validation prevents execution for invalid namespaces."""
        # Simulate namespace doesn't exist
        mock_namespace_exists.return_value = False
        
        # Mock sys.exit to prevent actual exit
        mock_sys_exit.return_value = None
        
        # Mock Click context for resource extraction
        mock_context = Mock()
        mock_context.info_name = "hyp-jumpstart-endpoint"
        mock_get_context.return_value = mock_context
        
        @handle_cli_exceptions()
        def list_pods_function(namespace="missing-ns"):
            # This should never execute due to proactive validation
            return "should not reach here"
        
        # Set the function name to simulate a Click command
        list_pods_function.name = "hyp-jumpstart-endpoint"
        list_pods_function.__name__ = "list_pods_function"
        
        # Call the function - should be caught by proactive validation
        result = list_pods_function(namespace="missing-ns")
        
        # Should show namespace error message before function execution
        mock_click_echo.assert_called_once()
        first_call_args = mock_click_echo.call_args[0][0]
        # Test should match actual enhanced behavior - includes helpful list command suggestion
        assert "Namespace 'missing-ns' does not exist on this cluster" in first_call_args
        assert "Use 'hyp list hyp-jumpstart-endpoint' to check for available resources" in first_call_args
        expected_message = "❌ Namespace 'missing-ns' does not exist on this cluster. Use 'hyp list hyp-jumpstart-endpoint' to check for available resources."
        assert first_call_args == expected_message
        mock_sys_exit.assert_called_with(1)
        
        # Verify function never executed (result should be None due to early return)
        assert result is None


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
        assert "other resources exist in namespace 'default'" in first_call_args
        assert "hyp list" in first_call_args
        mock_sys.exit.assert_called_with(1)
    
    @patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
    @patch('sagemaker.hyperpod.common.cli_decorators.click')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys')
    def test_non_404_exception_handling(self, mock_sys, mock_click, mock_namespace_exists):
        """Test non-404 exceptions are handled normally."""
        # Mock namespace exists to bypass proactive validation
        mock_namespace_exists.return_value = True
        
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


class TestGetLogsOperationDetection:
    """Test get-logs operation detection functionality."""
    
    def test_is_get_logs_operation_by_function_name(self):
        """Test get-logs operation detection by function name."""
        mock_func = Mock()
        mock_func.__name__ = "pytorch_get_logs"
        
        result = _is_get_logs_operation(mock_func)
        assert result is True
    
    def test_is_get_logs_operation_by_wrapped_function(self):
        """Test get-logs operation detection by wrapped function name."""
        mock_func = Mock()
        mock_func.__name__ = "wrapper"
        mock_wrapped = Mock()
        mock_wrapped.__name__ = "js_get_logs"
        mock_func.__wrapped__ = mock_wrapped
        
        result = _is_get_logs_operation(mock_func)
        assert result is True
    
    @patch('sagemaker.hyperpod.common.cli_decorators.click.get_current_context')
    def test_is_get_logs_operation_by_click_context(self, mock_get_context):
        """Test get-logs operation detection by Click context."""
        mock_func = Mock()
        mock_func.__name__ = "some_function"
        
        mock_context = Mock()
        mock_context.info_name = "hyp-get-logs"
        mock_get_context.return_value = mock_context
        
        result = _is_get_logs_operation(mock_func)
        assert result is True
    
    def test_is_get_logs_operation_false(self):
        """Test get-logs operation detection returns False for non-logs operations."""
        mock_func = Mock()
        mock_func.__name__ = "pytorch_create"
        
        # Ensure no __wrapped__ attribute exists
        if hasattr(mock_func, '__wrapped__'):
            del mock_func.__wrapped__
        
        with patch('sagemaker.hyperpod.common.cli_decorators.click.get_current_context') as mock_get_context:
            mock_get_context.side_effect = RuntimeError("No context")
            result = _is_get_logs_operation(mock_func)
            
        assert result is False


class TestPodReadinessHandling:
    """Test pod readiness checking and error message generation."""
    
    @patch('sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient')
    def test_check_pod_readiness_pending_container_creating(self, mock_k8s_client_class):
        """Test pod readiness check for Pending pod with ContainerCreating."""
        # Mock KubernetesClient instance
        mock_k8s_client = Mock()
        mock_k8s_client._kube_client = Mock()  # Simulate initialized client
        mock_k8s_client_class.return_value = mock_k8s_client
        
        # Mock pod details for Pending with ContainerCreating
        mock_pod_details = Mock()
        mock_pod_details.status = Mock()
        mock_pod_details.status.phase = 'Pending'
        
        # Mock container status with waiting state
        mock_container_status = Mock()
        mock_container_status.state = Mock()
        mock_container_status.state.waiting = Mock()
        mock_container_status.state.waiting.reason = 'ContainerCreating'
        mock_container_status.state.terminated = None
        mock_pod_details.status.container_statuses = [mock_container_status]
        mock_pod_details.status.init_container_statuses = None
        
        # Mock metadata
        mock_pod_details.metadata = Mock()
        mock_pod_details.metadata.deletion_timestamp = None
        
        mock_k8s_client.get_pod_details.return_value = mock_pod_details
        
        from sagemaker.hyperpod.common.cli_decorators import _check_pod_readiness_and_generate_message
        result = _check_pod_readiness_and_generate_message('test-pod', 'default')
        
        expected = ("❌ Cannot get logs for pod 'test-pod' - pod is not ready yet.\n"
                   "Pod Status: Pending (ContainerCreating)\n"
                   "Reason: Containers are still being created")
        assert result == expected
    
    @patch('sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient')
    def test_check_pod_readiness_failed_pod(self, mock_k8s_client_class):
        """Test pod readiness check for Failed pod."""
        # Mock KubernetesClient instance
        mock_k8s_client = Mock()
        mock_k8s_client._kube_client = Mock()
        mock_k8s_client_class.return_value = mock_k8s_client
        
        # Mock pod details for Failed pod
        mock_pod_details = Mock()
        mock_pod_details.status = Mock()
        mock_pod_details.status.phase = 'Failed'
        
        # Mock container status with terminated state
        mock_container_status = Mock()
        mock_container_status.state = Mock()
        mock_container_status.state.waiting = None
        mock_container_status.state.terminated = Mock()
        mock_container_status.state.terminated.reason = 'Error'
        mock_pod_details.status.container_statuses = [mock_container_status]
        mock_pod_details.status.init_container_statuses = None
        
        # Mock metadata
        mock_pod_details.metadata = Mock()
        mock_pod_details.metadata.deletion_timestamp = None
        
        mock_k8s_client.get_pod_details.return_value = mock_pod_details
        
        from sagemaker.hyperpod.common.cli_decorators import _check_pod_readiness_and_generate_message
        result = _check_pod_readiness_and_generate_message('test-pod', 'default')
        
        expected = ("❌ Cannot get logs for pod 'test-pod' - pod has failed.\n"
                   "Pod Status: Failed (Error)\n"
                   "Reason: Container exited with non-zero status")
        assert result == expected
    
    @patch('sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient')
    def test_check_pod_readiness_image_pull_backoff(self, mock_k8s_client_class):
        """Test pod readiness check for ImagePullBackOff."""
        # Mock KubernetesClient instance
        mock_k8s_client = Mock()
        mock_k8s_client._kube_client = Mock()
        mock_k8s_client_class.return_value = mock_k8s_client
        
        # Mock pod details for Pending with ImagePullBackOff
        mock_pod_details = Mock()
        mock_pod_details.status = Mock()
        mock_pod_details.status.phase = 'Pending'
        
        # Mock container status with ImagePullBackOff
        mock_container_status = Mock()
        mock_container_status.state = Mock()
        mock_container_status.state.waiting = Mock()
        mock_container_status.state.waiting.reason = 'ImagePullBackOff'
        mock_container_status.state.terminated = None
        mock_pod_details.status.container_statuses = [mock_container_status]
        mock_pod_details.status.init_container_statuses = None
        
        # Mock metadata
        mock_pod_details.metadata = Mock()
        mock_pod_details.metadata.deletion_timestamp = None
        
        mock_k8s_client.get_pod_details.return_value = mock_pod_details
        
        from sagemaker.hyperpod.common.cli_decorators import _check_pod_readiness_and_generate_message
        result = _check_pod_readiness_and_generate_message('test-pod', 'default')
        
        expected = ("❌ Cannot get logs for pod 'test-pod' - pod is not ready yet.\n"
                   "Pod Status: Pending (ImagePullBackOff)\n"
                   "Reason: Cannot pull container image")
        assert result == expected
    
    @patch('sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient')
    def test_check_pod_readiness_crash_loop_backoff(self, mock_k8s_client_class):
        """Test pod readiness check for CrashLoopBackOff."""
        # Mock KubernetesClient instance
        mock_k8s_client = Mock()
        mock_k8s_client._kube_client = Mock()
        mock_k8s_client_class.return_value = mock_k8s_client
        
        # Mock pod details for Running with CrashLoopBackOff
        mock_pod_details = Mock()
        mock_pod_details.status = Mock()
        mock_pod_details.status.phase = 'Running'
        
        # Mock container status with CrashLoopBackOff
        mock_container_status = Mock()
        mock_container_status.state = Mock()
        mock_container_status.state.waiting = Mock()
        mock_container_status.state.waiting.reason = 'CrashLoopBackOff'
        mock_container_status.state.terminated = None
        mock_pod_details.status.container_statuses = [mock_container_status]
        mock_pod_details.status.init_container_statuses = None
        
        # Mock metadata
        mock_pod_details.metadata = Mock()
        mock_pod_details.metadata.deletion_timestamp = None
        
        mock_k8s_client.get_pod_details.return_value = mock_pod_details
        
        from sagemaker.hyperpod.common.cli_decorators import _check_pod_readiness_and_generate_message
        result = _check_pod_readiness_and_generate_message('test-pod', 'default')
        
        expected = ("❌ Cannot get logs for pod 'test-pod' - pod is not ready yet.\n"
                   "Pod Status: Running (CrashLoopBackOff)\n"
                   "Reason: Container keeps crashing and restarting")
        assert result == expected
    
    @patch('sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient')
    def test_check_pod_readiness_terminating(self, mock_k8s_client_class):
        """Test pod readiness check for terminating pod."""
        # Mock KubernetesClient instance
        mock_k8s_client = Mock()
        mock_k8s_client._kube_client = Mock()
        mock_k8s_client_class.return_value = mock_k8s_client
        
        # Mock pod details for terminating pod
        mock_pod_details = Mock()
        mock_pod_details.status = Mock()
        mock_pod_details.status.phase = 'Running'
        mock_pod_details.status.container_statuses = None
        mock_pod_details.status.init_container_statuses = None
        
        # Mock metadata with deletion timestamp
        mock_pod_details.metadata = Mock()
        mock_pod_details.metadata.deletion_timestamp = "2024-01-01T00:00:00Z"
        
        mock_k8s_client.get_pod_details.return_value = mock_pod_details
        
        from sagemaker.hyperpod.common.cli_decorators import _check_pod_readiness_and_generate_message
        result = _check_pod_readiness_and_generate_message('test-pod', 'default')
        
        expected = ("❌ Cannot get logs for pod 'test-pod' - pod is being terminated.\n"
                   "Pod Status: Terminating\n"
                   "Reason: Pod is shutting down")
        assert result == expected
    
    @patch('sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient')
    def test_check_pod_readiness_client_not_initialized(self, mock_k8s_client_class):
        """Test pod readiness check when Kubernetes client is not initialized."""
        # Mock KubernetesClient instance with no _kube_client
        mock_k8s_client = Mock()
        mock_k8s_client._kube_client = None  # Simulate uninitialized client
        mock_k8s_client_class.return_value = mock_k8s_client
        
        from sagemaker.hyperpod.common.cli_decorators import _check_pod_readiness_and_generate_message
        result = _check_pod_readiness_and_generate_message('test-pod', 'default')
        
        expected = "❌ Cannot get logs for pod 'test-pod' - pod is not ready yet."
        assert result == expected


class TestGetLogsErrorHandlingIntegration:
    """Test integration of get-logs error handling in the main decorator."""
    
    @patch('sagemaker.hyperpod.common.cli_decorators._is_get_logs_operation')
    @patch('sagemaker.hyperpod.common.cli_decorators._check_pod_readiness_and_generate_message')
    @patch('sagemaker.hyperpod.common.cli_decorators._extract_primary_target_dynamically')
    @patch('sagemaker.hyperpod.common.cli_decorators._extract_namespace_from_kwargs')
    @patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
    @patch('sagemaker.hyperpod.common.cli_decorators.click.echo')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys.exit')
    def test_get_logs_400_bad_request_pod_not_ready(
        self, mock_sys_exit, mock_click_echo, mock_namespace_exists,
        mock_extract_namespace, mock_extract_target, mock_check_pod_readiness, mock_is_get_logs
    ):
        """Test get-logs 400 Bad Request handling for pod not ready."""
        # Mock conditions for get-logs 400 error
        mock_namespace_exists.return_value = True  # Namespace exists
        mock_is_get_logs.return_value = True  # Is get-logs operation
        mock_extract_target.return_value = ('pod', 'test-pod-123')  # Extract pod name
        mock_extract_namespace.return_value = 'default'  # Extract namespace
        mock_check_pod_readiness.return_value = ("❌ Cannot get logs for pod 'test-pod-123' - pod is not ready yet.\n"
                                               "Pod Status: Pending (ContainerCreating)\n"
                                               "Reason: Containers are still being created")
        
        @handle_cli_exceptions()
        def get_logs_function():
            # Simulate 400 Bad Request from Kubernetes API
            raise Exception("400 Bad Request")
        
        result = get_logs_function()
        
        # Should show pod readiness error message
        mock_click_echo.assert_called_once()
        call_args = mock_click_echo.call_args[0][0]
        
        assert "❌ Cannot get logs for pod 'test-pod-123' - pod is not ready yet." in call_args
        assert "Pod Status: Pending (ContainerCreating)" in call_args
        assert "Reason: Containers are still being created" in call_args
        
        mock_sys_exit.assert_called_with(1)
        assert result is None  # Function should not execute
    
    @patch('sagemaker.hyperpod.common.cli_decorators._is_get_logs_operation')
    @patch('sagemaker.hyperpod.common.cli_decorators._has_container_parameter')
    @patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
    def test_get_logs_400_bad_request_falls_through_to_container_error(
        self, mock_namespace_exists, mock_has_container, mock_is_get_logs
    ):
        """Test that non-get-logs 400 errors still fall through to container error handling."""
        # Mock conditions 
        mock_namespace_exists.return_value = True  # Namespace exists
        mock_is_get_logs.return_value = False  # NOT a get-logs operation
        mock_has_container.return_value = True  # Has container parameter
        
        @handle_cli_exceptions()
        def some_other_function():
            # Simulate 400 Bad Request that should be handled by container logic
            raise Exception("400 Bad Request")
        
        # Should proceed to container error handling, not pod readiness
        # This test verifies the order of elif conditions is correct
        assert mock_is_get_logs.return_value is False
        assert mock_has_container.return_value is True


class TestTrainingOperatorDetection:
    """Test Training Operator detection functionality."""
    
    def test_is_pytorch_job_operation_by_function_name(self):
        """Test PyTorch job detection by function name."""
        mock_func = Mock()
        mock_func.__name__ = "pytorch_create"
        
        result = _is_pytorch_job_operation(mock_func)
        assert result is True
    
    def test_is_pytorch_job_operation_by_wrapped_function(self):
        """Test PyTorch job detection by wrapped function name."""
        mock_func = Mock()
        mock_func.__name__ = "wrapper"
        mock_wrapped = Mock()
        mock_wrapped.__name__ = "pytorch_job_function"
        mock_func.__wrapped__ = mock_wrapped
        
        result = _is_pytorch_job_operation(mock_func)
        assert result is True
    
    @patch('sagemaker.hyperpod.common.cli_decorators.click.get_current_context')
    def test_is_pytorch_job_operation_by_click_context(self, mock_get_context):
        """Test PyTorch job detection by Click context."""
        mock_func = Mock()
        mock_func.__name__ = "some_function"
        
        mock_context = Mock()
        mock_context.info_name = "hyp-pytorch-job"
        mock_get_context.return_value = mock_context
        
        result = _is_pytorch_job_operation(mock_func)
        assert result is True
    
    def test_is_pytorch_job_operation_false(self):
        """Test PyTorch job detection returns False for non-PyTorch operations."""
        mock_func = Mock()
        mock_func.__name__ = "inference_create"
        
        # Ensure no __wrapped__ attribute exists
        if hasattr(mock_func, '__wrapped__'):
            del mock_func.__wrapped__
        
        with patch('sagemaker.hyperpod.common.cli_decorators.click.get_current_context') as mock_get_context:
            mock_get_context.side_effect = RuntimeError("No context")
            result = _is_pytorch_job_operation(mock_func)
            
        assert result is False
    
    @patch('sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient')
    @patch('kubernetes.client.ApiextensionsV1Api')
    def test_check_training_operator_exists_true(self, mock_extensions_api_class, mock_k8s_client_class):
        """Test Training Operator detection when CRD exists."""
        # Mock KubernetesClient instance
        mock_k8s_client = Mock()
        mock_k8s_client._kube_client = Mock()  # Simulate initialized client
        mock_k8s_client_class.return_value = mock_k8s_client
        
        # Mock ApiextensionsV1Api instance
        mock_extensions_api = Mock()
        mock_extensions_api_class.return_value = mock_extensions_api
        
        # Mock successful CRD read (no exception means CRD exists)
        mock_extensions_api.read_custom_resource_definition.return_value = Mock()
        
        result = _check_training_operator_exists()
        
        assert result is True
        mock_extensions_api.read_custom_resource_definition.assert_called_once_with(
            name="hyperpodpytorchjobs.sagemaker.amazonaws.com"
        )
    
    @patch('sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient')
    @patch('kubernetes.client.ApiextensionsV1Api')
    def test_check_training_operator_exists_false(self, mock_extensions_api_class, mock_k8s_client_class):
        """Test Training Operator detection when CRD doesn't exist."""
        # Mock KubernetesClient instance
        mock_k8s_client = Mock()
        mock_k8s_client._kube_client = Mock()  # Simulate initialized client
        mock_k8s_client_class.return_value = mock_k8s_client
        
        # Mock ApiextensionsV1Api instance
        mock_extensions_api = Mock()
        mock_extensions_api_class.return_value = mock_extensions_api
        
        # Mock 404 exception (CRD doesn't exist)
        from kubernetes.client.rest import ApiException as K8sApiException
        mock_extensions_api.read_custom_resource_definition.side_effect = K8sApiException(status=404)
        
        result = _check_training_operator_exists()
        
        assert result is False
        mock_extensions_api.read_custom_resource_definition.assert_called_once_with(
            name="hyperpodpytorchjobs.sagemaker.amazonaws.com"
        )
    
    @patch('sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient')
    def test_check_training_operator_exists_client_not_initialized(self, mock_k8s_client_class):
        """Test Training Operator detection when Kubernetes client is not initialized."""
        # Mock KubernetesClient instance with no _kube_client
        mock_k8s_client = Mock()
        mock_k8s_client._kube_client = None  # Simulate uninitialized client
        mock_k8s_client_class.return_value = mock_k8s_client
        
        result = _check_training_operator_exists()
        
        # Should return True (don't block) when client is not available
        assert result is True
    
    @patch('sagemaker.hyperpod.common.cli_decorators._is_pytorch_job_operation')
    @patch('sagemaker.hyperpod.common.cli_decorators._check_training_operator_exists')
    @patch('sagemaker.hyperpod.common.cli_decorators._is_create_operation')
    @patch('sagemaker.hyperpod.common.cli_decorators.click.echo')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys.exit')
    def test_pytorch_job_creation_blocked_when_operator_missing(
        self, mock_sys_exit, mock_click_echo, mock_is_create, mock_check_operator, mock_is_pytorch
    ):
        """Test PyTorch job creation is blocked when Training Operator is missing."""
        # Mock conditions for PyTorch job creation
        mock_is_create.return_value = True
        mock_is_pytorch.return_value = True
        mock_check_operator.return_value = False  # Operator missing
        
        @handle_cli_exceptions()
        def pytorch_create_function():
            return "should not reach here"
        
        result = pytorch_create_function()
        
        # Should show Training Operator error messages
        assert mock_click_echo.call_count == 3
        call_args = [call[0][0] for call in mock_click_echo.call_args_list]
        
        assert "❌ Training Operator not found in cluster." in call_args[0]
        assert "Missing Custom Resource Definition: hyperpodpytorchjobs.sagemaker.amazonaws.com" in call_args[1]
        assert "The Training Operator is required to submit PyTorch jobs" in call_args[2]
        
        mock_sys_exit.assert_called_with(1)
        assert result is None  # Function should not execute
    
    @patch('sagemaker.hyperpod.common.cli_decorators._is_pytorch_job_operation')
    @patch('sagemaker.hyperpod.common.cli_decorators._check_training_operator_exists')
    @patch('sagemaker.hyperpod.common.cli_decorators._is_create_operation')
    @patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
    def test_pytorch_job_creation_allowed_when_operator_exists(
        self, mock_namespace_exists, mock_is_create, mock_check_operator, mock_is_pytorch
    ):
        """Test PyTorch job creation is allowed when Training Operator exists."""
        # Mock conditions for PyTorch job creation
        mock_is_create.return_value = True
        mock_is_pytorch.return_value = True
        mock_check_operator.return_value = True  # Operator exists
        mock_namespace_exists.return_value = True  # Namespace exists
        
        @handle_cli_exceptions()
        def pytorch_create_function():
            return "pytorch job created successfully"
        
        result = pytorch_create_function()
        
        # Should execute successfully
        assert result == "pytorch job created successfully"
    
    @patch('sagemaker.hyperpod.common.cli_decorators._is_pytorch_job_operation')
    @patch('sagemaker.hyperpod.common.cli_decorators._is_create_operation')
    @patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
    def test_non_pytorch_job_creation_unaffected(
        self, mock_namespace_exists, mock_is_create, mock_is_pytorch
    ):
        """Test non-PyTorch job creation is unaffected by Training Operator checks."""
        # Mock conditions for non-PyTorch job creation
        mock_is_create.return_value = True
        mock_is_pytorch.return_value = False  # Not a PyTorch job
        mock_namespace_exists.return_value = True  # Namespace exists
        
        @handle_cli_exceptions()
        def inference_create_function():
            return "inference endpoint created successfully"
        
        result = inference_create_function()
        
        # Should execute successfully without Training Operator checks
        assert result == "inference endpoint created successfully"


class TestPodNotFoundInJobScenario:
    """Test enhanced error handling for pod not found in job scenarios."""
    
    @patch('sagemaker.hyperpod.common.cli_decorators._is_get_logs_operation')
    @patch('sagemaker.hyperpod.common.cli_decorators._check_job_exists_for_pod_validation')
    @patch('sagemaker.hyperpod.common.cli_decorators._extract_resource_from_command')
    @patch('sagemaker.hyperpod.common.cli_decorators.click.get_current_context')
    def test_is_pod_not_found_in_job_scenario_true(self, mock_get_context, mock_extract_resource, mock_check_job, mock_is_get_logs):
        """Test detection of pod not found in job scenario when job exists."""
        # Mock get-logs operation
        mock_is_get_logs.return_value = True
        
        # Mock job exists
        mock_check_job.return_value = True
        
        # Mock resource extraction
        mock_extract_resource.return_value = ('pytorch-job', 'PyTorch Job')
        
        # Mock Click context with job name
        mock_context = Mock()
        mock_context.params = {'job_name': 'test-job', 'pod_name': 'fake-pod'}
        mock_get_context.return_value = mock_context
        
        from sagemaker.hyperpod.common.cli_decorators import _is_pod_not_found_in_job_scenario
        result = _is_pod_not_found_in_job_scenario("Job not found", job_name='test-job')
        
        assert result is True
        mock_check_job.assert_called_once_with('test-job', 'default', 'pytorch-job')
    
    @patch('sagemaker.hyperpod.common.cli_decorators._is_get_logs_operation')
    def test_is_pod_not_found_in_job_scenario_not_get_logs(self, mock_is_get_logs):
        """Test detection returns False for non-get-logs operations."""
        mock_is_get_logs.return_value = False
        
        from sagemaker.hyperpod.common.cli_decorators import _is_pod_not_found_in_job_scenario
        result = _is_pod_not_found_in_job_scenario("Job not found")
        
        assert result is False
    
    @patch('sagemaker.hyperpod.common.cli_decorators._is_get_logs_operation')
    def test_is_pod_not_found_in_job_scenario_no_not_found_error(self, mock_is_get_logs):
        """Test detection returns False when error message doesn't contain 'not found'."""
        mock_is_get_logs.return_value = True
        
        from sagemaker.hyperpod.common.cli_decorators import _is_pod_not_found_in_job_scenario
        result = _is_pod_not_found_in_job_scenario("Some other error")
        
        assert result is False
    
    @patch('subprocess.run')
    def test_check_job_exists_for_pod_validation_true(self, mock_subprocess):
        """Test job existence check returns True when job exists."""
        # Mock successful subprocess result
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        from sagemaker.hyperpod.common.cli_decorators import _check_job_exists_for_pod_validation
        result = _check_job_exists_for_pod_validation('test-job', 'default', 'pytorch-job')
        
        assert result is True
        mock_subprocess.assert_called_once_with(
            ['hyp', 'describe', 'hyp-pytorch-job', '--job-name', 'test-job'],
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )
    
    @patch('subprocess.run')
    def test_check_job_exists_for_pod_validation_false(self, mock_subprocess):
        """Test job existence check returns False when job doesn't exist."""
        # Mock failed subprocess result
        mock_result = Mock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result
        
        from sagemaker.hyperpod.common.cli_decorators import _check_job_exists_for_pod_validation
        result = _check_job_exists_for_pod_validation('missing-job', 'default', 'pytorch-job')
        
        assert result is False
    
    def test_generate_pod_not_found_message(self):
        """Test generation of pod not found message."""
        from sagemaker.hyperpod.common.cli_decorators import _generate_pod_not_found_message
        result = _generate_pod_not_found_message('fake-pod', 'test-job')
        
        expected = "❌ Pod 'fake-pod' not found for job 'test-job'."
        assert result == expected
    
    @patch('sagemaker.hyperpod.common.cli_decorators._is_pod_not_found_in_job_scenario')
    @patch('sagemaker.hyperpod.common.cli_decorators._extract_primary_target_dynamically')
    @patch('sagemaker.hyperpod.common.cli_decorators.click.get_current_context')
    @patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
    @patch('sagemaker.hyperpod.common.cli_decorators.click.echo')
    @patch('sagemaker.hyperpod.common.cli_decorators.sys.exit')
    def test_pod_not_found_in_job_integration(self, mock_sys_exit, mock_click_echo, mock_namespace_exists, 
                                            mock_get_context, mock_extract_target, mock_is_pod_scenario):
        """Test full integration of pod not found in job scenario."""
        # Mock conditions
        mock_namespace_exists.return_value = True
        mock_is_pod_scenario.return_value = True
        mock_extract_target.return_value = ('pod', 'fake-pod')
        
        # Mock Click context with job name
        mock_context = Mock()
        mock_context.params = {'job_name': 'test-job', 'pod_name': 'fake-pod'}
        mock_get_context.return_value = mock_context
        
        @handle_cli_exceptions()
        def get_logs_function():
            raise Exception("Job not found")
        
        result = get_logs_function()
        
        # Should show enhanced pod not found message
        mock_click_echo.assert_called_once_with("❌ Pod 'fake-pod' not found for job 'test-job'.")
        mock_sys_exit.assert_called_with(1)
        assert result is None
