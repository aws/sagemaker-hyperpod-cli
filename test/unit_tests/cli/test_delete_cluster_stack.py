"""
Unit tests for delete cluster-stack command implementation.
Tests all possible scenarios including success, failures, and edge cases.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
import click
import json

from sagemaker.hyperpod.cli.commands.cluster_stack import delete_cluster_stack
from sagemaker.hyperpod.cli.cluster_stack_utils import StackNotFoundError


class TestDeleteClusterStack:
    """Test suite for delete cluster-stack command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.delete_stack_with_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_successful_deletion_without_retention(self, mock_setup_logging, mock_delete_stack):
        """Test successful stack deletion without resource retention."""
        # Setup mocks
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2', '--debug']
        )
        
        # Assertions
        assert result.exit_code == 0
        
        # Verify function calls
        mock_delete_stack.assert_called_once()
        call_args = mock_delete_stack.call_args
        assert call_args[1]['stack_name'] == 'test-stack'
        assert call_args[1]['region'] == 'us-west-2'
        assert call_args[1]['retain_resources_str'] == ""

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.delete_stack_with_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_successful_deletion_with_retention(self, mock_setup_logging, mock_delete_stack):
        """Test successful stack deletion with resource retention."""
        # Setup mocks
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        # Execute command with retention
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--retain-resources', 'S3BucketStack,VPCStack', '--region', 'us-west-2']
        )
        
        # Assertions
        assert result.exit_code == 0
        
        # Verify function calls
        mock_delete_stack.assert_called_once()
        call_args = mock_delete_stack.call_args
        assert call_args[1]['stack_name'] == 'test-stack'
        assert call_args[1]['region'] == 'us-west-2'
        assert call_args[1]['retain_resources_str'] == 'S3BucketStack,VPCStack'

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.delete_stack_with_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_stack_not_found(self, mock_setup_logging, mock_delete_stack):
        """Test handling when stack doesn't exist."""
        # Setup mocks
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        mock_delete_stack.side_effect = StackNotFoundError("Stack 'non-existent-stack' not found")
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['non-existent-stack', '--region', 'us-west-2']
        )
        
        # Assertions
        assert result.exit_code == 0
        assert "❌ Stack 'non-existent-stack' not found" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.delete_stack_with_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_termination_protection_enabled(self, mock_setup_logging, mock_delete_stack):
        """Test handling when stack has termination protection enabled."""
        # Setup mocks
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        # Mock termination protection error
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack cannot be deleted while TerminationProtection is enabled'}},
            'DeleteStack'
        )
        mock_delete_stack.side_effect = error
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['protected-stack', '--region', 'us-west-2']
        )
        
        # Assertions
        assert result.exit_code == 1
        assert "TerminationProtection is enabled" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.delete_stack_with_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_cloudformation_retention_limitation(self, mock_setup_logging, mock_delete_stack):
        """Test handling CloudFormation's retain-resources limitation."""
        # Setup mocks
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        # Mock CloudFormation retention limitation error
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'specify which resources to retain only when the stack is in the DELETE_FAILED state'}},
            'DeleteStack'
        )
        mock_delete_stack.side_effect = error
        
        # Execute command with retention
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--retain-resources', 'S3BucketStack', '--region', 'us-west-2']
        )
        
        # Assertions - CLI re-raises as ClickException, so exit code is 1
        assert result.exit_code == 1
        assert "DELETE_FAILED state" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.delete_stack_with_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_access_denied_error(self, mock_setup_logging, mock_delete_stack):
        """Test handling access denied errors."""
        # Setup mocks
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        # Mock access denied error
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'ListStackResources'
        )
        mock_delete_stack.side_effect = error
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2']
        )
        
        # Assertions - ClickException results in exit code 1
        assert result.exit_code == 1
        assert "Access denied" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.delete_stack_with_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_retain_resources_parsing(self, mock_setup_logging, mock_delete_stack):
        """Test proper parsing of retain-resources parameter."""
        # Setup mocks
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        # Test with spaces and various formats
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--retain-resources', ' S3BucketStack , VPCStack , IAMRole1 ', '--region', 'us-west-2']
        )
        
        # Assertions
        assert result.exit_code == 0
        
        # Verify function calls
        mock_delete_stack.assert_called_once()
        call_args = mock_delete_stack.call_args
        assert call_args[1]['retain_resources_str'] == ' S3BucketStack , VPCStack , IAMRole1 '

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.delete_stack_with_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_debug_logging(self, mock_setup_logging, mock_delete_stack):
        """Test that debug logging is properly enabled."""
        # Setup mocks
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        # Execute command with debug flag
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2', '--debug']
        )
        
        # Assertions
        assert result.exit_code == 0
        
        # Verify setup_logging was called
        mock_setup_logging.assert_called_once()

    def test_command_help(self):
        """Test that command help is displayed correctly."""
        result = self.runner.invoke(delete_cluster_stack, ['--help'])
        
        assert result.exit_code == 0
        assert "Delete a HyperPod cluster stack." in result.output
        assert "--retain-resources" in result.output
        assert "--region" in result.output
        assert "--debug" in result.output
        assert "Removes the specified CloudFormation stack and all associated AWS resources." in result.output

    def test_required_region_flag(self):
        """Test that the --region flag is required."""
        # Test without region flag should fail
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack']
        )
        
        # Assertions
        assert result.exit_code == 2  # Click returns 2 for missing required options
        assert "Missing option '--region'" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.delete_stack_with_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_generic_error_handling(self, mock_setup_logging, mock_delete_stack):
        """Test handling of generic/unexpected errors."""
        # Setup mocks
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        # Mock unexpected error
        error = Exception("Unexpected error occurred")
        mock_delete_stack.side_effect = error
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2']
        )
        
        # Assertions
        assert result.exit_code == 1
        assert "Unexpected error occurred" in result.output


if __name__ == '__main__':
    pytest.main([__file__])
