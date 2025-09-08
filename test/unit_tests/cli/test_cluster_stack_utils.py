"""
Unit tests for cluster stack utility classes.
Tests the modular components for CloudFormation operations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import click
from botocore.exceptions import ClientError

from sagemaker.hyperpod.cli.cluster_stack_utils import (
    CloudFormationResourceManager,
    DeletionConfirmationHandler,
    CloudFormationErrorHandler,
    StackNotFoundError,
    parse_retain_resources,
    perform_stack_deletion
)
from sagemaker.hyperpod.cli.common_utils import (
    GenericConfirmationHandler,
    parse_comma_separated_list,
    categorize_resources_by_type
)


class TestCloudFormationResourceManager:
    """Test suite for CloudFormationResourceManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.region = 'us-west-2'
        self.mock_cf_client = Mock()
        
        # Sample resources for testing
        self.sample_resources = [
            {
                'LogicalResourceId': 'EC2Instance1',
                'ResourceType': 'AWS::EC2::Instance',
                'PhysicalResourceId': 'i-1234567890abcdef0'
            },
            {
                'LogicalResourceId': 'VPCStack',
                'ResourceType': 'AWS::EC2::VPC',
                'PhysicalResourceId': 'vpc-1234567890abcdef0'
            },
            {
                'LogicalResourceId': 'S3Bucket1',
                'ResourceType': 'AWS::S3::Bucket',
                'PhysicalResourceId': 's3-bucket-name'
            },
            {
                'LogicalResourceId': 'IAMRole1',
                'ResourceType': 'AWS::IAM::Role',
                'PhysicalResourceId': 'MyRole'
            }
        ]

    @patch('boto3.client')
    def test_get_stack_resources_success(self, mock_boto3_client):
        """Test successful retrieval of stack resources."""
        mock_boto3_client.return_value = self.mock_cf_client
        self.mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': self.sample_resources
        }
        
        manager = CloudFormationResourceManager(self.region)
        resources = manager.get_stack_resources('test-stack')
        
        assert resources == self.sample_resources
        self.mock_cf_client.list_stack_resources.assert_called_once_with(StackName='test-stack')

    @patch('boto3.client')
    def test_get_stack_resources_not_found(self, mock_boto3_client):
        """Test handling when stack doesn't exist."""
        mock_boto3_client.return_value = self.mock_cf_client
        error = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack does not exist'}},
            'ListStackResources'
        )
        self.mock_cf_client.list_stack_resources.side_effect = error
        
        manager = CloudFormationResourceManager(self.region)
        
        with pytest.raises(StackNotFoundError, match="Stack 'test-stack' not found"):
            manager.get_stack_resources('test-stack')

    def test_validate_retain_resources_valid(self):
        """Test validation of retain resources that exist in stack."""
        manager = CloudFormationResourceManager(self.region)
        retain_list = ['EC2Instance1', 'VPCStack']
        
        valid, invalid = manager.validate_retain_resources(retain_list, self.sample_resources)
        
        assert valid == ['EC2Instance1', 'VPCStack']
        assert invalid == []

    def test_validate_retain_resources_invalid(self):
        """Test validation of retain resources that don't exist in stack."""
        manager = CloudFormationResourceManager(self.region)
        retain_list = ['NonExistentResource', 'VPCStack', 'AnotherFakeResource']
        
        valid, invalid = manager.validate_retain_resources(retain_list, self.sample_resources)
        
        assert valid == ['VPCStack']
        assert invalid == ['NonExistentResource', 'AnotherFakeResource']

    def test_validate_retain_resources_empty(self):
        """Test validation with empty retain list."""
        manager = CloudFormationResourceManager(self.region)
        
        valid, invalid = manager.validate_retain_resources([], self.sample_resources)
        
        assert valid == []
        assert invalid == []

    def test_categorize_resources(self):
        """Test resource categorization by type."""
        manager = CloudFormationResourceManager(self.region)
        
        categories = manager.categorize_resources(self.sample_resources)
        
        assert 'EC2 Instances' in categories
        assert 'Networking' in categories
        assert 'IAM' in categories
        assert 'Storage' in categories
        assert len(categories['EC2 Instances']) == 1
        assert len(categories['Networking']) == 1
        assert len(categories['IAM']) == 1
        assert len(categories['Storage']) == 1

    def test_compare_resource_states(self):
        """Test comparison of resource states before and after deletion."""
        manager = CloudFormationResourceManager(self.region)
        
        # Simulate some resources being deleted
        current_resources = [
            {'LogicalResourceId': 'VPCStack'},
            {'LogicalResourceId': 'IAMRole1'}
        ]
        
        deleted, remaining = manager.compare_resource_states(self.sample_resources, current_resources)
        
        assert deleted == {'EC2Instance1', 'S3Bucket1'}
        assert remaining == {'VPCStack', 'IAMRole1'}


