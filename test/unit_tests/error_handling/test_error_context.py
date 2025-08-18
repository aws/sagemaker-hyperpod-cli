"""
Unit tests for error_context module.
Tests ErrorContext dataclass and ContextGatherer functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import TimeoutError as FutureTimeoutError

from sagemaker.hyperpod.common.exceptions.error_context import (
    ErrorContext,
    ContextGatherer
)
from sagemaker.hyperpod.common.exceptions.error_constants import ResourceType, OperationType


class TestErrorContext:
    """Test ErrorContext dataclass."""
    
    def test_error_context_creation(self):
        """Test ErrorContext can be created with required fields."""
        context = ErrorContext(
            resource_name="test-resource",
            namespace="test-namespace",
            resource_type=ResourceType.HYP_PYTORCH_JOB
        )
        
        assert context.resource_name == "test-resource"
        assert context.namespace == "test-namespace"
        assert context.resource_type == ResourceType.HYP_PYTORCH_JOB
        assert context.operation_type == OperationType.DELETE  # Default
        assert context.available_count == 0  # Default
    
    def test_error_context_with_all_fields(self):
        """Test ErrorContext with all fields specified."""
        context = ErrorContext(
            resource_name="test-job",
            namespace="production",
            resource_type=ResourceType.HYP_JUMPSTART_ENDPOINT,
            operation_type=OperationType.DESCRIBE,
            available_count=5
        )
        
        assert context.resource_name == "test-job"
        assert context.namespace == "production"
        assert context.resource_type == ResourceType.HYP_JUMPSTART_ENDPOINT
        assert context.operation_type == OperationType.DESCRIBE
        assert context.available_count == 5
    
    def test_error_context_enum_types(self):
        """Test ErrorContext enforces enum types."""
        context = ErrorContext(
            resource_name="test",
            namespace="default",
            resource_type=ResourceType.HYP_CUSTOM_ENDPOINT,
            operation_type=OperationType.LIST
        )
        
        assert isinstance(context.resource_type, ResourceType)
        assert isinstance(context.operation_type, OperationType)


class TestContextGatherer:
    """Test ContextGatherer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.gatherer = ContextGatherer(timeout_seconds=1.0)
    
    def test_context_gatherer_initialization(self):
        """Test ContextGatherer initializes with correct timeout."""
        gatherer = ContextGatherer(timeout_seconds=5.0)
        assert gatherer.timeout_seconds == 5.0
        
        # Test default timeout
        default_gatherer = ContextGatherer()
        assert default_gatherer.timeout_seconds == 30.0
    
    def test_gather_context_creates_correct_context(self):
        """Test gather_context creates ErrorContext with correct fields."""
        with patch.object(self.gatherer, '_gather_resource_count') as mock_gather:
            context = self.gatherer.gather_context(
                resource_name="test-resource",
                namespace="test-ns",
                resource_type=ResourceType.HYP_PYTORCH_JOB,
                operation_type=OperationType.DELETE
            )
            
            assert isinstance(context, ErrorContext)
            assert context.resource_name == "test-resource"
            assert context.namespace == "test-ns"
            assert context.resource_type == ResourceType.HYP_PYTORCH_JOB
            assert context.operation_type == OperationType.DELETE
            mock_gather.assert_called_once_with(context)
    
    def test_gather_context_default_operation_type(self):
        """Test gather_context uses default operation type."""
        with patch.object(self.gatherer, '_gather_resource_count'):
            context = self.gatherer.gather_context(
                resource_name="test",
                namespace="default",
                resource_type=ResourceType.HYP_CUSTOM_ENDPOINT
            )
            
            assert context.operation_type == OperationType.DELETE  # Default
    
    @patch('sagemaker.hyperpod.common.exceptions.error_context.ThreadPoolExecutor')
    def test_gather_context_timeout_handling(self, mock_executor):
        """Test gather_context handles timeout gracefully."""
        # Mock ThreadPoolExecutor to raise timeout
        mock_future = Mock()
        mock_future.result.side_effect = FutureTimeoutError()
        mock_executor_instance = Mock()
        mock_executor_instance.submit.return_value = mock_future
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        
        context = self.gatherer.gather_context(
            "test", "default", ResourceType.HYP_PYTORCH_JOB
        )
        
        # Should complete without raising exception
        assert isinstance(context, ErrorContext)
        assert context.available_count == 0  # No count due to timeout
    
    @patch('sagemaker.hyperpod.common.exceptions.error_context.ThreadPoolExecutor')
    def test_gather_context_exception_handling(self, mock_executor):
        """Test gather_context handles exceptions gracefully."""
        # Mock ThreadPoolExecutor to raise exception
        mock_executor.return_value.__enter__.side_effect = Exception("Test error")
        
        context = self.gatherer.gather_context(
            "test", "default", ResourceType.HYP_PYTORCH_JOB
        )
        
        # Should complete without raising exception
        assert isinstance(context, ErrorContext)
        assert context.available_count == 0  # No count due to exception
    
    def test_gather_resource_count_success(self):
        """Test _gather_resource_count updates context correctly."""
        with patch.object(self.gatherer, '_get_available_resource_names') as mock_get:
            mock_get.return_value = ["job1", "job2", "job3"]
            
            context = ErrorContext(
                resource_name="test",
                namespace="default",
                resource_type=ResourceType.HYP_PYTORCH_JOB
            )
            
            self.gatherer._gather_resource_count(context)
            
            assert context.available_count == 3
            mock_get.assert_called_once_with("default", ResourceType.HYP_PYTORCH_JOB)
    
    def test_gather_resource_count_exception(self):
        """Test _gather_resource_count handles exceptions."""
        with patch.object(self.gatherer, '_get_available_resource_names') as mock_get:
            mock_get.side_effect = Exception("API Error")
            
            context = ErrorContext(
                resource_name="test",
                namespace="default", 
                resource_type=ResourceType.HYP_PYTORCH_JOB
            )
            
            # Should not raise exception
            self.gatherer._gather_resource_count(context)
            assert context.available_count == 0  # Default value preserved
    
    @patch('sagemaker.hyperpod.training.hyperpod_pytorch_job.HyperPodPytorchJob')
    def test_get_available_resource_names_pytorch_job(self, mock_job_class):
        """Test _get_available_resource_names for PyTorch jobs."""
        # Mock job instances
        mock_job1 = Mock()
        mock_job1.metadata.name = "job1"
        mock_job2 = Mock()
        mock_job2.metadata.name = "job2"
        
        mock_job_class.list.return_value = [mock_job1, mock_job2]
        
        names = self.gatherer._get_available_resource_names(
            "default", ResourceType.HYP_PYTORCH_JOB
        )
        
        assert names == ["job1", "job2"]
        mock_job_class.list.assert_called_once_with(namespace="default")
    
    @patch('sagemaker.hyperpod.inference.hp_jumpstart_endpoint.HPJumpStartEndpoint')
    def test_get_available_resource_names_jumpstart_endpoint(self, mock_endpoint_class):
        """Test _get_available_resource_names for JumpStart endpoints."""
        # Mock endpoint instances
        mock_ep1 = Mock()
        mock_ep1.metadata.name = "endpoint1"
        mock_ep2 = Mock()
        mock_ep2.metadata.name = "endpoint2"
        
        mock_endpoint_class.list.return_value = [mock_ep1, mock_ep2]
        
        names = self.gatherer._get_available_resource_names(
            "test-ns", ResourceType.HYP_JUMPSTART_ENDPOINT
        )
        
        assert names == ["endpoint1", "endpoint2"]
        mock_endpoint_class.list.assert_called_once_with(namespace="test-ns")
    
    @patch('sagemaker.hyperpod.inference.hp_endpoint.HPEndpoint')
    def test_get_available_resource_names_custom_endpoint(self, mock_endpoint_class):
        """Test _get_available_resource_names for custom endpoints."""
        # Mock endpoint instances
        mock_ep1 = Mock()
        mock_ep1.metadata.name = "custom1"
        
        mock_endpoint_class.list.return_value = [mock_ep1]
        
        names = self.gatherer._get_available_resource_names(
            "production", ResourceType.HYP_CUSTOM_ENDPOINT
        )
        
        assert names == ["custom1"]
        mock_endpoint_class.list.assert_called_once_with(namespace="production")
    
    @patch('sagemaker.hyperpod.inference.hp_jumpstart_endpoint.HPJumpStartEndpoint')
    def test_get_available_resource_names_jumpstart_exception(self, mock_endpoint_class):
        """Test _get_available_resource_names handles JumpStart exceptions."""
        mock_endpoint_class.list.side_effect = Exception("API Error")
        
        names = self.gatherer._get_available_resource_names(
            "default", ResourceType.HYP_JUMPSTART_ENDPOINT
        )
        
        assert names == []  # Returns empty list on exception
    
    @patch('sagemaker.hyperpod.inference.hp_endpoint.HPEndpoint')
    def test_get_available_resource_names_custom_exception(self, mock_endpoint_class):
        """Test _get_available_resource_names handles custom endpoint exceptions."""
        mock_endpoint_class.list.side_effect = Exception("Network Error")
        
        names = self.gatherer._get_available_resource_names(
            "default", ResourceType.HYP_CUSTOM_ENDPOINT
        )
        
        assert names == []  # Returns empty list on exception
    
    def test_get_available_resource_names_unknown_type(self):
        """Test _get_available_resource_names returns empty for unknown types."""
        # This would only happen if new ResourceType is added but not handled
        names = self.gatherer._get_available_resource_names("default", None)
        assert names == []
    
    @patch('sagemaker.hyperpod.training.hyperpod_pytorch_job.HyperPodPytorchJob')
    def test_integration_gather_context_with_real_data(self, mock_job_class):
        """Test full integration of gather_context with mocked data."""
        # Mock job instances
        mock_job1 = Mock()
        mock_job1.metadata.name = "training-job-1"
        mock_job2 = Mock()
        mock_job2.metadata.name = "training-job-2"
        mock_job3 = Mock()
        mock_job3.metadata.name = "training-job-3"
        
        mock_job_class.list.return_value = [mock_job1, mock_job2, mock_job3]
        
        context = self.gatherer.gather_context(
            resource_name="missing-job",
            namespace="production",
            resource_type=ResourceType.HYP_PYTORCH_JOB,
            operation_type=OperationType.DELETE
        )
        
        assert context.resource_name == "missing-job"
        assert context.namespace == "production"
        assert context.resource_type == ResourceType.HYP_PYTORCH_JOB
        assert context.operation_type == OperationType.DELETE
        assert context.available_count == 3
        mock_job_class.list.assert_called_once_with(namespace="production")
