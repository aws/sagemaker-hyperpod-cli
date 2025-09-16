"""
Unit tests for Kubernetes authentication error handling in cli_decorators.py
Tests all authentication scenarios and error message generation.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock, Mock
from kubernetes.client.exceptions import ApiException
from kubernetes.config.config_exception import ConfigException

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from sagemaker.hyperpod.common.cli_decorators import (
    _check_kubernetes_connectivity,
    _generate_kubernetes_auth_error_message,
    _is_kubernetes_operation,
    _check_aws_credentials,
    _get_current_kubernetes_context,
    handle_cli_exceptions
)


class TestKubernetesConnectivityCheck:
    """Test the _check_kubernetes_connectivity function"""
    
    @patch('sagemaker.hyperpod.common.cli_decorators.config.load_kube_config')
    @patch('kubernetes.client.VersionApi')
    def test_successful_connection(self, mock_version_api, mock_load_config):
        """Test successful Kubernetes connection"""
        mock_version_instance = Mock()
        mock_version_api.return_value = mock_version_instance
        mock_version_instance.get_code.return_value = {"major": "1", "minor": "28"}
        
        is_connected, error_type = _check_kubernetes_connectivity()
        
        assert is_connected is True
        assert error_type == ""
        mock_load_config.assert_called_once()
        mock_version_instance.get_code.assert_called_once()
    
    @patch('sagemaker.hyperpod.common.cli_decorators.config.load_kube_config')
    def test_no_config_found(self, mock_load_config):
        """Test ConfigException with no configuration found"""
        mock_load_config.side_effect = ConfigException("No configuration found")
        
        is_connected, error_type = _check_kubernetes_connectivity()
        
        assert is_connected is False
        assert error_type == "no_config"
    
    @patch('sagemaker.hyperpod.common.cli_decorators.config.load_kube_config')
    def test_invalid_config(self, mock_load_config):
        """Test ConfigException with invalid kube-config"""
        mock_load_config.side_effect = ConfigException("Invalid kube-config file")
        
        is_connected, error_type = _check_kubernetes_connectivity()
        
        assert is_connected is False
        assert error_type == "invalid_config"
    
    @patch('sagemaker.hyperpod.common.cli_decorators.config.load_kube_config')
    @patch('kubernetes.client.VersionApi')
    def test_401_unauthorized(self, mock_version_api, mock_load_config):
        """Test 401 Unauthorized ApiException"""
        mock_version_instance = Mock()
        mock_version_api.return_value = mock_version_instance
        mock_version_instance.get_code.side_effect = ApiException(status=401, reason="Unauthorized")
        
        is_connected, error_type = _check_kubernetes_connectivity()
        
        assert is_connected is False
        assert error_type == "unauthorized"
    
    @patch('sagemaker.hyperpod.common.cli_decorators.config.load_kube_config')
    @patch('kubernetes.client.VersionApi')
    def test_403_forbidden(self, mock_version_api, mock_load_config):
        """Test 403 Forbidden ApiException"""
        mock_version_instance = Mock()
        mock_version_api.return_value = mock_version_instance
        mock_version_instance.get_code.side_effect = ApiException(status=403, reason="Forbidden")
        
        is_connected, error_type = _check_kubernetes_connectivity()
        
        assert is_connected is False
        assert error_type == "forbidden"
    
    @patch('sagemaker.hyperpod.common.cli_decorators.config.load_kube_config')
    @patch('kubernetes.client.VersionApi')
    def test_connection_error(self, mock_version_api, mock_load_config):
        """Test connection timeout error"""
        mock_version_instance = Mock()
        mock_version_api.return_value = mock_version_instance
        mock_version_instance.get_code.side_effect = Exception("connection timeout")
        
        is_connected, error_type = _check_kubernetes_connectivity()
        
        assert is_connected is False
        assert error_type == "connection_error"
    
    @patch('sagemaker.hyperpod.common.cli_decorators.config.load_kube_config')
    @patch('kubernetes.client.VersionApi')
    def test_unauthorized_string_error(self, mock_version_api, mock_load_config):
        """Test unauthorized error in string format"""
        mock_version_instance = Mock()
        mock_version_api.return_value = mock_version_instance
        mock_version_instance.get_code.side_effect = Exception("401 unauthorized access")
        
        is_connected, error_type = _check_kubernetes_connectivity()
        
        assert is_connected is False
        assert error_type == "unauthorized"


class TestKubernetesAuthErrorMessages:
    """Test the _generate_kubernetes_auth_error_message function"""
    
    def test_no_config_error_message(self):
        """Test error message for no configuration found"""
        message = _generate_kubernetes_auth_error_message("no_config")
        
        assert "❌ Kubernetes configuration not found" in message
        assert "hyp set-cluster-context" in message
        assert "aws eks update-kubeconfig" not in message
        assert "💡 This will set up the necessary Kubernetes configuration" in message
    
    def test_invalid_config_error_message(self):
        """Test error message for invalid configuration"""
        message = _generate_kubernetes_auth_error_message("invalid_config")
        
        assert "❌ Invalid Kubernetes configuration" in message
        assert "hyp set-cluster-context" in message
        assert "aws eks update-kubeconfig" not in message
        assert "💡 This will refresh your cluster configuration" in message
    
    @patch('sagemaker.hyperpod.common.cli_decorators._get_current_kubernetes_context')
    @patch('sagemaker.hyperpod.common.cli_decorators._check_aws_credentials')
    def test_unauthorized_with_valid_aws_creds(self, mock_aws_creds, mock_context):
        """Test unauthorized error message with valid AWS credentials"""
        mock_context.return_value = "my-cluster"
        mock_aws_creds.return_value = True
        
        message = _generate_kubernetes_auth_error_message("unauthorized")
        
        assert "❌ Kubernetes authentication failed (401 Unauthorized)" in message
        assert "Current context: my-cluster" in message
        assert "hyp set-cluster-context" in message
        assert "Try your HyperPod command again" in message
        assert "aws eks update-kubeconfig" not in message
        assert "💡 This will refresh your authentication" in message
    
    @patch('sagemaker.hyperpod.common.cli_decorators._get_current_kubernetes_context')
    @patch('sagemaker.hyperpod.common.cli_decorators._check_aws_credentials')
    def test_unauthorized_with_invalid_aws_creds(self, mock_aws_creds, mock_context):
        """Test unauthorized error message with invalid AWS credentials"""
        mock_context.return_value = "my-cluster"
        mock_aws_creds.return_value = False
        
        message = _generate_kubernetes_auth_error_message("unauthorized")
        
        assert "❌ Kubernetes authentication failed (401 Unauthorized)" in message
        assert "🔍 AWS credentials issue detected" in message
        assert "aws sts get-caller-identity" in message
        assert "hyp set-cluster-context" in message
        assert "aws eks update-kubeconfig" not in message
        assert "💡 Make sure your AWS credentials have the necessary EKS permissions" in message
    
    def test_forbidden_error_message(self):
        """Test forbidden error message"""
        message = _generate_kubernetes_auth_error_message("forbidden")
        
        assert "❌ Kubernetes access denied (403 Forbidden)" in message
        assert "RBAC permissions" in message
        assert "kubectl config current-context" not in message
        assert "kubectl auth can-i get pods" not in message
        assert "Verify you're using the correct cluster context" in message
        assert "Contact your cluster administrator for access" in message
    
    def test_connection_error_message(self):
        """Test connection error message"""
        message = _generate_kubernetes_auth_error_message("connection_error")
        
        assert "❌ Cannot connect to Kubernetes cluster" in message
        assert "Network connection to the cluster failed" in message
        assert "hyp set-cluster-context" in message
        assert "aws eks update-kubeconfig" not in message
    
    def test_generic_error_message(self):
        """Test generic error message"""
        message = _generate_kubernetes_auth_error_message("some_unknown_error")
        
        assert "❌ Kubernetes connection failed" in message
        assert "Error: some_unknown_error" in message
        assert "kubectl config view" not in message
        assert "kubectl get nodes" not in message
        assert "hyp set-cluster-context" in message


class TestKubernetesOperationDetection:
    """Test the _is_kubernetes_operation function"""
    
    def test_logs_operation_detection(self):
        """Test detection of logs operations"""
        mock_func = Mock()
        mock_func.__name__ = "js_get_operator_logs"
        
        result = _is_kubernetes_operation(mock_func)
        
        assert result is True
    
    def test_create_operation_detection(self):
        """Test detection of create operations"""
        mock_func = Mock()
        mock_func.__name__ = "js_create_endpoint"
        
        result = _is_kubernetes_operation(mock_func)
        
        assert result is True
    
    def test_describe_operation_detection(self):
        """Test detection of describe operations"""
        mock_func = Mock()
        mock_func.__name__ = "pytorch_describe_job"
        
        result = _is_kubernetes_operation(mock_func)
        
        assert result is True
    
    def test_non_kubernetes_operation(self):
        """Test non-Kubernetes operation detection"""
        mock_func = Mock()
        mock_func.__name__ = "some_other_function"
        
        result = _is_kubernetes_operation(mock_func)
        
        assert result is False
    
    @patch('sagemaker.hyperpod.common.cli_decorators.click.get_current_context')
    def test_click_command_detection(self, mock_get_context):
        """Test detection via Click command context"""
        mock_func = Mock()
        mock_func.__name__ = "some_function"
        
        mock_context = Mock()
        mock_context.info_name = "hyp-get-logs"
        mock_get_context.return_value = mock_context
        
        result = _is_kubernetes_operation(mock_func)
        
        assert result is True
    
    def test_wrapped_function_detection(self):
        """Test detection of wrapped functions"""
        mock_func = Mock()
        mock_func.__name__ = "wrapper"
        
        mock_wrapped = Mock()
        mock_wrapped.__name__ = "get_operator_logs"
        mock_func.__wrapped__ = mock_wrapped
        
        result = _is_kubernetes_operation(mock_func)
        
        assert result is True


class TestAWSCredentialsCheck:
    """Test the _check_aws_credentials function"""
    
    @patch('boto3.client')
    def test_valid_aws_credentials(self, mock_boto_client):
        """Test valid AWS credentials"""
        mock_sts = Mock()
        mock_boto_client.return_value = mock_sts
        mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}
        
        result = _check_aws_credentials()
        
        assert result is True
        mock_boto_client.assert_called_once_with('sts')
        mock_sts.get_caller_identity.assert_called_once()
    
    @patch('boto3.client')
    def test_no_credentials_error(self, mock_boto_client):
        """Test NoCredentialsError"""
        from botocore.exceptions import NoCredentialsError
        
        mock_sts = Mock()
        mock_boto_client.return_value = mock_sts
        mock_sts.get_caller_identity.side_effect = NoCredentialsError()
        
        result = _check_aws_credentials()
        
        assert result is False
    
    @patch('boto3.client')
    def test_partial_credentials_error(self, mock_boto_client):
        """Test PartialCredentialsError"""
        from botocore.exceptions import PartialCredentialsError
        
        mock_sts = Mock()
        mock_boto_client.return_value = mock_sts
        mock_sts.get_caller_identity.side_effect = PartialCredentialsError(provider="aws", cred_var="AWS_SECRET_ACCESS_KEY")
        
        result = _check_aws_credentials()
        
        assert result is False


class TestKubernetesContextRetrieval:
    """Test the _get_current_kubernetes_context function"""
    
    @patch('sagemaker.hyperpod.common.cli_decorators.config.list_kube_config_contexts')
    def test_get_current_context_success(self, mock_list_contexts):
        """Test successful context retrieval"""
        mock_contexts = [{"name": "context1"}, {"name": "context2"}]
        mock_active = {"name": "my-cluster"}
        mock_list_contexts.return_value = (mock_contexts, mock_active)
        
        result = _get_current_kubernetes_context()
        
        assert result == "my-cluster"
    
    @patch('sagemaker.hyperpod.common.cli_decorators.config.list_kube_config_contexts')
    def test_get_current_context_no_active(self, mock_list_contexts):
        """Test context retrieval with no active context"""
        mock_contexts = [{"name": "context1"}, {"name": "context2"}]
        mock_list_contexts.return_value = (mock_contexts, None)
        
        result = _get_current_kubernetes_context()
        
        assert result == "none"
    
    @patch('sagemaker.hyperpod.common.cli_decorators.config.list_kube_config_contexts')
    def test_get_current_context_error(self, mock_list_contexts):
        """Test context retrieval with error"""
        mock_list_contexts.side_effect = Exception("Config error")
        
        result = _get_current_kubernetes_context()
        
        assert result == "unknown"


class TestDecoratorIntegration:
    """Test the handle_cli_exceptions decorator integration"""
    
    @patch('sagemaker.hyperpod.common.cli_decorators._is_kubernetes_operation')
    @patch('sagemaker.hyperpod.common.cli_decorators._check_kubernetes_connectivity')
    @patch('sagemaker.hyperpod.common.cli_decorators.click.echo')
    def test_decorator_proactive_auth_check_unauthorized(self, mock_echo, mock_connectivity, mock_is_k8s_op):
        """Test decorator proactive authentication check for unauthorized error"""
        mock_is_k8s_op.return_value = True
        mock_connectivity.return_value = (False, "unauthorized")
        
        @handle_cli_exceptions()
        def mock_function():
            return "success"
        
        mock_function.__name__ = "get_operator_logs"
        
        # Should exit with sys.exit(1) due to auth failure
        with pytest.raises(SystemExit) as exc_info:
            mock_function()
        
        assert exc_info.value.code == 1
        mock_echo.assert_called()
        # Verify the error message contains expected content
        error_message = mock_echo.call_args[0][0]
        assert "❌ Kubernetes authentication failed (401 Unauthorized)" in error_message
        assert "hyp set-cluster-context" in error_message
    
    @patch('sagemaker.hyperpod.common.cli_decorators._is_kubernetes_operation')
    @patch('sagemaker.hyperpod.common.cli_decorators._check_kubernetes_connectivity')
    def test_decorator_successful_auth_check(self, mock_connectivity, mock_is_k8s_op):
        """Test decorator with successful authentication check"""
        mock_is_k8s_op.return_value = True
        mock_connectivity.return_value = (True, "")
        
        @handle_cli_exceptions()
        def mock_function():
            return "success"
        
        mock_function.__name__ = "get_operator_logs"
        
        result = mock_function()
        
        assert result == "success"
    
    @patch('sagemaker.hyperpod.common.cli_decorators._is_kubernetes_operation')
    @patch('sagemaker.hyperpod.common.cli_decorators._check_kubernetes_connectivity')
    @patch('sagemaker.hyperpod.common.cli_decorators.click.echo')
    def test_decorator_reactive_401_handling(self, mock_echo, mock_connectivity, mock_is_k8s_op):
        """Test decorator reactive handling of 401 ApiException"""
        mock_is_k8s_op.return_value = True
        mock_connectivity.return_value = (True, "")
        
        @handle_cli_exceptions()
        def mock_function():
            raise ApiException(status=401, reason="Unauthorized")
        
        mock_function.__name__ = "get_operator_logs"
        
        with pytest.raises(SystemExit) as exc_info:
            mock_function()
        
        assert exc_info.value.code == 1
        mock_echo.assert_called()
        error_message = mock_echo.call_args[0][0]
        assert "❌ Kubernetes authentication failed (401 Unauthorized)" in error_message
    
    @patch('sagemaker.hyperpod.common.cli_decorators._is_kubernetes_operation')
    @patch('sagemaker.hyperpod.common.cli_decorators._check_kubernetes_connectivity')
    @patch('sagemaker.hyperpod.common.cli_decorators.click.echo')
    def test_decorator_reactive_403_handling(self, mock_echo, mock_connectivity, mock_is_k8s_op):
        """Test decorator reactive handling of 403 ApiException"""
        mock_is_k8s_op.return_value = True
        mock_connectivity.return_value = (True, "")
        
        @handle_cli_exceptions()
        def mock_function():
            raise ApiException(status=403, reason="Forbidden")
        
        mock_function.__name__ = "get_operator_logs"
        
        with pytest.raises(SystemExit) as exc_info:
            mock_function()
        
        assert exc_info.value.code == 1
        mock_echo.assert_called()
        error_message = mock_echo.call_args[0][0]
        assert "❌ Kubernetes access denied (403 Forbidden)" in error_message
    
    @patch('sagemaker.hyperpod.common.cli_decorators._is_kubernetes_operation')
    @patch('sagemaker.hyperpod.common.cli_decorators._check_kubernetes_connectivity')
    @patch('sagemaker.hyperpod.common.cli_decorators.click.echo')
    def test_decorator_config_exception_handling(self, mock_echo, mock_connectivity, mock_is_k8s_op):
        """Test decorator handling of ConfigException"""
        mock_is_k8s_op.return_value = True
        mock_connectivity.return_value = (True, "")
        
        @handle_cli_exceptions()
        def mock_function():
            raise ConfigException("No configuration found")
        
        mock_function.__name__ = "get_operator_logs"
        
        with pytest.raises(SystemExit) as exc_info:
            mock_function()
        
        assert exc_info.value.code == 1
        mock_echo.assert_called()
        error_message = mock_echo.call_args[0][0]
        assert "❌ Kubernetes configuration not found" in error_message
    
    @patch('sagemaker.hyperpod.common.cli_decorators._is_kubernetes_operation')
    @patch('sagemaker.hyperpod.common.cli_decorators._check_kubernetes_connectivity')
    @patch('sagemaker.hyperpod.common.cli_decorators.click.echo')
    def test_decorator_string_401_handling(self, mock_echo, mock_connectivity, mock_is_k8s_op):
        """Test decorator handling of string-based 401 errors"""
        mock_is_k8s_op.return_value = True
        mock_connectivity.return_value = (True, "")
        
        @handle_cli_exceptions()
        def mock_function():
            raise Exception("401 Unauthorized: the server has asked for the client to provide credentials")
        
        mock_function.__name__ = "get_operator_logs"
        
        with pytest.raises(SystemExit) as exc_info:
            mock_function()
        
        assert exc_info.value.code == 1
        mock_echo.assert_called()
        error_message = mock_echo.call_args[0][0]
        assert "❌ Kubernetes authentication failed (401 Unauthorized)" in error_message
    
    @patch('sagemaker.hyperpod.common.cli_decorators._is_kubernetes_operation')
    def test_decorator_non_kubernetes_operation(self, mock_is_k8s_op):
        """Test decorator with non-Kubernetes operation"""
        mock_is_k8s_op.return_value = False
        
        @handle_cli_exceptions()
        def mock_function():
            return "success"
        
        mock_function.__name__ = "some_other_function"
        
        result = mock_function()
        
        assert result == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
