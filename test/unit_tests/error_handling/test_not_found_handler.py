"""
Unit tests for not_found_handler module.
Tests NotFoundMessageGenerator, NotFoundHandler, and convenience functions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from sagemaker.hyperpod.common.not_found_handler import (
    NotFoundMessageGenerator,
    NotFoundHandler,
    get_404_message
)
from sagemaker.hyperpod.common.error_context import ErrorContext
from sagemaker.hyperpod.common.error_constants import ResourceType, OperationType


class TestNotFoundMessageGenerator:
    """Test NotFoundMessageGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = NotFoundMessageGenerator()
    
    def test_message_generator_initialization(self):
        """Test NotFoundMessageGenerator initializes correctly."""
        generator = NotFoundMessageGenerator()
        assert generator is not None
    
    def test_generate_message_empty_namespace(self):
        """Test generate_message for empty namespace (no resources)."""
        context = ErrorContext(
            resource_name="missing-job",
            namespace="empty-ns",
            resource_type=ResourceType.HYP_PYTORCH_JOB,
            operation_type=OperationType.DELETE,
            available_count=0
        )
        
        message = self.generator.generate_message(context)
        
        expected_parts = [
            "❓ Job 'missing-job' not found in namespace 'empty-ns'",
            "No resources of this type exist in the namespace",
            "Use 'hyp list hyp-pytorch-job' to check for available resources"
        ]
        
        for part in expected_parts:
            assert part in message
    
    def test_generate_message_generic_helpful(self):
        """Test generate_message for generic case with resources available."""
        context = ErrorContext(
            resource_name="missing-endpoint",
            namespace="production",
            resource_type=ResourceType.HYP_JUMPSTART_ENDPOINT,
            operation_type=OperationType.DESCRIBE,
            available_count=5
        )
        
        message = self.generator.generate_message(context)
        
        expected_parts = [
            "❓ JumpStart endpoint 'missing-endpoint' not found in namespace 'production'",
            "Please check the resource name",
            "There are 5 resources in this namespace",
            "Use 'hyp list hyp-jumpstart-endpoint --namespace production' to see available resources"
        ]
        
        for part in expected_parts:
            assert part in message
    
    def test_generate_message_default_namespace(self):
        """Test generate_message doesn't show --namespace flag for default namespace."""
        context = ErrorContext(
            resource_name="missing-custom",
            namespace="default",
            resource_type=ResourceType.HYP_CUSTOM_ENDPOINT,
            operation_type=OperationType.GET,
            available_count=2
        )
        
        message = self.generator.generate_message(context)
        
        # Should not include --namespace flag for default namespace
        assert "--namespace default" not in message
        assert "Use 'hyp list hyp-custom-endpoint' to see available resources" in message
    
    def test_generate_empty_namespace_message(self):
        """Test _generate_empty_namespace_message directly."""
        context = ErrorContext(
            resource_name="test-resource",
            namespace="test-ns",
            resource_type=ResourceType.HYP_PYTORCH_JOB,
            operation_type=OperationType.DELETE
        )
        
        message = self.generator._generate_empty_namespace_message(context)
        
        assert "❓ Job 'test-resource' not found in namespace 'test-ns'" in message
        assert "No resources of this type exist in the namespace" in message
        assert "Use 'hyp list hyp-pytorch-job' to check for available resources" in message
    
    def test_generate_generic_helpful_message(self):
        """Test _generate_generic_helpful_message directly."""
        context = ErrorContext(
            resource_name="test-endpoint",
            namespace="staging",
            resource_type=ResourceType.HYP_JUMPSTART_ENDPOINT,
            operation_type=OperationType.DELETE,
            available_count=3
        )
        
        message = self.generator._generate_generic_helpful_message(context)
        
        assert "❓ JumpStart endpoint 'test-endpoint' not found in namespace 'staging'" in message
        assert "There are 3 resources in this namespace" in message
        assert "Use 'hyp list hyp-jumpstart-endpoint --namespace staging'" in message
    
    def test_get_resource_display_name(self):
        """Test _get_resource_display_name returns correct display names."""
        assert self.generator._get_resource_display_name(ResourceType.HYP_PYTORCH_JOB) == "Job"
        assert self.generator._get_resource_display_name(ResourceType.HYP_CUSTOM_ENDPOINT) == "Custom endpoint"
        assert self.generator._get_resource_display_name(ResourceType.HYP_JUMPSTART_ENDPOINT) == "JumpStart endpoint"
    
    def test_get_list_command(self):
        """Test _get_list_command returns correct commands."""
        assert self.generator._get_list_command(ResourceType.HYP_PYTORCH_JOB) == "hyp list hyp-pytorch-job"
        assert self.generator._get_list_command(ResourceType.HYP_CUSTOM_ENDPOINT) == "hyp list hyp-custom-endpoint"
        assert self.generator._get_list_command(ResourceType.HYP_JUMPSTART_ENDPOINT) == "hyp list hyp-jumpstart-endpoint"


