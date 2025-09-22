"""
Integration tests for CLI cluster stack deletion functionality.

Tests the basic happy path user workflow for deleting cluster stacks via CLI commands.
Focuses on core functionality with minimal stack creation/deletion overhead.

Detailed error handling and edge cases are covered by unit tests.
"""
import time
import pytest
import boto3
from click.testing import CliRunner

from sagemaker.hyperpod.cli.commands.cluster_stack import delete_cluster_stack
from test.integration_tests.cluster_management.utils import (
    assert_command_succeeded,
    assert_yes_no_prompt_displayed,
    assert_success_message_displayed,
)


# --------- Test Configuration ---------
REGION = "us-east-2"
TEST_STACK_PREFIX = "hyperpod-cli-delete-test"


@pytest.fixture(scope="module")
def runner():
    """Click test runner for CLI commands."""
    return CliRunner()


@pytest.fixture(scope="module")
def cfn_client():
    """CloudFormation client for test infrastructure."""
    return boto3.client('cloudformation', region_name=REGION)


def create_test_stack(cfn_client, stack_name):
    """Create a minimal test stack for deletion testing."""
    template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "Test stack for CLI deletion integration tests",
        "Resources": {
            "TestRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "RoleName": f"{stack_name}-test-role",
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
            {"Key": "Purpose", "Value": "IntegrationTest"},
            {"Key": "Component", "Value": "CLI-Delete-Test"}
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


# --------- CLI Delete Tests ---------

def test_delete_with_user_confirmation(runner, cfn_client):
    """Test CLI deletion happy path with user confirmation."""
    # Create a test stack for this test
    import uuid
    stack_name = f"{TEST_STACK_PREFIX}-happy-{str(uuid.uuid4())[:8]}"
    create_test_stack(cfn_client, stack_name)
    
    try:
        # Test deletion with confirmation prompt (simulate 'y' response)
        result = runner.invoke(delete_cluster_stack, [
            stack_name,
            "--region", REGION
        ], input='y\n', catch_exceptions=False)
        
        assert_command_succeeded(result)
        assert_yes_no_prompt_displayed(result)
        assert_success_message_displayed(result, ["deletion", "initiated"])
        
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
