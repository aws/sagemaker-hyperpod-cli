"""
Integration tests for SDK cluster stack deletion functionality.

Tests the basic happy path for HpClusterStack.delete() method.
Focuses on core SDK functionality with minimal stack creation/deletion overhead.

Detailed error handling and edge cases are covered by unit tests.
"""
import time
import pytest
import boto3
import uuid

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
            "TestRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "RoleName": f"{stack_name}-sdk-test-role",
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"Service": "lambda.amazonaws.com"},
                                "Action": "sts:AssumeRole"
                            }
                        ]
                    }
                }
            }
        },
        "Outputs": {
            "RoleName": {
                "Description": "Name of the test role",
                "Value": {"Ref": "TestRole"}
            }
        }
    }
    
    import json
    cfn_client.create_stack(
        StackName=stack_name,
        TemplateBody=json.dumps(template),
        Capabilities=['CAPABILITY_NAMED_IAM'],
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