class TestNotFoundHandler:
    """Test NotFoundHandler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = NotFoundHandler(enable_context_gathering=True, timeout_seconds=1.0)
    
    def test_handler_initialization(self):
        """Test NotFoundHandler initializes correctly."""
        handler = NotFoundHandler(enable_context_gathering=False, timeout_seconds=5.0)
        assert handler.enable_context_gathering is False
        assert handler.context_gatherer.timeout_seconds == 5.0
        assert handler.message_generator is not None
    
    def test_handler_default_initialization(self):
        """Test NotFoundHandler default initialization."""
        handler = NotFoundHandler()
        assert handler.enable_context_gathering is True
        assert handler.context_gatherer.timeout_seconds == 2.0  # Default
        assert handler.message_generator is not None
    
    def test_generate_404_message_with_context(self):
        """Test generate_404_message with context gathering enabled."""
        # Mock the handler's context gatherer directly
        mock_context = ErrorContext(
            resource_name="test-job",
            namespace="default",
            resource_type=ResourceType.HYP_PYTORCH_JOB,
            operation_type=OperationType.DELETE,
            available_count=2
        )
        
        # Mock both the context gatherer and message generator
        with patch.object(self.handler, 'context_gatherer') as mock_gatherer, \
             patch.object(self.handler, 'message_generator') as mock_msg_gen:
            
            mock_gatherer.gather_context.return_value = mock_context
            mock_msg_gen.generate_message.return_value = "Test 404 message"
            
            result = self.handler.generate_404_message(
                "test-job", "default", ResourceType.HYP_PYTORCH_JOB, OperationType.DELETE
            )
            
            assert result == "Test 404 message"
            mock_gatherer.gather_context.assert_called_once_with(
                "test-job", "default", ResourceType.HYP_PYTORCH_JOB, OperationType.DELETE
            )
            mock_msg_gen.generate_message.assert_called_once_with(mock_context)
    
    def test_generate_404_message_context_disabled(self):
        """Test generate_404_message with context gathering disabled."""
        handler = NotFoundHandler(enable_context_gathering=False)
        
        result = handler.generate_404_message(
            "test-resource", "test-ns", ResourceType.HYP_CUSTOM_ENDPOINT, OperationType.DESCRIBE
        )
        
        expected_parts = [
            "Custom endpoint 'test-resource' not found in namespace 'test-ns'",
            "Please check the resource name and namespace"
        ]
        
        for part in expected_parts:
            assert part in result
    
    @patch('sagemaker.hyperpod.common.not_found_handler.ContextGatherer')
    def test_generate_404_message_exception_fallback(self, mock_gatherer_class):
        """Test generate_404_message falls back on exception."""
        # Mock context gatherer to raise exception
        mock_gatherer = Mock()
        mock_gatherer.gather_context.side_effect = Exception("API Error")
        mock_gatherer_class.return_value = mock_gatherer
        
        handler = NotFoundHandler(enable_context_gathering=True)
        
        result = handler.generate_404_message(
            "failing-resource", "default", ResourceType.HYP_JUMPSTART_ENDPOINT, OperationType.DELETE
        )
        
        # Should use fallback message
        expected_parts = [
            "JumpStart endpoint 'failing-resource' not found in namespace 'default'",
            "Please check the resource name and namespace"
        ]
        
        for part in expected_parts:
            assert part in result
    
    def test_generate_fallback_message(self):
        """Test _generate_fallback_message directly."""
        result = self.handler._generate_fallback_message(
            "test-resource", "production", ResourceType.HYP_PYTORCH_JOB
        )
        
        assert "Job 'test-resource' not found in namespace 'production'" in result
        assert "Please check the resource name and namespace" in result
    
    def test_generate_fallback_message_all_resource_types(self):
        """Test _generate_fallback_message for all resource types."""
        test_cases = [
            (ResourceType.HYP_PYTORCH_JOB, "Job"),
            (ResourceType.HYP_CUSTOM_ENDPOINT, "Custom endpoint"),
            (ResourceType.HYP_JUMPSTART_ENDPOINT, "JumpStart endpoint")
        ]
        
        for resource_type, expected_display in test_cases:
            result = self.handler._generate_fallback_message(
                "test", "default", resource_type
            )
            assert f"{expected_display} 'test' not found" in result


class TestConvenienceFunction:
    """Test get_404_message convenience function."""
    
    @patch('sagemaker.hyperpod.common.not_found_handler._handler')
    def test_get_404_message_calls_handler(self, mock_handler):
        """Test get_404_message calls the global handler."""
        mock_handler.generate_404_message.return_value = "Test message"
        
        result = get_404_message(
            "test-resource", "test-ns", ResourceType.HYP_PYTORCH_JOB, OperationType.DELETE
        )
        
        assert result == "Test message"
        mock_handler.generate_404_message.assert_called_once_with(
            "test-resource", "test-ns", ResourceType.HYP_PYTORCH_JOB, OperationType.DELETE
        )
    
    @patch('sagemaker.hyperpod.common.not_found_handler._handler')
    def test_get_404_message_default_operation(self, mock_handler):
        """Test get_404_message with default operation type."""
        mock_handler.generate_404_message.return_value = "Test message"
        
        result = get_404_message("test", "default", ResourceType.HYP_CUSTOM_ENDPOINT)
        
        mock_handler.generate_404_message.assert_called_once_with(
            "test", "default", ResourceType.HYP_CUSTOM_ENDPOINT, OperationType.DELETE
        )


class TestIntegration:
    """Integration tests for the complete 404 handling flow."""
    
    @patch('sagemaker.hyperpod.training.hyperpod_pytorch_job.HyperPodPytorchJob')
    def test_end_to_end_pytorch_job_404(self, mock_job_class):
        """Test complete 404 handling flow for PyTorch job."""
        # Mock available jobs
        mock_job1 = Mock()
        mock_job1.metadata.name = "existing-job-1"
        mock_job2 = Mock()
        mock_job2.metadata.name = "existing-job-2"
        
        mock_job_class.list.return_value = [mock_job1, mock_job2]
        
        # Test the complete flow
        result = get_404_message(
            "missing-job", "production", ResourceType.HYP_PYTORCH_JOB, OperationType.DELETE
        )
        
        expected_parts = [
            "❓ Job 'missing-job' not found in namespace 'production'",
            "There are 2 resources in this namespace",
            "Use 'hyp list hyp-pytorch-job --namespace production'"
        ]
        
        for part in expected_parts:
            assert part in result
    
    @patch('sagemaker.hyperpod.inference.hp_jumpstart_endpoint.HPJumpStartEndpoint')
    def test_end_to_end_jumpstart_endpoint_404_empty(self, mock_endpoint_class):
        """Test complete 404 handling flow for JumpStart endpoint with empty namespace."""
        # Mock no available endpoints
        mock_endpoint_class.list.return_value = []
        
        result = get_404_message(
            "missing-endpoint", "default", ResourceType.HYP_JUMPSTART_ENDPOINT, OperationType.DESCRIBE
        )
        
        expected_parts = [
            "❓ JumpStart endpoint 'missing-endpoint' not found in namespace 'default'",
            "No resources of this type exist in the namespace",
            "Use 'hyp list hyp-jumpstart-endpoint' to check for available resources"
        ]
        
        for part in expected_parts:
            assert part in result
    
    @patch('sagemaker.hyperpod.inference.hp_endpoint.HPEndpoint')
    def test_end_to_end_custom_endpoint_404_with_exception(self, mock_endpoint_class):
        """Test complete 404 handling flow with API exception."""
        # Mock endpoint listing to raise exception
        mock_endpoint_class.list.side_effect = Exception("Kubernetes API error")
        
        result = get_404_message(
            "failing-endpoint", "staging", ResourceType.HYP_CUSTOM_ENDPOINT, OperationType.DELETE
        )
        
        # Should still provide helpful message with fallback behavior
        expected_parts = [
            "❓ Custom endpoint 'failing-endpoint' not found in namespace 'staging'"
        ]
        
        for part in expected_parts:
            assert part in result
