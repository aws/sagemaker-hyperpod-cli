"""
Unit tests for cluster stack utility functions.
Tests the modular components for CloudFormation operations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import click
import logging
from botocore.exceptions import ClientError

from sagemaker.hyperpod.cli.cluster_stack_utils import (
    StackNotFoundError,
    delete_stack_with_confirmation,
    MessageCallback,
    ConfirmCallback,
    SuccessCallback
)
from sagemaker.hyperpod.cli.common_utils import (
    parse_comma_separated_list,
    categorize_resources_by_type
)


class TestStackDeletionWorkflow:
    """Test suite for the main stack deletion workflow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.region = 'us-west-2'
        self.stack_name = 'test-stack'
        
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
    def test_delete_stack_with_confirmation_success(self, mock_boto3_client):
        """Test successful stack deletion with confirmation."""
        mock_cf_client = Mock()
        mock_boto3_client.return_value = mock_cf_client
        mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': self.sample_resources
        }
        
        # Mock callbacks
        message_callback = Mock()
        confirm_callback = Mock(return_value=True)
        success_callback = Mock()
        
        delete_stack_with_confirmation(
            stack_name=self.stack_name,
            region=self.region,
            retain_resources_str="",
            message_callback=message_callback,
            confirm_callback=confirm_callback,
            success_callback=success_callback
        )
        
        # Verify CloudFormation calls
        mock_cf_client.list_stack_resources.assert_called_once_with(StackName=self.stack_name)
        mock_cf_client.delete_stack.assert_called_once_with(StackName=self.stack_name)
        
        # Verify callbacks were called
        assert message_callback.called
        assert confirm_callback.called
        assert success_callback.called

    @patch('boto3.client')
    def test_delete_stack_with_confirmation_cancelled(self, mock_boto3_client):
        """Test stack deletion cancelled by user."""
        mock_cf_client = Mock()
        mock_boto3_client.return_value = mock_cf_client
        mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': self.sample_resources
        }
        
        # Mock callbacks - user cancels
        message_callback = Mock()
        confirm_callback = Mock(return_value=False)
        success_callback = Mock()
        
        delete_stack_with_confirmation(
            stack_name=self.stack_name,
            region=self.region,
            retain_resources_str="",
            message_callback=message_callback,
            confirm_callback=confirm_callback,
            success_callback=success_callback
        )
        
        # Verify deletion was not called
        mock_cf_client.delete_stack.assert_not_called()
        
        # Verify cancellation message
        message_callback.assert_any_call("Operation cancelled.")
        assert not success_callback.called

    @patch('boto3.client')
    def test_delete_stack_with_confirmation_stack_not_found(self, mock_boto3_client):
        """Test handling when stack doesn't exist."""
        mock_cf_client = Mock()
        mock_boto3_client.return_value = mock_cf_client
        error = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack does not exist'}},
            'ListStackResources'
        )
        mock_cf_client.list_stack_resources.side_effect = error
        
        message_callback = Mock()
        confirm_callback = Mock()
        success_callback = Mock()
        
        with pytest.raises(StackNotFoundError):
            delete_stack_with_confirmation(
                stack_name=self.stack_name,
                region=self.region,
                retain_resources_str="",
                message_callback=message_callback,
                confirm_callback=confirm_callback,
                success_callback=success_callback
            )

    @patch('boto3.client')
    def test_delete_stack_with_retain_resources(self, mock_boto3_client):
        """Test stack deletion with resource retention."""
        mock_cf_client = Mock()
        mock_boto3_client.return_value = mock_cf_client
        mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': self.sample_resources
        }
        
        message_callback = Mock()
        confirm_callback = Mock(return_value=True)
        success_callback = Mock()
        
        delete_stack_with_confirmation(
            stack_name=self.stack_name,
            region=self.region,
            retain_resources_str="S3Bucket1,VPCStack",
            message_callback=message_callback,
            confirm_callback=confirm_callback,
            success_callback=success_callback
        )
        
        # Verify deletion was called with retention
        mock_cf_client.delete_stack.assert_called_once_with(
            StackName=self.stack_name,
            RetainResources=['S3Bucket1', 'VPCStack']
        )

    @patch('boto3.client')
    def test_delete_stack_with_invalid_retain_resources(self, mock_boto3_client):
        """Test handling of invalid retain resources."""
        mock_cf_client = Mock()
        mock_boto3_client.return_value = mock_cf_client
        mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': self.sample_resources
        }
        
        message_callback = Mock()
        confirm_callback = Mock(return_value=True)
        success_callback = Mock()
        
        delete_stack_with_confirmation(
            stack_name=self.stack_name,
            region=self.region,
            retain_resources_str="S3Bucket1,NonExistentResource",
            message_callback=message_callback,
            confirm_callback=confirm_callback,
            success_callback=success_callback
        )
        
        # Verify warning about invalid resources was displayed
        warning_calls = [call for call in message_callback.call_args_list 
                        if 'don\'t exist in the stack' in str(call)]
        assert len(warning_calls) > 0
        
        # Verify deletion was called with only valid resources
        mock_cf_client.delete_stack.assert_called_once_with(
            StackName=self.stack_name,
            RetainResources=['S3Bucket1']
        )

    @patch('boto3.client')
    def test_delete_stack_termination_protection_error(self, mock_boto3_client):
        """Test handling of termination protection error."""
        mock_cf_client = Mock()
        mock_boto3_client.return_value = mock_cf_client
        mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': self.sample_resources
        }
        
        # Mock termination protection error
        error = Exception("Stack cannot be deleted while TerminationProtection is enabled")
        mock_cf_client.delete_stack.side_effect = error
        
        message_callback = Mock()
        confirm_callback = Mock(return_value=True)
        success_callback = Mock()
        
        with pytest.raises(Exception):
            delete_stack_with_confirmation(
                stack_name=self.stack_name,
                region=self.region,
                retain_resources_str="",
                message_callback=message_callback,
                confirm_callback=confirm_callback,
                success_callback=success_callback
            )
        
        # Verify termination protection message was displayed
        protection_calls = [call for call in message_callback.call_args_list 
                           if 'Termination Protection is enabled' in str(call)]
        assert len(protection_calls) > 0

    @patch('boto3.client')
    def test_delete_stack_retention_limitation_error(self, mock_boto3_client):
        """Test handling of CloudFormation retention limitation error."""
        mock_cf_client = Mock()
        mock_boto3_client.return_value = mock_cf_client
        mock_cf_client.list_stack_resources.return_value = {
            'StackResourceSummaries': self.sample_resources
        }
        
        # Mock retention limitation error
        error = Exception("specify which resources to retain only when the stack is in the DELETE_FAILED state")
        mock_cf_client.delete_stack.side_effect = error
        
        message_callback = Mock()
        confirm_callback = Mock(return_value=True)
        success_callback = Mock()
        
        # Should raise exception
        with pytest.raises(Exception, match="specify which resources to retain only when the stack is in the DELETE_FAILED state"):
            delete_stack_with_confirmation(
                stack_name=self.stack_name,
                region=self.region,
                retain_resources_str="S3Bucket1",
                message_callback=message_callback,
                confirm_callback=confirm_callback,
                success_callback=success_callback
            )

    def test_delete_stack_with_logger(self):
        """Test stack deletion with logger parameter."""
        logger = Mock(spec=logging.Logger)
        message_callback = Mock()
        confirm_callback = Mock(return_value=False)  # Cancel to avoid actual deletion
        
        with patch('boto3.client') as mock_boto3_client:
            mock_cf_client = Mock()
            mock_boto3_client.return_value = mock_cf_client
            mock_cf_client.list_stack_resources.return_value = {
                'StackResourceSummaries': self.sample_resources
            }
            
            delete_stack_with_confirmation(
                stack_name=self.stack_name,
                region=self.region,
                retain_resources_str="",
                message_callback=message_callback,
                confirm_callback=confirm_callback,
                logger=logger
            )
            
            # Verify logger was used
            assert logger.info.called


