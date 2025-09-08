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
from sagemaker.hyperpod.cli.cluster_stack_utils import (
    StackNotFoundError,
    parse_retain_resources,
    perform_stack_deletion
)


class TestDeleteClusterStack:
    """Test suite for delete cluster-stack command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.mock_cf_client = Mock()
        self.mock_logger = Mock()
        
        # Sample stack resources for testing
        self.sample_resources = [
            {
                'LogicalResourceId': 'EC2Instance1',
                'ResourceType': 'AWS::EC2::Instance',
                'PhysicalResourceId': 'i-1234567890abcdef0'
            },
            {
                'LogicalResourceId': 'VPCStack',
                'ResourceType': 'AWS::CloudFormation::Stack',
                'PhysicalResourceId': 'vpc-1234567890abcdef0'
            },
            {
                'LogicalResourceId': 'S3BucketStack',
                'ResourceType': 'AWS::CloudFormation::Stack',
                'PhysicalResourceId': 's3-bucket-name'
            },
            {
                'LogicalResourceId': 'IAMRole1',
                'ResourceType': 'AWS::IAM::Role',
                'PhysicalResourceId': 'MyRole'
            },
            {
                'LogicalResourceId': 'SecurityGroup1',
                'ResourceType': 'AWS::EC2::SecurityGroup',
                'PhysicalResourceId': 'sg-1234567890abcdef0'
            }
        ]

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.get_stack_resources_and_validate_retention')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.display_deletion_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_successful_deletion_without_retention(self, mock_setup_logging, mock_perform_deletion, mock_display_confirmation, mock_get_resources):
        """Test successful stack deletion without resource retention."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_get_resources.return_value = (self.sample_resources, [], [])
        mock_display_confirmation.return_value = True
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2', '--debug']
        )
        
        # Assertions
        assert result.exit_code == 0
        
        # Verify function calls
        mock_get_resources.assert_called_once_with('test-stack', 'us-west-2', None)
        mock_display_confirmation.assert_called_once_with(self.sample_resources, [], [])
        mock_perform_deletion.assert_called_once_with('test-stack', 'us-west-2', [])

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.get_stack_resources_and_validate_retention')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.display_deletion_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_successful_deletion_with_retention(self, mock_setup_logging, mock_perform_deletion, mock_display_confirmation, mock_get_resources):
        """Test successful stack deletion with resource retention."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_get_resources.return_value = (self.sample_resources, ['S3BucketStack', 'VPCStack'], [])
        mock_display_confirmation.return_value = True
        
        # Execute command with retention
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--retain-resources', 'S3BucketStack,VPCStack', '--region', 'us-west-2']
        )
        
        # Assertions
        assert result.exit_code == 0
        
        # Verify function calls
        mock_get_resources.assert_called_once_with('test-stack', 'us-west-2', 'S3BucketStack,VPCStack')
        mock_display_confirmation.assert_called_once_with(self.sample_resources, ['S3BucketStack', 'VPCStack'], [])
        mock_perform_deletion.assert_called_once_with('test-stack', 'us-west-2', ['S3BucketStack', 'VPCStack'])

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.get_stack_resources_and_validate_retention')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.display_deletion_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_user_cancellation(self, mock_setup_logging, mock_perform_deletion, mock_display_confirmation, mock_get_resources):
        """Test user cancelling the deletion operation."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_get_resources.return_value = (self.sample_resources, [], [])
        mock_display_confirmation.return_value = False  # User cancels
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2']
        )
        
        # Assertions
        assert result.exit_code == 0
        assert "Operation cancelled." in result.output
        
        # Verify function calls
        mock_get_resources.assert_called_once_with('test-stack', 'us-west-2', None)
        mock_display_confirmation.assert_called_once_with(self.sample_resources, [], [])
        
        # Verify deletion was not performed
        mock_perform_deletion.assert_not_called()

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.get_stack_resources_and_validate_retention')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_stack_not_found(self, mock_setup_logging, mock_get_resources):
        """Test handling when stack doesn't exist."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_get_resources.side_effect = StackNotFoundError("Stack 'non-existent-stack' not found")
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['non-existent-stack', '--region', 'us-west-2']
        )
        
        # Assertions
        assert result.exit_code == 0
        assert "❌ Stack 'non-existent-stack' not found" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.get_stack_resources_and_validate_retention')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.display_deletion_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.handle_deletion_error')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_termination_protection_enabled(self, mock_setup_logging, mock_handle_error, mock_perform_deletion, mock_display_confirmation, mock_get_resources):
        """Test handling when stack has termination protection enabled."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_get_resources.return_value = (self.sample_resources, [], [])
        mock_display_confirmation.return_value = True
        
        # Mock termination protection error
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack cannot be deleted while TerminationProtection is enabled'}},
            'DeleteStack'
        )
        mock_perform_deletion.side_effect = error
        mock_handle_error.side_effect = click.ClickException("Termination protection must be disabled before deletion")
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['protected-stack', '--region', 'us-west-2']
        )
        
        # Assertions
        assert result.exit_code == 1
        
        # Verify function calls
        mock_get_resources.assert_called_once_with('protected-stack', 'us-west-2', None)
        mock_display_confirmation.assert_called_once_with(self.sample_resources, [], [])
        mock_perform_deletion.assert_called_once_with('protected-stack', 'us-west-2', [])
        mock_handle_error.assert_called_once_with(error, 'protected-stack', 'us-west-2', None)

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.get_stack_resources_and_validate_retention')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.display_deletion_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.handle_deletion_error')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_cloudformation_retention_limitation(self, mock_setup_logging, mock_handle_error, mock_perform_deletion, mock_display_confirmation, mock_get_resources):
        """Test handling CloudFormation's retain-resources limitation."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_get_resources.return_value = (self.sample_resources, ['S3BucketStack'], [])
        mock_display_confirmation.return_value = True
        
        # Mock CloudFormation retention limitation error
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'specify which resources to retain only when the stack is in the DELETE_FAILED state'}},
            'DeleteStack'
        )
        mock_perform_deletion.side_effect = error
        # handle_deletion_error returns None for retention limitation (exits gracefully)
        mock_handle_error.return_value = None
        
        # Execute command with retention
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--retain-resources', 'S3BucketStack', '--region', 'us-west-2']
        )
        
        # Assertions - Now exits gracefully with code 0
        assert result.exit_code == 0
        
        # Verify function calls
        mock_get_resources.assert_called_once_with('test-stack', 'us-west-2', 'S3BucketStack')
        mock_display_confirmation.assert_called_once_with(self.sample_resources, ['S3BucketStack'], [])
        mock_handle_error.assert_called_once_with(error, 'test-stack', 'us-west-2', 'S3BucketStack')

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.get_stack_resources_and_validate_retention')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.display_deletion_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.handle_deletion_error')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.handle_partial_deletion_failure')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_partial_deletion_failure(self, mock_setup_logging, mock_handle_partial_failure, mock_handle_error, mock_perform_deletion, mock_display_confirmation, mock_get_resources):
        """Test handling partial deletion failures with dependency violations."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_get_resources.return_value = (self.sample_resources, [], [])
        mock_display_confirmation.return_value = True
        
        # Mock partial deletion failure
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Resource has dependencies'}},
            'DeleteStack'
        )
        mock_perform_deletion.side_effect = error
        # Mock handle_deletion_error to raise a non-ClickException (so partial deletion handling is triggered)
        mock_handle_error.side_effect = Exception("Some other error")
        # Simulate partial deletion failure that raises ClickException
        mock_handle_partial_failure.side_effect = click.ClickException("Partial deletion detected")
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2']
        )
        
        assert result.exit_code == 1
        
        # Verify function calls
        mock_get_resources.assert_called_once_with('test-stack', 'us-west-2', None)
        mock_display_confirmation.assert_called_once_with(self.sample_resources, [], [])
        mock_perform_deletion.assert_called_once_with('test-stack', 'us-west-2', [])
        mock_handle_error.assert_called_once_with(error, 'test-stack', 'us-west-2', None)
        mock_handle_partial_failure.assert_called_once_with('test-stack', 'us-west-2', self.sample_resources, [])

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.get_stack_resources_and_validate_retention')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.handle_deletion_error')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_access_denied_error(self, mock_setup_logging, mock_handle_error, mock_get_resources):
        """Test handling access denied errors."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        
        # Mock access denied error
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'ListStackResources'
        )
        mock_get_resources.side_effect = error
        mock_handle_error.side_effect = click.ClickException("Access denied. Check AWS permissions")
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2']
        )
        
        # Assertions - ClickException results in exit code 1
        assert result.exit_code == 1
        
        # Verify error handler was called
        mock_handle_error.assert_called_once_with(error, 'test-stack', 'us-west-2', None)

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.get_stack_resources_and_validate_retention')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_empty_stack_resources(self, mock_setup_logging, mock_get_resources):
        """Test handling when stack has no resources."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_get_resources.side_effect = StackNotFoundError("No resources found in stack 'empty-stack'")
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['empty-stack', '--region', 'us-west-2']
        )
        
        # Assertions
        assert result.exit_code == 0
        assert "❌ Stack 'empty-stack' not found" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.get_stack_resources_and_validate_retention')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.display_deletion_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_resource_categorization(self, mock_setup_logging, mock_perform_deletion, mock_display_confirmation, mock_get_resources):
        """Test proper categorization of different resource types."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        
        # Extended resource list with various types
        extended_resources = [
            {'LogicalResourceId': 'EC2Instance1', 'ResourceType': 'AWS::EC2::Instance', 'PhysicalResourceId': 'i-123'},
            {'LogicalResourceId': 'EC2Instance2', 'ResourceType': 'AWS::EC2::Instance', 'PhysicalResourceId': 'i-456'},
            {'LogicalResourceId': 'VPC1', 'ResourceType': 'AWS::EC2::VPC', 'PhysicalResourceId': 'vpc-123'},
            {'LogicalResourceId': 'SecurityGroup1', 'ResourceType': 'AWS::EC2::SecurityGroup', 'PhysicalResourceId': 'sg-123'},
            {'LogicalResourceId': 'InternetGateway1', 'ResourceType': 'AWS::EC2::InternetGateway', 'PhysicalResourceId': 'igw-123'},
            {'LogicalResourceId': 'IAMRole1', 'ResourceType': 'AWS::IAM::Role', 'PhysicalResourceId': 'MyRole'},
            {'LogicalResourceId': 'IAMPolicy1', 'ResourceType': 'AWS::IAM::Policy', 'PhysicalResourceId': 'MyPolicy'},
            {'LogicalResourceId': 'S3Bucket1', 'ResourceType': 'AWS::S3::Bucket', 'PhysicalResourceId': 'my-bucket'},
            {'LogicalResourceId': 'EFSFileSystem1', 'ResourceType': 'AWS::EFS::FileSystem', 'PhysicalResourceId': 'fs-123'},
            {'LogicalResourceId': 'Lambda1', 'ResourceType': 'AWS::Lambda::Function', 'PhysicalResourceId': 'my-function'}
        ]
        
        mock_get_resources.return_value = (extended_resources, [], [])
        mock_display_confirmation.return_value = True
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2']
        )
        
        # Assertions for proper categorization
        assert result.exit_code == 0
        
        # Verify function calls
        mock_get_resources.assert_called_once_with('test-stack', 'us-west-2', None)
        mock_display_confirmation.assert_called_once_with(extended_resources, [], [])
        mock_perform_deletion.assert_called_once_with('test-stack', 'us-west-2', [])

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.get_stack_resources_and_validate_retention')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.display_deletion_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_retain_resources_parsing(self, mock_setup_logging, mock_perform_deletion, mock_display_confirmation, mock_get_resources):
        """Test proper parsing of retain-resources parameter."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_get_resources.return_value = (self.sample_resources, ['S3BucketStack', 'VPCStack', 'IAMRole1'], [])
        mock_display_confirmation.return_value = True
        
        # Test with spaces and various formats
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--retain-resources', ' S3BucketStack , VPCStack , IAMRole1 ', '--region', 'us-west-2']
        )
        
        # Assertions
        assert result.exit_code == 0
        
        # Verify function calls
        mock_get_resources.assert_called_once_with('test-stack', 'us-west-2', ' S3BucketStack , VPCStack , IAMRole1 ')
        mock_display_confirmation.assert_called_once_with(self.sample_resources, ['S3BucketStack', 'VPCStack', 'IAMRole1'], [])
        mock_perform_deletion.assert_called_once_with('test-stack', 'us-west-2', ['S3BucketStack', 'VPCStack', 'IAMRole1'])

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.get_stack_resources_and_validate_retention')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.display_deletion_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_debug_logging(self, mock_setup_logging, mock_perform_deletion, mock_display_confirmation, mock_get_resources):
        """Test that debug logging is properly enabled."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_get_resources.return_value = (self.sample_resources, [], [])
        mock_display_confirmation.return_value = True
        
        # Execute command with debug flag
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2', '--debug']
        )
        
        # Assertions
        assert result.exit_code == 0
        
        # Verify setup_logging was called
        mock_setup_logging.assert_called_once()
        
        # Verify function calls
        mock_get_resources.assert_called_once_with('test-stack', 'us-west-2', None)
        mock_display_confirmation.assert_called_once_with(self.sample_resources, [], [])
        mock_perform_deletion.assert_called_once_with('test-stack', 'us-west-2', [])

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

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.get_stack_resources_and_validate_retention')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.display_deletion_confirmation')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.handle_deletion_error')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_generic_error_handling(self, mock_setup_logging, mock_handle_error, mock_perform_deletion, mock_display_confirmation, mock_get_resources):
        """Test handling of generic/unexpected errors."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_get_resources.return_value = (self.sample_resources, [], [])
        mock_display_confirmation.return_value = True
        
        # Mock unexpected error
        error = Exception("Unexpected error occurred")
        mock_perform_deletion.side_effect = error
        mock_handle_error.side_effect = click.ClickException("Unexpected error occurred")
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2']
        )
        
        # Assertions
        assert result.exit_code == 1
        
        # Verify function calls
        mock_get_resources.assert_called_once_with('test-stack', 'us-west-2', None)
        mock_display_confirmation.assert_called_once_with(self.sample_resources, [], [])
        mock_perform_deletion.assert_called_once_with('test-stack', 'us-west-2', [])
        mock_handle_error.assert_called_once_with(error, 'test-stack', 'us-west-2', None)


if __name__ == '__main__':
    pytest.main([__file__])
