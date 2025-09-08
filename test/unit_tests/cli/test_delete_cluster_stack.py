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
    CloudFormationResourceManager,
    DeletionConfirmationHandler,
    CloudFormationErrorHandler,
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

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.CloudFormationResourceManager')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.DeletionConfirmationHandler')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_successful_deletion_without_retention(self, mock_setup_logging, mock_perform_deletion, mock_confirmation_handler_class, mock_resource_manager_class):
        """Test successful stack deletion without resource retention."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        
        # Mock resource manager
        mock_resource_manager = Mock()
        mock_resource_manager_class.return_value = mock_resource_manager
        mock_resource_manager.get_stack_resources.return_value = self.sample_resources
        mock_resource_manager.validate_retain_resources.return_value = ([], [])
        mock_resource_manager.categorize_resources.return_value = {
            'EC2 Instances': [' - EC2Instance1 (i-1234567890abcdef0)'],
            'Networking': [' - SecurityGroup1'],
            'IAM': [' - IAMRole1'],
            'Storage': [],
            'Other': [' - VPCStack', ' - S3BucketStack']
        }
        
        # Mock confirmation handler
        mock_confirmation_handler = Mock()
        mock_confirmation_handler_class.return_value = mock_confirmation_handler
        mock_confirmation_handler.confirm_deletion.return_value = True
        
        # Execute command with 'y' input for confirmation
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2', '--debug'],
            input='y\n'
        )
        
        # Assertions
        assert result.exit_code == 0
        # Since we're mocking the utility classes, the actual output methods aren't called
        # We verify behavior through method calls instead of output text
        
        # Verify utility calls
        mock_resource_manager.get_stack_resources.assert_called_once_with('test-stack')
        mock_resource_manager.validate_retain_resources.assert_called_once_with([], self.sample_resources)
        mock_confirmation_handler.confirm_deletion.assert_called_once()
        mock_perform_deletion.assert_called_once_with('test-stack', 'us-west-2', [])

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.CloudFormationResourceManager')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.DeletionConfirmationHandler')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_successful_deletion_with_retention(self, mock_setup_logging, mock_perform_deletion, mock_confirmation_handler_class, mock_resource_manager_class):
        """Test successful stack deletion with resource retention."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        
        # Mock resource manager
        mock_resource_manager = Mock()
        mock_resource_manager_class.return_value = mock_resource_manager
        mock_resource_manager.get_stack_resources.return_value = self.sample_resources
        mock_resource_manager.validate_retain_resources.return_value = (['S3BucketStack', 'VPCStack'], [])
        mock_resource_manager.categorize_resources.return_value = {
            'EC2 Instances': [' - EC2Instance1 (i-1234567890abcdef0)'],
            'Networking': [' - SecurityGroup1'],
            'IAM': [' - IAMRole1'],
            'Storage': [],
            'Other': []
        }
        
        # Mock confirmation handler
        mock_confirmation_handler = Mock()
        mock_confirmation_handler_class.return_value = mock_confirmation_handler
        mock_confirmation_handler.confirm_deletion.return_value = True
        
        # Execute command with retention
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--retain-resources', 'S3BucketStack,VPCStack', '--region', 'us-west-2'],
            input='y\n'
        )
        
        # Assertions
        assert result.exit_code == 0
        
        # Verify utility calls
        mock_resource_manager.get_stack_resources.assert_called_once_with('test-stack')
        mock_resource_manager.validate_retain_resources.assert_called_once_with(['S3BucketStack', 'VPCStack'], self.sample_resources)
        mock_confirmation_handler.confirm_deletion.assert_called_once()
        mock_perform_deletion.assert_called_once_with('test-stack', 'us-west-2', ['S3BucketStack', 'VPCStack'])

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.CloudFormationResourceManager')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.DeletionConfirmationHandler')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_user_cancellation(self, mock_setup_logging, mock_perform_deletion, mock_confirmation_handler_class, mock_resource_manager_class):
        """Test user cancelling the deletion operation."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        
        # Mock resource manager
        mock_resource_manager = Mock()
        mock_resource_manager_class.return_value = mock_resource_manager
        mock_resource_manager.get_stack_resources.return_value = self.sample_resources
        mock_resource_manager.validate_retain_resources.return_value = ([], [])
        mock_resource_manager.categorize_resources.return_value = {
            'EC2 Instances': [' - EC2Instance1 (i-1234567890abcdef0)'],
            'Networking': [' - SecurityGroup1'],
            'IAM': [' - IAMRole1'],
            'Storage': [],
            'Other': [' - VPCStack', ' - S3BucketStack']
        }
        
        # Mock confirmation handler - user cancels
        mock_confirmation_handler = Mock()
        mock_confirmation_handler_class.return_value = mock_confirmation_handler
        mock_confirmation_handler.confirm_deletion.return_value = False
        
        # Execute command with 'n' input for cancellation
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2'],
            input='n\n'
        )
        
        # Assertions
        assert result.exit_code == 0
        assert "Operation cancelled." in result.output
        
        # Verify utility calls
        mock_resource_manager.get_stack_resources.assert_called_once_with('test-stack')
        mock_resource_manager.validate_retain_resources.assert_called_once_with([], self.sample_resources)
        
        # Verify deletion was not performed
        mock_perform_deletion.assert_not_called()

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.CloudFormationResourceManager')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_stack_not_found(self, mock_setup_logging, mock_resource_manager_class):
        """Test handling when stack doesn't exist."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        
        # Mock resource manager to raise StackNotFoundError
        mock_resource_manager = Mock()
        mock_resource_manager_class.return_value = mock_resource_manager
        mock_resource_manager.get_stack_resources.side_effect = StackNotFoundError("Stack 'non-existent-stack' not found")
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['non-existent-stack', '--region', 'us-west-2']
        )
        
        # Assertions
        assert result.exit_code == 0
        assert "❌ Stack 'non-existent-stack' not found" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.CloudFormationResourceManager')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.DeletionConfirmationHandler')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.CloudFormationErrorHandler')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_termination_protection_enabled(self, mock_setup_logging, mock_perform_deletion, mock_error_handler_class, mock_confirmation_handler_class, mock_resource_manager_class):
        """Test handling when stack has termination protection enabled."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        
        # Mock resource manager
        mock_resource_manager = Mock()
        mock_resource_manager_class.return_value = mock_resource_manager
        mock_resource_manager.get_stack_resources.return_value = self.sample_resources
        mock_resource_manager.validate_retain_resources.return_value = ([], [])
        mock_resource_manager.categorize_resources.return_value = {
            'EC2 Instances': [' - EC2Instance1 (i-1234567890abcdef0)'],
            'Networking': [' - SecurityGroup1'],
            'IAM': [' - IAMRole1'],
            'Storage': [],
            'Other': [' - VPCStack', ' - S3BucketStack']
        }
        
        # Mock confirmation handler
        mock_confirmation_handler = Mock()
        mock_confirmation_handler_class.return_value = mock_confirmation_handler
        mock_confirmation_handler.confirm_deletion.return_value = True
        
        # Mock error handler
        mock_error_handler = Mock()
        mock_error_handler_class.return_value = mock_error_handler
        
        # Mock termination protection error
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack cannot be deleted while TerminationProtection is enabled'}},
            'DeleteStack'
        )
        mock_perform_deletion.side_effect = error
        # The error handler should raise ClickException for termination protection
        mock_error_handler.handle_deletion_error.side_effect = click.ClickException("Termination protection must be disabled before deletion")
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['protected-stack', '--region', 'us-west-2'],
            input='y\n'
        )
        
        # Assertions
        assert result.exit_code == 1
        
        # Verify utility calls
        mock_resource_manager.get_stack_resources.assert_called_once_with('protected-stack')
        mock_resource_manager.validate_retain_resources.assert_called_once_with([], self.sample_resources)
        mock_confirmation_handler.confirm_deletion.assert_called_once()
        mock_perform_deletion.assert_called_once_with('protected-stack', 'us-west-2', [])
        mock_error_handler.handle_deletion_error.assert_called_once_with(error, 'protected-stack', None)

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.CloudFormationResourceManager')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.DeletionConfirmationHandler')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.CloudFormationErrorHandler')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_cloudformation_retention_limitation(self, mock_setup_logging, mock_perform_deletion, mock_error_handler_class, mock_confirmation_handler_class, mock_resource_manager_class):
        """Test handling CloudFormation's retain-resources limitation."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        
        # Mock resource manager
        mock_resource_manager = Mock()
        mock_resource_manager_class.return_value = mock_resource_manager
        mock_resource_manager.get_stack_resources.return_value = self.sample_resources
        mock_resource_manager.validate_retain_resources.return_value = (['S3BucketStack'], [])
        mock_resource_manager.categorize_resources.return_value = {
            'EC2 Instances': [' - EC2Instance1 (i-1234567890abcdef0)'],
            'Networking': [' - SecurityGroup1'],
            'IAM': [' - IAMRole1'],
            'Storage': [],
            'Other': [' - VPCStack']
        }
        
        # Mock confirmation handler
        mock_confirmation_handler = Mock()
        mock_confirmation_handler_class.return_value = mock_confirmation_handler
        mock_confirmation_handler.confirm_deletion.return_value = True
        
        # Mock error handler - this case returns gracefully without raising exception
        mock_error_handler = Mock()
        mock_error_handler_class.return_value = mock_error_handler
        # handle_deletion_error returns None for retention limitation (exits gracefully)
        mock_error_handler.handle_deletion_error.return_value = None
        
        # Mock CloudFormation retention limitation error
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'specify which resources to retain only when the stack is in the DELETE_FAILED state'}},
            'DeleteStack'
        )
        mock_perform_deletion.side_effect = error
        
        # Execute command with retention
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--retain-resources', 'S3BucketStack', '--region', 'us-west-2'],
            input='y\n'
        )
        
        # Assertions - Now exits gracefully with code 0
        assert result.exit_code == 0
        
        # Verify utility calls
        mock_resource_manager.get_stack_resources.assert_called_once_with('test-stack')
        mock_resource_manager.validate_retain_resources.assert_called_once_with(['S3BucketStack'], self.sample_resources)
        mock_confirmation_handler.confirm_deletion.assert_called_once()

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.CloudFormationResourceManager')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.DeletionConfirmationHandler')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.CloudFormationErrorHandler')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_partial_deletion_failure(self, mock_setup_logging, mock_perform_deletion, mock_error_handler_class, mock_confirmation_handler_class, mock_resource_manager_class):
        """Test handling partial deletion failures with dependency violations."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        
        # Mock resource manager
        mock_resource_manager = Mock()
        mock_resource_manager_class.return_value = mock_resource_manager
        mock_resource_manager.get_stack_resources.return_value = self.sample_resources
        mock_resource_manager.validate_retain_resources.return_value = ([], [])
        mock_resource_manager.categorize_resources.return_value = {
            'EC2 Instances': [' - EC2Instance1 (i-1234567890abcdef0)'],
            'Networking': [' - SecurityGroup1'],
            'IAM': [' - IAMRole1'],
            'Storage': [],
            'Other': [' - VPCStack', ' - S3BucketStack']
        }
        
        # Mock current resources after partial deletion
        remaining_resources = [
            {
                'LogicalResourceId': 'VPCStack',
                'ResourceType': 'AWS::CloudFormation::Stack',
                'PhysicalResourceId': 'vpc-1234567890abcdef0'
            },
            {
                'LogicalResourceId': 'SecurityGroup1',
                'ResourceType': 'AWS::EC2::SecurityGroup',
                'PhysicalResourceId': 'sg-1234567890abcdef0'
            }
        ]
        
        # Mock resource manager to return remaining resources on second call
        mock_resource_manager.get_stack_resources.side_effect = [self.sample_resources, remaining_resources]
        mock_resource_manager.compare_resource_states.return_value = (
            [' - EC2Instance1 (i-1234567890abcdef0)', ' - IAMRole1', ' - S3BucketStack'],  # deleted
            [' - VPCStack', ' - SecurityGroup1']  # remaining
        )
        
        # Mock confirmation handler
        mock_confirmation_handler = Mock()
        mock_confirmation_handler_class.return_value = mock_confirmation_handler
        mock_confirmation_handler.confirm_deletion.return_value = True
        
        # Mock error handler
        mock_error_handler = Mock()
        mock_error_handler_class.return_value = mock_error_handler
        
        # Mock partial deletion failure
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Resource has dependencies'}},
            'DeleteStack'
        )
        mock_perform_deletion.side_effect = error
        # The handle_deletion_error should raise a non-ClickException to trigger partial deletion handling
        mock_error_handler.handle_deletion_error.side_effect = Exception("Partial deletion detected")
        mock_error_handler.handle_partial_deletion_failure.return_value = None
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2'],
            input='y\n'
        )
        
        assert result.exit_code == 1
        
        # Verify utility calls
        mock_resource_manager.get_stack_resources.assert_called_with('test-stack')
        mock_confirmation_handler.confirm_deletion.assert_called_once()
        mock_perform_deletion.assert_called_once_with('test-stack', 'us-west-2', [])
        mock_error_handler.handle_partial_deletion_failure.assert_called_once()

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.CloudFormationResourceManager')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.CloudFormationErrorHandler')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_access_denied_error(self, mock_setup_logging, mock_error_handler_class, mock_resource_manager_class):
        """Test handling access denied errors."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        
        # Mock resource manager to raise access denied error
        mock_resource_manager = Mock()
        mock_resource_manager_class.return_value = mock_resource_manager
        
        # Mock error handler
        mock_error_handler = Mock()
        mock_error_handler_class.return_value = mock_error_handler
        
        # Mock access denied error
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'ListStackResources'
        )
        mock_resource_manager.get_stack_resources.side_effect = error
        
        # The error handler should raise ClickException for access denied
        mock_error_handler.handle_deletion_error.side_effect = click.ClickException("Access denied. Check AWS permissions")
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2']
        )
        
        # Assertions - ClickException results in exit code 1
        assert result.exit_code == 1
        
        # Verify error handler was called
        mock_error_handler.handle_deletion_error.assert_called_once_with(error, 'test-stack', None)

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.CloudFormationResourceManager')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_empty_stack_resources(self, mock_setup_logging, mock_resource_manager_class):
        """Test handling when stack has no resources."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        
        # Mock resource manager to return empty resources
        mock_resource_manager = Mock()
        mock_resource_manager_class.return_value = mock_resource_manager
        mock_resource_manager.get_stack_resources.return_value = []
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['empty-stack', '--region', 'us-west-2']
        )
        
        # Assertions
        assert result.exit_code == 0
        assert "❌ No resources found in stack 'empty-stack'" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.CloudFormationResourceManager')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.DeletionConfirmationHandler')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_resource_categorization(self, mock_setup_logging, mock_perform_deletion, mock_confirmation_handler_class, mock_resource_manager_class):
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
        
        # Mock resource manager
        mock_resource_manager = Mock()
        mock_resource_manager_class.return_value = mock_resource_manager
        mock_resource_manager.get_stack_resources.return_value = extended_resources
        mock_resource_manager.validate_retain_resources.return_value = ([], [])
        mock_resource_manager.categorize_resources.return_value = {
            'EC2 Instances': [' - EC2Instance1 (i-123)', ' - EC2Instance2 (i-456)'],
            'Networking': [' - VPC1', ' - SecurityGroup1', ' - InternetGateway1'],
            'IAM': [' - IAMRole1', ' - IAMPolicy1'],
            'Storage': [' - S3Bucket1', ' - EFSFileSystem1'],
            'Other': [' - Lambda1']
        }
        
        # Mock confirmation handler
        mock_confirmation_handler = Mock()
        mock_confirmation_handler_class.return_value = mock_confirmation_handler
        mock_confirmation_handler.confirm_deletion.return_value = True
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2'],
            input='y\n'
        )
        
        # Assertions for proper categorization
        assert result.exit_code == 0
        # Since we're mocking the utility classes, the actual output methods aren't called
        # We verify behavior through method calls instead of output text
        
        # Verify utility calls
        mock_resource_manager.get_stack_resources.assert_called_once_with('test-stack')
        mock_resource_manager.validate_retain_resources.assert_called_once_with([], extended_resources)
        mock_confirmation_handler.confirm_deletion.assert_called_once()
        mock_perform_deletion.assert_called_once_with('test-stack', 'us-west-2', [])

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.CloudFormationResourceManager')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.DeletionConfirmationHandler')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_retain_resources_parsing(self, mock_setup_logging, mock_perform_deletion, mock_confirmation_handler_class, mock_resource_manager_class):
        """Test proper parsing of retain-resources parameter."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        
        # Mock resource manager
        mock_resource_manager = Mock()
        mock_resource_manager_class.return_value = mock_resource_manager
        mock_resource_manager.get_stack_resources.return_value = self.sample_resources
        mock_resource_manager.validate_retain_resources.return_value = (['S3BucketStack', 'VPCStack', 'IAMRole1'], [])
        mock_resource_manager.categorize_resources.return_value = {
            'EC2 Instances': [' - EC2Instance1 (i-1234567890abcdef0)'],
            'Networking': [' - SecurityGroup1'],
            'IAM': [],
            'Storage': [],
            'Other': []
        }
        
        # Mock confirmation handler
        mock_confirmation_handler = Mock()
        mock_confirmation_handler_class.return_value = mock_confirmation_handler
        mock_confirmation_handler.confirm_deletion.return_value = True
        
        # Test with spaces and various formats
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--retain-resources', ' S3BucketStack , VPCStack , IAMRole1 ', '--region', 'us-west-2'],
            input='y\n'
        )
        
        # Assertions
        assert result.exit_code == 0
        
        # Verify proper parsing (spaces should be stripped)
        mock_resource_manager.validate_retain_resources.assert_called_once_with(['S3BucketStack', 'VPCStack', 'IAMRole1'], self.sample_resources)
        mock_perform_deletion.assert_called_once_with('test-stack', 'us-west-2', ['S3BucketStack', 'VPCStack', 'IAMRole1'])

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.CloudFormationResourceManager')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.DeletionConfirmationHandler')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_debug_logging(self, mock_setup_logging, mock_perform_deletion, mock_confirmation_handler_class, mock_resource_manager_class):
        """Test that debug logging is properly enabled."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        
        # Mock resource manager
        mock_resource_manager = Mock()
        mock_resource_manager_class.return_value = mock_resource_manager
        mock_resource_manager.get_stack_resources.return_value = self.sample_resources
        mock_resource_manager.validate_retain_resources.return_value = ([], [])
        mock_resource_manager.categorize_resources.return_value = {
            'EC2 Instances': [' - EC2Instance1 (i-1234567890abcdef0)'],
            'Networking': [' - SecurityGroup1'],
            'IAM': [' - IAMRole1'],
            'Storage': [],
            'Other': [' - VPCStack', ' - S3BucketStack']
        }
        
        # Mock confirmation handler
        mock_confirmation_handler = Mock()
        mock_confirmation_handler_class.return_value = mock_confirmation_handler
        mock_confirmation_handler.confirm_deletion.return_value = True
        
        # Execute command with debug flag
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2', '--debug'],
            input='y\n'
        )
        
        # Assertions
        assert result.exit_code == 0
        
        # Verify setup_logging was called with the logger
        mock_setup_logging.assert_called_once()
        
        # Verify utility calls
        mock_resource_manager.get_stack_resources.assert_called_once_with('test-stack')
        mock_confirmation_handler.confirm_deletion.assert_called_once()
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

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.CloudFormationResourceManager')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.DeletionConfirmationHandler')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.perform_stack_deletion')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_generic_error_handling(self, mock_setup_logging, mock_perform_deletion, mock_confirmation_handler_class, mock_resource_manager_class):
        """Test handling of generic/unexpected errors."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        
        # Mock resource manager
        mock_resource_manager = Mock()
        mock_resource_manager_class.return_value = mock_resource_manager
        mock_resource_manager.get_stack_resources.return_value = self.sample_resources
        mock_resource_manager.validate_retain_resources.return_value = ([], [])
        mock_resource_manager.categorize_resources.return_value = {
            'EC2 Instances': [' - EC2Instance1 (i-1234567890abcdef0)'],
            'Networking': [' - SecurityGroup1'],
            'IAM': [' - IAMRole1'],
            'Storage': [],
            'Other': [' - VPCStack', ' - S3BucketStack']
        }
        
        # Mock confirmation handler
        mock_confirmation_handler = Mock()
        mock_confirmation_handler_class.return_value = mock_confirmation_handler
        mock_confirmation_handler.confirm_deletion.return_value = True
        
        # Mock unexpected error
        mock_perform_deletion.side_effect = Exception("Unexpected error occurred")
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2'],
            input='y\n'
        )
        
        # Assertions
        assert result.exit_code == 1
        assert "❌ Error deleting stack: Unexpected error occurred" in result.output
        
        # Verify utility calls
        mock_resource_manager.get_stack_resources.assert_called_once_with('test-stack')
        mock_confirmation_handler.confirm_deletion.assert_called_once()
        mock_perform_deletion.assert_called_once_with('test-stack', 'us-west-2', [])


if __name__ == '__main__':
    pytest.main([__file__])
