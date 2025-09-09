"""
Integration tests for SDK cluster stack deletion functionality.

Tests the HpClusterStack.delete() method and related SDK functionality.
Focuses on programmatic usage patterns and error handling.
"""
import time
import pytest
import boto3
import uuid
from unittest.mock import patch, MagicMock

from sagemaker.hyperpod.cluster_management.hp_cluster_stack import HpClusterStack


# --------- Test Configuration ---------
REGION = "us-east-2"
TEST_STACK_PREFIX = "hyperpod-sdk-delete-test"


@pytest.fixture(scope="module")
def cfn_client():
    """CloudFormation client for test infrastructure."""
    return boto3.client('cloudformation', region_name=REGION)


def create_test_stack(cfn_client, stack_name):
    """Create a minimal test stack for deletion testing."""
    template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "Test stack for SDK deletion integration tests",
        "Resources": {
            "TestBucket": {
                "Type": "AWS::S3::Bucket",
                "Properties": {
                    "BucketName": f"{stack_name.lower()}-sdk-test-bucket"
                }
            },
            "TestParameter": {
                "Type": "AWS::SSM::Parameter",
                "Properties": {
                    "Name": f"/test/{stack_name}/parameter",
                    "Type": "String",
                    "Value": "test-value"
                }
            }
        },
        "Outputs": {
            "BucketName": {
                "Description": "Name of the test bucket",
                "Value": {"Ref": "TestBucket"}
            }
        }
    }
    
    import json
    cfn_client.create_stack(
        StackName=stack_name,
        TemplateBody=json.dumps(template),
        Tags=[
            {"Key": "Purpose", "Value": "SDKIntegrationTest"},
            {"Key": "Component", "Value": "SDK-Delete-Test"}
        ]
    )
    
    # Wait for stack creation to complete
    waiter = cfn_client.get_waiter('stack_create_complete')
    waiter.wait(StackName=stack_name, WaiterConfig={'Delay': 10, 'MaxAttempts': 30})


def wait_for_stack_delete_complete(cfn_client, stack_name, timeout_minutes=10):
    """Wait for stack deletion to complete."""
    try:
        waiter = cfn_client.get_waiter('stack_delete_complete')
        waiter.wait(
            StackName=stack_name,
            WaiterConfig={'Delay': 15, 'MaxAttempts': timeout_minutes * 4}
        )
        return True
    except Exception as e:
        if "does not exist" in str(e):
            return True  # Stack was deleted
        raise


# --------- SDK Delete Tests ---------

@pytest.mark.dependency(name="test_sdk_delete_nonexistent_stack")
def test_sdk_delete_nonexistent_stack_error_handling():
    """Test SDK error handling when trying to delete a non-existent stack."""
    nonexistent_stack = f"nonexistent-stack-{str(uuid.uuid4())[:8]}"
    
    # Should raise ValueError with helpful message
    with pytest.raises(ValueError) as exc_info:
        HpClusterStack.delete(
            stack_name=nonexistent_stack,
            region=REGION
        )
    
    error_message = str(exc_info.value).lower()
    assert "not found" in error_message or "does not exist" in error_message
    assert nonexistent_stack in str(exc_info.value)


@pytest.mark.dependency(name="test_sdk_delete_basic_functionality")
def test_sdk_delete_basic_functionality(cfn_client):
    """Test basic SDK deletion functionality with auto-confirmation."""
    # Create test stack
    stack_name = f"{TEST_STACK_PREFIX}-basic-{str(uuid.uuid4())[:8]}"
    create_test_stack(cfn_client, stack_name)
    
    try:
        # Delete using SDK (should auto-confirm)
        HpClusterStack.delete(
            stack_name=stack_name,
            region=REGION
        )
        
        # Wait for deletion to complete
        wait_for_stack_delete_complete(cfn_client, stack_name)
        
        # Verify stack is deleted
        with pytest.raises(Exception) as exc_info:
            cfn_client.describe_stacks(StackName=stack_name)
        assert "does not exist" in str(exc_info.value)
        
    except Exception:
        # Cleanup in case of test failure
        try:
            cfn_client.delete_stack(StackName=stack_name)
        except:
            pass
        raise