class TestDeletionConfirmationHandler:
    """Test suite for DeletionConfirmationHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = DeletionConfirmationHandler()

    def test_display_deletion_warning(self, capsys):
        """Test display of deletion warning."""
        resource_categories = {
            'EC2 Instances': ['Instance1'],
            'Networking': ['VPC1', 'SecurityGroup1'],
            'Storage': ['Bucket1']
        }
        
        self.handler.display_deletion_warning(resource_categories)
        
        captured = capsys.readouterr()
        assert "⚠ WARNING: This will delete the following 4 resources:" in captured.out
        assert "EC2 Instances (1):" in captured.out
        assert "Networking (2):" in captured.out
        assert "Storage (1):" in captured.out

    def test_display_retention_info(self, capsys):
        """Test display of retention information."""
        retained_resources = ['S3Bucket1', 'VPCStack']
        
        self.handler.display_retention_info(retained_resources)
        
        captured = capsys.readouterr()
        assert "The following 2 resources will be RETAINED:" in captured.out
        assert "✓ S3Bucket1 (retained)" in captured.out
        assert "✓ VPCStack (retained)" in captured.out

    def test_display_retention_info_empty(self, capsys):
        """Test display of retention info with empty list."""
        self.handler.display_retention_info([])
        
        captured = capsys.readouterr()
        assert captured.out == ""  # Should not display anything

    def test_display_invalid_resources_warning(self, capsys):
        """Test display of invalid resources warning."""
        invalid_resources = ['NonExistent1', 'NonExistent2']
        
        self.handler.display_invalid_resources_warning(invalid_resources)
        
        captured = capsys.readouterr()
        assert "⚠️  Warning: The following 2 resources don't exist in the stack:" in captured.out
        assert "- NonExistent1 (not found)" in captured.out
        assert "- NonExistent2 (not found)" in captured.out

    @patch('click.confirm')
    def test_confirm_deletion_yes(self, mock_confirm):
        """Test deletion confirmation when user says yes."""
        mock_confirm.return_value = True
        
        result = self.handler.confirm_deletion()
        
        assert result is True
        mock_confirm.assert_called_once_with("Continue?", default=False)

    @patch('click.confirm')
    def test_confirm_deletion_no(self, mock_confirm):
        """Test deletion confirmation when user says no."""
        mock_confirm.return_value = False
        
        result = self.handler.confirm_deletion()
        
        assert result is False
        mock_confirm.assert_called_once_with("Continue?", default=False)


class TestCloudFormationErrorHandler:
    """Test suite for CloudFormationErrorHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.region = 'us-west-2'
        self.mock_cf_client = Mock()

    @patch('boto3.client')
    def test_handle_termination_protection_error(self, mock_boto3_client, capsys):
        """Test handling of termination protection error."""
        mock_boto3_client.return_value = self.mock_cf_client
        handler = CloudFormationErrorHandler(self.region)
        
        error = Exception("Stack cannot be deleted while TerminationProtection is enabled")
        
        with pytest.raises(click.ClickException, match="Termination protection must be disabled"):
            handler.handle_deletion_error(error, 'test-stack')
        
        captured = capsys.readouterr()
        assert "❌ Stack deletion blocked: Termination Protection is enabled" in captured.out
        assert "aws cloudformation update-termination-protection" in captured.out

    @patch('boto3.client')
    def test_handle_retention_limitation_error(self, mock_boto3_client, capsys):
        """Test handling of CloudFormation retention limitation error."""
        mock_boto3_client.return_value = self.mock_cf_client
        handler = CloudFormationErrorHandler(self.region)
        
        error = Exception("specify which resources to retain only when the stack is in the DELETE_FAILED state")
        
        # Should not raise exception, just display message and return
        handler.handle_deletion_error(error, 'test-stack', 'S3Bucket1,VPC1')
        
        captured = capsys.readouterr()
        assert "❌ CloudFormation limitation: --retain-resources only works on failed deletions" in captured.out
        assert "💡 Recommended workflow:" in captured.out

    @patch('boto3.client')
    def test_handle_generic_error(self, mock_boto3_client, capsys):
        """Test handling of generic errors."""
        mock_boto3_client.return_value = self.mock_cf_client
        handler = CloudFormationErrorHandler(self.region)
        
        error = Exception("Some generic error")
        
        with pytest.raises(click.ClickException, match="Some generic error"):
            handler.handle_deletion_error(error, 'test-stack')
        
        captured = capsys.readouterr()
        assert "❌ Error deleting stack: Some generic error" in captured.out

    @patch('boto3.client')
    def test_handle_partial_deletion_failure(self, mock_boto3_client, capsys):
        """Test handling of partial deletion failures."""
        mock_boto3_client.return_value = self.mock_cf_client
        handler = CloudFormationErrorHandler(self.region)
        
        original_resources = [
            {'LogicalResourceId': 'Resource1'},
            {'LogicalResourceId': 'Resource2'},
            {'LogicalResourceId': 'Resource3'}
        ]
        
        # Mock current resources after partial deletion
        self.mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': [
                {'LogicalResourceId': 'Resource2'},
                {'LogicalResourceId': 'Resource3'}
            ]
        }
        
        handler.handle_partial_deletion_failure('test-stack', original_resources, [])
        
        captured = capsys.readouterr()
        assert "✗ Stack deletion failed" in captured.out
        assert "Successfully deleted (1):" in captured.out
        assert "✓ Resource1" in captured.out
        assert "Failed to delete (2):" in captured.out
        assert "✗ Resource2" in captured.out
        assert "✗ Resource3" in captured.out


