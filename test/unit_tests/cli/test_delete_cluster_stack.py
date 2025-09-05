"""
Unit tests for delete cluster-stack command implementation.
Tests all possible scenarios including success, failures, and edge cases.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
import json

from sagemaker.hyperpod.cli.commands.cluster_stack import delete_cluster_stack


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

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.create_boto3_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_successful_deletion_without_retention(self, mock_setup_logging, mock_create_client):
        """Test successful stack deletion without resource retention."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_create_client.return_value = self.mock_cf_client
        
        self.mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': self.sample_resources
        }
        self.mock_cf_client.delete_stack.return_value = {}
        
        # Execute command with 'y' input for confirmation
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2', '--debug'],
            input='y\n'
        )
        
        # Assertions
        assert result.exit_code == 0
        assert "⚠ WARNING: This will delete the following 5 resources:" in result.output
        assert "EC2 Instances (1):" in result.output
        assert "Networking (1):" in result.output
        assert "IAM (1):" in result.output
        assert "Other (2):" in result.output
        assert "✓ Stack 'test-stack' deletion initiated successfully" in result.output
        
        # Verify CloudFormation calls
        self.mock_cf_client.list_stack_resources.assert_called_once_with(StackName='test-stack')
        self.mock_cf_client.delete_stack.assert_called_once_with(StackName='test-stack')

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.create_boto3_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_successful_deletion_with_retention(self, mock_setup_logging, mock_create_client):
        """Test successful stack deletion with resource retention."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_create_client.return_value = self.mock_cf_client
        
        self.mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': self.sample_resources
        }
        self.mock_cf_client.delete_stack.return_value = {}
        
        # Execute command with retention
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--retain-resources', 'S3BucketStack,VPCStack', '--region', 'us-west-2'],
            input='y\n'
        )
        
        # Assertions
        assert result.exit_code == 0
        assert "The following 2 resources will be RETAINED:" in result.output
        assert "✓ S3BucketStack (retained)" in result.output
        assert "✓ VPCStack (retained)" in result.output
        assert "Successfully retained as requested (2):" in result.output
        assert "💡 Retained resources will remain as standalone AWS resources" in result.output
        
        # Verify CloudFormation calls with retention
        self.mock_cf_client.delete_stack.assert_called_once_with(
            StackName='test-stack',
            RetainResources=['S3BucketStack', 'VPCStack']
        )

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.create_boto3_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_user_cancellation(self, mock_setup_logging, mock_create_client):
        """Test user cancelling the deletion operation."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_create_client.return_value = self.mock_cf_client
        
        self.mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': self.sample_resources
        }
        
        # Execute command with 'n' input for cancellation
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2'],
            input='n\n'
        )
        
        # Assertions
        assert result.exit_code == 0
        assert "Operation cancelled." in result.output
        
        # Verify CloudFormation delete was not called
        self.mock_cf_client.delete_stack.assert_not_called()

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.create_boto3_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_stack_not_found(self, mock_setup_logging, mock_create_client):
        """Test handling when stack doesn't exist."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_create_client.return_value = self.mock_cf_client
        
        # Mock stack not found error
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack does not exist'}},
            'ListStackResources'
        )
        self.mock_cf_client.list_stack_resources.side_effect = error
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['non-existent-stack', '--region', 'us-west-2']
        )
        
        # Assertions
        assert result.exit_code == 0
        assert "❌ Stack 'non-existent-stack' not found" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.create_boto3_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_termination_protection_enabled(self, mock_setup_logging, mock_create_client):
        """Test handling when stack has termination protection enabled."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_create_client.return_value = self.mock_cf_client
        
        self.mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': self.sample_resources
        }
        
        # Mock termination protection error
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack cannot be deleted while TerminationProtection is enabled'}},
            'DeleteStack'
        )
        self.mock_cf_client.delete_stack.side_effect = error
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['protected-stack', '--region', 'us-west-2'],
            input='y\n'
        )
        
        # Assertions
        assert result.exit_code == 1
        assert "❌ Stack deletion blocked: Termination Protection is enabled" in result.output
        assert "aws cloudformation update-termination-protection --no-enable-termination-protection" in result.output
        assert "Then retry the delete command." in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.create_boto3_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_cloudformation_retention_limitation(self, mock_setup_logging, mock_create_client):
        """Test handling CloudFormation's retain-resources limitation."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_create_client.return_value = self.mock_cf_client
        
        self.mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': self.sample_resources
        }
        
        # Mock CloudFormation retention limitation error
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'specify which resources to retain only when the stack is in the DELETE_FAILED state'}},
            'DeleteStack'
        )
        self.mock_cf_client.delete_stack.side_effect = error
        
        # Execute command with retention
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--retain-resources', 'S3BucketStack', '--region', 'us-west-2'],
            input='y\n'
        )
        
        # Assertions - Now exits gracefully with code 0
        assert result.exit_code == 0
        assert "❌ CloudFormation limitation: --retain-resources only works on failed deletions" in result.output
        assert "💡 Recommended workflow:" in result.output
        assert "1. First try deleting without --retain-resources:" in result.output
        assert "2. If deletion fails, the stack will be in DELETE_FAILED state" in result.output
        assert "3. Then retry with --retain-resources to keep specific resources:" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.create_boto3_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_partial_deletion_failure(self, mock_setup_logging, mock_create_client):
        """Test handling partial deletion failures with dependency violations."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_create_client.return_value = self.mock_cf_client
        
        self.mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': self.sample_resources
        }
        
        # Mock partial deletion failure
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Resource has dependencies'}},
            'DeleteStack'
        )
        self.mock_cf_client.delete_stack.side_effect = error
        
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
        
        # First call returns original resources, second call returns remaining resources
        self.mock_cf_client.list_stack_resources.side_effect = [
            {'StackResourceSummaries': self.sample_resources},
            {'StackResourceSummaries': remaining_resources}
        ]
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2'],
            input='y\n'
        )
        
        # Assertions
        assert result.exit_code == 1
        assert "✗ Stack deletion failed" in result.output
        assert "Successfully deleted (3):" in result.output
        assert "Failed to delete (2):" in result.output
        assert "💡 Note: Some resources may have dependencies preventing deletion" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.create_boto3_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_access_denied_error(self, mock_setup_logging, mock_create_client):
        """Test handling access denied errors."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_create_client.return_value = self.mock_cf_client
        
        # Mock access denied error
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'ListStackResources'
        )
        self.mock_cf_client.list_stack_resources.side_effect = error
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2']
        )
        
        # Assertions - Now exits gracefully with code 0
        assert result.exit_code == 0
        assert "❌ Access denied. Check AWS permissions" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.create_boto3_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_empty_stack_resources(self, mock_setup_logging, mock_create_client):
        """Test handling when stack has no resources."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_create_client.return_value = self.mock_cf_client
        
        self.mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': []
        }
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['empty-stack', '--region', 'us-west-2']
        )
        
        # Assertions
        assert result.exit_code == 0
        assert "❌ No resources found in stack 'empty-stack'" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.create_boto3_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_resource_categorization(self, mock_setup_logging, mock_create_client):
        """Test proper categorization of different resource types."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_create_client.return_value = self.mock_cf_client
        
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
        
        self.mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': extended_resources
        }
        self.mock_cf_client.delete_stack.return_value = {}
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2'],
            input='y\n'
        )
        
        # Assertions for proper categorization
        assert result.exit_code == 0
        assert "EC2 Instances (2):" in result.output
        assert "Networking (3):" in result.output
        assert "IAM (2):" in result.output
        assert "Storage (2):" in result.output
        assert "Other (1):" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.create_boto3_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_retain_resources_parsing(self, mock_setup_logging, mock_create_client):
        """Test proper parsing of retain-resources parameter."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_create_client.return_value = self.mock_cf_client
        
        self.mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': self.sample_resources
        }
        self.mock_cf_client.delete_stack.return_value = {}
        
        # Test with spaces and various formats
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--retain-resources', ' S3BucketStack , VPCStack , IAMRole1 ', '--region', 'us-west-2'],
            input='y\n'
        )
        
        # Assertions
        assert result.exit_code == 0
        assert "The following 3 resources will be RETAINED:" in result.output
        
        # Verify proper parsing (spaces should be stripped)
        self.mock_cf_client.delete_stack.assert_called_once_with(
            StackName='test-stack',
            RetainResources=['S3BucketStack', 'VPCStack', 'IAMRole1']
        )

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.create_boto3_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_debug_logging(self, mock_setup_logging, mock_create_client):
        """Test that debug logging is properly enabled."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_create_client.return_value = self.mock_cf_client
        
        self.mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': self.sample_resources
        }
        self.mock_cf_client.delete_stack.return_value = {}
        
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

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.create_boto3_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_generic_error_handling(self, mock_setup_logging, mock_create_client):
        """Test handling of generic/unexpected errors."""
        # Setup mocks
        mock_setup_logging.return_value = self.mock_logger
        mock_create_client.return_value = self.mock_cf_client
        
        self.mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': self.sample_resources
        }
        
        # Mock unexpected error
        self.mock_cf_client.delete_stack.side_effect = Exception("Unexpected error occurred")
        
        # Execute command
        result = self.runner.invoke(
            delete_cluster_stack,
            ['test-stack', '--region', 'us-west-2'],
            input='y\n'
        )
        
        # Assertions
        assert result.exit_code == 1
        assert "❌ Error deleting stack: Unexpected error occurred" in result.output


if __name__ == '__main__':
    pytest.main([__file__])