@pytest.mark.dependency(name="test_sdk_delete_with_region_parameter")
def test_sdk_delete_with_region_parameter(cfn_client):
    """Test SDK deletion with explicit region parameter."""
    # Create test stack
    stack_name = f"{TEST_STACK_PREFIX}-region-{str(uuid.uuid4())[:8]}"
    create_test_stack(cfn_client, stack_name)
    
    try:
        # Delete using SDK with explicit region
        HpClusterStack.delete(
            stack_name=stack_name,
            region=REGION
        )
        
        # Wait for deletion to complete
        wait_for_stack_delete_complete(cfn_client, stack_name)
        
        # Verify stack is deleted
        with pytest.raises(Exception) as exc_info:
            cfn_client.describe_stacks(StackName=stack_name)
        assert "does not exist" in str(exc_info.value)
        
    except Exception:
        # Cleanup in case of test failure
        try:
            cfn_client.delete_stack(StackName=stack_name)
        except:
            pass
        raise


@pytest.mark.dependency(name="test_sdk_retain_resources_validation")
def test_sdk_retain_resources_validation_error(cfn_client):
    """Test SDK validation of retain_resources parameter on non-DELETE_FAILED stack."""
    # Create test stack in CREATE_COMPLETE state
    stack_name = f"{TEST_STACK_PREFIX}-retain-{str(uuid.uuid4())[:8]}"
    create_test_stack(cfn_client, stack_name)
    
    try:
        # Try to delete with retain_resources (should raise ValueError)
        with pytest.raises(ValueError) as exc_info:
            HpClusterStack.delete(
                stack_name=stack_name,
                region=REGION,
                retain_resources=["TestBucket"]
            )
        
        # Should have helpful error about retain_resources limitation
        error_message = str(exc_info.value).lower()
        assert "retain" in error_message
        assert "delete_failed" in error_message
        assert "can only be used" in error_message or "only supported" in error_message or "only works" in error_message
        
        # Verify stack still exists (deletion should not have been attempted)
        response = cfn_client.describe_stacks(StackName=stack_name)
        assert len(response['Stacks']) == 1
        assert response['Stacks'][0]['StackStatus'] == 'CREATE_COMPLETE'
        
    finally:
        # Cleanup
        try:
            cfn_client.delete_stack(StackName=stack_name)
            wait_for_stack_delete_complete(cfn_client, stack_name)
        except:
            pass


@pytest.mark.dependency(name="test_sdk_delete_with_logging")
def test_sdk_delete_with_custom_logger(cfn_client):
    """Test SDK deletion with custom logger parameter."""
    import logging
    from io import StringIO
    
    # Create test stack
    stack_name = f"{TEST_STACK_PREFIX}-logger-{str(uuid.uuid4())[:8]}"
    create_test_stack(cfn_client, stack_name)
    
    # Set up custom logger to capture log messages
    log_stream = StringIO()
    logger = logging.getLogger(f"test_logger_{uuid.uuid4().hex[:8]}")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(log_stream)
    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(handler)
    
    try:
        # Delete using SDK with custom logger
        HpClusterStack.delete(
            stack_name=stack_name,
            region=REGION,
            logger=logger
        )
        
        # Check that logger captured relevant messages
        log_output = log_stream.getvalue()
        assert "auto-confirming" in log_output.lower() or "deletion" in log_output.lower()
        
        # Wait for deletion to complete
        wait_for_stack_delete_complete(cfn_client, stack_name)
        
        # Verify stack is deleted
        with pytest.raises(Exception) as exc_info:
            cfn_client.describe_stacks(StackName=stack_name)
        assert "does not exist" in str(exc_info.value)
        
    except Exception:
        # Cleanup in case of test failure
        try:
            cfn_client.delete_stack(StackName=stack_name)
        except:
            pass
        raise
    finally:
        # Clean up logger
        logger.removeHandler(handler)
        handler.close()
