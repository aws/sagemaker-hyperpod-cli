"""
Unit tests for utils module - specifically 404 error handling functions.
Tests handle_404 and handle_exception functions with comprehensive scenarios.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from kubernetes.client.exceptions import ApiException
from pydantic import ValidationError

from sagemaker.hyperpod.common.utils import handle_404, handle_exception
from sagemaker.hyperpod.common.error_constants import ResourceType, OperationType


class TestHandle404:
    """Test handle_404 function."""
    
    @patch('sagemaker.hyperpod.common.utils.get_404_message')
    def test_handle_404_with_valid_types(self, mock_get_404):
        """Test handle_404 with valid resource and operation types."""
        mock_get_404.return_value = "Enhanced 404 message"
        
        with pytest.raises(Exception) as exc_info:
            handle_404(
                "missing-job", 
                "production", 
                ResourceType.HYP_PYTORCH_JOB, 
                OperationType.DELETE
            )
        
        assert str(exc_info.value) == "Enhanced 404 message"
        mock_get_404.assert_called_once_with(
            "missing-job", "production", ResourceType.HYP_PYTORCH_JOB, OperationType.DELETE
        )
    
    def test_handle_404_with_none_types(self):
        """Test handle_404 with None resource and operation types."""
        with pytest.raises(Exception) as exc_info:
            handle_404("missing-resource", "test-ns", None, None)
        
        expected_message = (
            "Resource 'missing-resource' not found in namespace 'test-ns'. "
            "Please check the resource name and namespace."
        )
        assert str(exc_info.value) == expected_message
    
    def test_handle_404_with_partial_none_types(self):
        """Test handle_404 with one None type."""
        with pytest.raises(Exception) as exc_info:
            handle_404("test", "default", ResourceType.HYP_PYTORCH_JOB, None)
        
        expected_message = (
            "Resource 'test' not found in namespace 'default'. "
            "Please check the resource name and namespace."
        )
        assert str(exc_info.value) == expected_message
    
    @patch('sagemaker.hyperpod.common.utils.get_404_message')
    def test_handle_404_all_resource_types(self, mock_get_404):
        """Test handle_404 with all resource types."""
        test_cases = [
            ResourceType.HYP_PYTORCH_JOB,
            ResourceType.HYP_CUSTOM_ENDPOINT,
            ResourceType.HYP_JUMPSTART_ENDPOINT
        ]
        
        mock_get_404.return_value = "Test message"
        
        for resource_type in test_cases:
            with pytest.raises(Exception):
                handle_404("test", "default", resource_type, OperationType.DELETE)
            
            mock_get_404.assert_called_with(
                "test", "default", resource_type, OperationType.DELETE
            )
    
    @patch('sagemaker.hyperpod.common.utils.get_404_message')
    def test_handle_404_all_operation_types(self, mock_get_404):
        """Test handle_404 with all operation types."""
        test_cases = [
            OperationType.DELETE,
            OperationType.GET,
            OperationType.DESCRIBE,
            OperationType.LIST
        ]
        
        mock_get_404.return_value = "Test message"
        
        for operation_type in test_cases:
            with pytest.raises(Exception):
                handle_404("test", "default", ResourceType.HYP_PYTORCH_JOB, operation_type)
            
            mock_get_404.assert_called_with(
                "test", "default", ResourceType.HYP_PYTORCH_JOB, operation_type
            )


class TestHandleException:
    """Test handle_exception function."""
    
    def test_handle_exception_401_unauthorized(self):
        """Test handle_exception for 401 Unauthorized."""
        api_exception = ApiException(status=401, reason="Unauthorized")
        
        with pytest.raises(Exception) as exc_info:
            handle_exception(api_exception, "test-resource", "test-ns")
        
        assert "Credentials unauthorized" in str(exc_info.value)
    
    def test_handle_exception_403_forbidden(self):
        """Test handle_exception for 403 Forbidden."""
        api_exception = ApiException(status=403, reason="Forbidden")
        
        with pytest.raises(Exception) as exc_info:
            handle_exception(api_exception, "test-resource", "test-ns")
        
        expected_message = "Access denied to resource 'test-resource' in namespace 'test-ns'."
        assert expected_message in str(exc_info.value)
    
    @patch('sagemaker.hyperpod.common.utils.handle_404')
    def test_handle_exception_404_with_valid_types(self, mock_handle_404):
        """Test handle_exception for 404 with valid resource/operation types."""
        api_exception = ApiException(status=404, reason="Not Found")
        mock_handle_404.side_effect = Exception("Enhanced 404 message")
        
        with pytest.raises(Exception) as exc_info:
            handle_exception(
                api_exception, "missing-job", "production", 
                "delete", "training_job"
            )
        
        assert str(exc_info.value) == "Enhanced 404 message"
        mock_handle_404.assert_called_once_with(
            "missing-job", "production", ResourceType.HYP_PYTORCH_JOB, OperationType.DELETE
        )
    
    @patch('sagemaker.hyperpod.common.utils.handle_404')
    def test_handle_exception_404_with_legacy_inference_endpoint(self, mock_handle_404):
        """Test handle_exception for 404 with legacy inference_endpoint type."""
        api_exception = ApiException(status=404, reason="Not Found")
        mock_handle_404.side_effect = Exception("Enhanced 404 message")
        
        with pytest.raises(Exception) as exc_info:
            handle_exception(
                api_exception, "missing-endpoint", "default", 
                "describe", "inference_endpoint"
            )
        
        assert str(exc_info.value) == "Enhanced 404 message"
        # Should default to custom endpoint for legacy inference_endpoint
        mock_handle_404.assert_called_once_with(
            "missing-endpoint", "default", ResourceType.HYP_CUSTOM_ENDPOINT, OperationType.DESCRIBE
        )
    
    @patch('sagemaker.hyperpod.common.utils.handle_404')
    def test_handle_exception_404_resource_type_mapping(self, mock_handle_404):
        """Test handle_exception 404 resource type mapping."""
        api_exception = ApiException(status=404, reason="Not Found")
        mock_handle_404.side_effect = Exception("Test message")
        
        # Test all mappings
        test_cases = [
            ("training_job", ResourceType.HYP_PYTORCH_JOB),
            ("hyp_pytorch_job", ResourceType.HYP_PYTORCH_JOB),
            ("inference_endpoint", ResourceType.HYP_CUSTOM_ENDPOINT),
            ("hyp_custom_endpoint", ResourceType.HYP_CUSTOM_ENDPOINT),
            ("hyp_jumpstart_endpoint", ResourceType.HYP_JUMPSTART_ENDPOINT),
        ]
        
        for resource_string, expected_enum in test_cases:
            mock_handle_404.reset_mock()
            
            with pytest.raises(Exception):
                handle_exception(
                    api_exception, "test", "default", 
                    "delete", resource_string
                )
            
            mock_handle_404.assert_called_once_with(
                "test", "default", expected_enum, OperationType.DELETE
            )
    
    @patch('sagemaker.hyperpod.common.utils.handle_404')
    def test_handle_exception_404_operation_type_mapping(self, mock_handle_404):
        """Test handle_exception 404 operation type mapping."""
        api_exception = ApiException(status=404, reason="Not Found")
        mock_handle_404.side_effect = Exception("Test message")
        
        # Test all operation mappings
        test_cases = [
            ("delete", OperationType.DELETE),
            ("get", OperationType.GET),
            ("describe", OperationType.DESCRIBE),
            ("list", OperationType.LIST),
        ]
        
        for operation_string, expected_enum in test_cases:
            mock_handle_404.reset_mock()
            
            with pytest.raises(Exception):
                handle_exception(
                    api_exception, "test", "default", 
                    operation_string, "training_job"
                )
            
            mock_handle_404.assert_called_once_with(
                "test", "default", ResourceType.HYP_PYTORCH_JOB, expected_enum
            )
    
    @patch('sagemaker.hyperpod.common.utils.handle_404')
    def test_handle_exception_404_unknown_types_fallback(self, mock_handle_404):
        """Test handle_exception 404 with unknown types uses fallback."""
        api_exception = ApiException(status=404, reason="Not Found")
        
        with pytest.raises(Exception):
            handle_exception(
                api_exception, "test", "default", 
                "unknown", "unknown"
            )
        
        # Should call handle_404 with None types for fallback
        mock_handle_404.assert_called_once_with("test", "default", None, None)
    
    @patch('sagemaker.hyperpod.common.utils.handle_404')
    def test_handle_exception_404_invalid_enum_values(self, mock_handle_404):
        """Test handle_exception 404 with invalid enum values."""
        api_exception = ApiException(status=404, reason="Not Found")
        
        with pytest.raises(Exception):
            handle_exception(
                api_exception, "test", "default", 
                "invalid_operation", "training_job"
            )
        
        # Should call handle_404 with None for invalid operation
        mock_handle_404.assert_called_once_with(
            "test", "default", ResourceType.HYP_PYTORCH_JOB, None
        )
    
    def test_handle_exception_409_conflict(self):
        """Test handle_exception for 409 Conflict."""
        api_exception = ApiException(status=409, reason="Conflict")
        
        with pytest.raises(Exception) as exc_info:
            handle_exception(api_exception, "existing-resource", "test-ns")
        
        expected_message = "Resource 'existing-resource' already exists in namespace 'test-ns'."
        assert expected_message in str(exc_info.value)
    
    def test_handle_exception_500_server_error(self):
        """Test handle_exception for 500 Internal Server Error."""
        api_exception = ApiException(status=500, reason="Internal Server Error")
        
        with pytest.raises(Exception) as exc_info:
            handle_exception(api_exception, "test-resource", "test-ns")
        
        assert "Kubernetes API internal server error" in str(exc_info.value)
    
    def test_handle_exception_503_service_unavailable(self):
        """Test handle_exception for 503 Service Unavailable."""
        api_exception = ApiException(status=503, reason="Service Unavailable")
        
        with pytest.raises(Exception) as exc_info:
            handle_exception(api_exception, "test-resource", "test-ns")
        
        assert "Kubernetes API internal server error" in str(exc_info.value)
    
    def test_handle_exception_unknown_api_error(self):
        """Test handle_exception for unknown API error."""
        api_exception = ApiException(status=418, reason="I'm a teapot")
        
        with pytest.raises(Exception) as exc_info:
            handle_exception(api_exception, "test-resource", "test-ns")
        
        expected_message = "Unhandled Kubernetes error: 418 I'm a teapot"
        assert expected_message in str(exc_info.value)
    
    def test_handle_exception_generic_exception_passthrough(self):
        """Test handle_exception passes through non-API/ValidationError exceptions."""
        generic_error = ValueError("Generic error")
        
        with pytest.raises(ValueError) as exc_info:
            handle_exception(generic_error, "test-resource", "test-ns")
        
        assert str(exc_info.value) == "Generic error"
    
    def test_handle_exception_default_parameters(self):
        """Test handle_exception with default parameters."""
        api_exception = ApiException(status=401, reason="Unauthorized")
        
        with pytest.raises(Exception) as exc_info:
            handle_exception(api_exception, "test-resource", "test-ns")
        
        # Should work with defaults (operation_type='unknown', resource_type='unknown')
        assert "Credentials unauthorized" in str(exc_info.value)


class TestIntegrationScenarios:
    """Integration tests for complete 404 handling scenarios."""
    
    @patch('sagemaker.hyperpod.common.utils.get_404_message')
    def test_complete_pytorch_job_delete_scenario(self, mock_get_404):
        """Test complete scenario: PyTorch job delete with 404."""
        api_exception = ApiException(status=404, reason="Not Found")
        mock_get_404.return_value = "❓ Job 'missing-job' not found in namespace 'production'. There are 2 resources in this namespace. Use 'hyp list hyp-pytorch-job --namespace production' to see available resources."
        
        with pytest.raises(Exception) as exc_info:
            handle_exception(
                api_exception, "missing-job", "production", 
                "delete", "training_job"
            )
        
        expected_message = "❓ Job 'missing-job' not found in namespace 'production'. There are 2 resources in this namespace. Use 'hyp list hyp-pytorch-job --namespace production' to see available resources."
        assert str(exc_info.value) == expected_message
        mock_get_404.assert_called_once_with(
            "missing-job", "production", ResourceType.HYP_PYTORCH_JOB, OperationType.DELETE
        )
    
    @patch('sagemaker.hyperpod.common.utils.get_404_message')
    def test_complete_jumpstart_endpoint_describe_scenario(self, mock_get_404):
        """Test complete scenario: JumpStart endpoint describe with 404."""
        api_exception = ApiException(status=404, reason="Not Found")
        mock_get_404.return_value = "❓ JumpStart endpoint 'missing-endpoint' not found in namespace 'default'. No resources of this type exist in the namespace. Use 'hyp list hyp-jumpstart-endpoint' to check for available resources."
        
        with pytest.raises(Exception) as exc_info:
            handle_exception(
                api_exception, "missing-endpoint", "default", 
                "describe", "hyp_jumpstart_endpoint"
            )
        
        expected_message = "❓ JumpStart endpoint 'missing-endpoint' not found in namespace 'default'. No resources of this type exist in the namespace. Use 'hyp list hyp-jumpstart-endpoint' to check for available resources."
        assert str(exc_info.value) == expected_message
        mock_get_404.assert_called_once_with(
            "missing-endpoint", "default", ResourceType.HYP_JUMPSTART_ENDPOINT, OperationType.DESCRIBE
        )
    
    def test_complete_non_404_error_scenario(self):
        """Test complete scenario: non-404 error handling."""
        api_exception = ApiException(status=403, reason="Forbidden")
        
        with pytest.raises(Exception) as exc_info:
            handle_exception(
                api_exception, "restricted-resource", "secure-ns", 
                "delete", "training_job"
            )
        
        expected_message = "Access denied to resource 'restricted-resource' in namespace 'secure-ns'."
        assert expected_message in str(exc_info.value)
    
    @patch('sagemaker.hyperpod.common.utils.get_404_message')
    def test_complete_fallback_scenario(self, mock_get_404):
        """Test complete scenario: 404 with fallback due to unknown types."""
        api_exception = ApiException(status=404, reason="Not Found")
        # Don't mock get_404_message so handle_404 uses fallback
        
        with pytest.raises(Exception) as exc_info:
            handle_exception(
                api_exception, "unknown-resource", "test-ns", 
                "unknown", "unknown"
            )
        
        expected_message = (
            "Resource 'unknown-resource' not found in namespace 'test-ns'. "
            "Please check the resource name and namespace."
        )
        assert str(exc_info.value) == expected_message