class TestCallbackTypes:
    """Test suite for callback type definitions."""

    def test_message_callback_type(self):
        """Test MessageCallback type works correctly."""
        def test_callback(message: str) -> None:
            pass
        
        # Should not raise type errors
        callback: MessageCallback = test_callback
        callback("test message")

    def test_confirm_callback_type(self):
        """Test ConfirmCallback type works correctly."""
        def test_callback(message: str) -> bool:
            return True
        
        # Should not raise type errors
        callback: ConfirmCallback = test_callback
        result = callback("test message")
        assert result is True

    def test_success_callback_type(self):
        """Test SuccessCallback type works correctly."""
        def test_callback(message: str) -> None:
            pass
        
        # Should not raise type errors
        callback: SuccessCallback = test_callback
        callback("test message")


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


class TestStackNotFoundError:
    """Test suite for StackNotFoundError exception."""

    def test_stack_not_found_error_creation(self):
        """Test StackNotFoundError can be created and raised."""
        with pytest.raises(StackNotFoundError, match="Test stack not found"):
            raise StackNotFoundError("Test stack not found")

    def test_stack_not_found_error_inheritance(self):
        """Test StackNotFoundError inherits from Exception."""
        error = StackNotFoundError("Test error")
        assert isinstance(error, Exception)


if __name__ == '__main__':
    pytest.main([__file__])