class TestUtilityFunctions:
    """Test suite for utility functions."""

    def test_parse_retain_resources_valid(self):
        """Test parsing of valid retain resources string."""
        result = parse_retain_resources("Resource1,Resource2,Resource3")
        assert result == ['Resource1', 'Resource2', 'Resource3']

    def test_parse_retain_resources_with_spaces(self):
        """Test parsing with spaces around resource names."""
        result = parse_retain_resources(" Resource1 , Resource2 , Resource3 ")
        assert result == ['Resource1', 'Resource2', 'Resource3']

    def test_parse_retain_resources_empty(self):
        """Test parsing of empty or None string."""
        assert parse_retain_resources(None) == []
        assert parse_retain_resources("") == []
        assert parse_retain_resources("   ") == []

    def test_parse_retain_resources_single(self):
        """Test parsing of single resource."""
        result = parse_retain_resources("SingleResource")
        assert result == ['SingleResource']

    @patch('boto3.client')
    @patch('click.echo')
    def test_perform_stack_deletion_success(self, mock_echo, mock_boto3_client):
        """Test successful stack deletion."""
        mock_cf_client = Mock()
        mock_boto3_client.return_value = mock_cf_client
        
        perform_stack_deletion('test-stack', 'us-west-2', [])
        
        mock_cf_client.delete_stack.assert_called_once_with(StackName='test-stack')
        mock_echo.assert_called_with("✓ Stack 'test-stack' deletion initiated successfully")

    @patch('boto3.client')
    @patch('click.echo')
    def test_perform_stack_deletion_with_retention(self, mock_echo, mock_boto3_client):
        """Test stack deletion with resource retention."""
        mock_cf_client = Mock()
        mock_boto3_client.return_value = mock_cf_client
        retain_list = ['Resource1', 'Resource2']
        
        perform_stack_deletion('test-stack', 'us-west-2', retain_list)
        
        mock_cf_client.delete_stack.assert_called_once_with(
            StackName='test-stack',
            RetainResources=retain_list
        )
        
        # Verify success message was displayed
        success_calls = [call for call in mock_echo.call_args_list if 'deletion initiated successfully' in str(call)]
        assert len(success_calls) == 1


class TestGenericUtilities:
    """Test suite for generic utilities from common_utils."""

    def test_parse_comma_separated_list(self):
        """Test parsing comma-separated lists."""
        # Test normal case
        result = parse_comma_separated_list("item1,item2,item3")
        assert result == ["item1", "item2", "item3"]
        
        # Test with spaces
        result = parse_comma_separated_list("item1, item2 , item3")
        assert result == ["item1", "item2", "item3"]
        
        # Test empty string
        result = parse_comma_separated_list("")
        assert result == []
        
        # Test None
        result = parse_comma_separated_list(None)
        assert result == []
    
    def test_categorize_resources_by_type(self):
        """Test generic resource categorization."""
        resources = [
            {"ResourceType": "AWS::EC2::Instance", "LogicalResourceId": "MyInstance"},
            {"ResourceType": "AWS::S3::Bucket", "LogicalResourceId": "MyBucket"},
            {"ResourceType": "AWS::Lambda::Function", "LogicalResourceId": "MyFunction"}
        ]
        
        type_mappings = {
            "Compute": ["AWS::EC2::Instance", "AWS::Lambda::Function"],
            "Storage": ["AWS::S3::Bucket"]
        }
        
        result = categorize_resources_by_type(resources, type_mappings)
        
        assert result == {
            "Compute": ["MyInstance", "MyFunction"],
            "Storage": ["MyBucket"]
        }
    
    def test_generic_confirmation_handler(self, capsys):
        """Test generic confirmation handler."""
        handler = GenericConfirmationHandler()
        
        # Test display_warning_list
        items = {"Category1": ["item1", "item2"], "Category2": ["item3"]}
        handler.display_warning_list("Test warning", items)
        captured = capsys.readouterr()
        
        assert "⚠ Test warning 3 resources:" in captured.out
        assert "Category1 (2):" in captured.out
        assert " - item1" in captured.out


if __name__ == '__main__':
    pytest.main([__file__])
