"""
Integration tests for CLI cluster stack deletion functionality.

Tests the complete user workflow for deleting cluster stacks via CLI commands.
Uses CLI commands as a user would, focusing on deletion process and error handling.
"""
import time
import pytest
import boto3
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from sagemaker.hyperpod.cli.commands.cluster_stack import delete_cluster_stack
from test.integration_tests.cluster_management.utils import (
    assert_command_succeeded,
    assert_command_failed_with_helpful_error,
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
def test_stack_name():
    """Generate a unique test stack name."""
    import uuid
    return f"{TEST_STACK_PREFIX}-{str(uuid.uuid4())[:8]}"


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
            "TestBucket": {
                "Type": "AWS::S3::Bucket",
                "Properties": {
                    "BucketName": f"{stack_name.lower()}-test-bucket"
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

@pytest.mark.dependency(name="test_delete_nonexistent_stack")
def test_delete_nonexistent_stack_error_handling(runner):
    """Test CLI error handling when trying to delete a non-existent stack."""
    nonexistent_stack = "nonexistent-stack-12345"
    
    result = runner.invoke(delete_cluster_stack, [
        nonexistent_stack,
        "--region", REGION
    ], input='y\n', catch_exceptions=False)
    
    # CLI shows user-friendly error message but doesn't fail with non-zero exit code
    assert "not found" in result.output.lower()
    assert nonexistent_stack in result.output


@pytest.mark.dependency(name="test_delete_with_confirmation_prompt")
def test_delete_with_confirmation_prompt(runner, test_stack_name, cfn_client):
    """Test CLI deletion with user confirmation prompt."""
    # Create test stack
    create_test_stack(cfn_client, test_stack_name)
    
    # Test deletion with confirmation prompt (simulate 'n' response)
    result = runner.invoke(delete_cluster_stack, [
        test_stack_name,
        "--region", REGION
    ], input='n\n', catch_exceptions=False)
    
    # Should show confirmation prompt and abort on 'n'
    assert_yes_no_prompt_displayed(result)
    assert "Aborted" in result.output or "cancelled" in result.output.lower()
    
    # Verify stack still exists
    response = cfn_client.describe_stacks(StackName=test_stack_name)
    assert len(response['Stacks']) == 1
    assert response['Stacks'][0]['StackStatus'] != 'DELETE_COMPLETE'


@pytest.mark.dependency(name="test_delete_with_user_confirmation_yes", depends=["test_delete_with_confirmation_prompt"])
def test_delete_with_user_confirmation_yes(runner, test_stack_name, cfn_client):
    """Test CLI deletion with user confirmation (yes response)."""
    result = runner.invoke(delete_cluster_stack, [
        test_stack_name,
        "--region", REGION
    ], input='y\n', catch_exceptions=False)
    
    assert_command_succeeded(result)
    assert_success_message_displayed(result, ["deletion", "initiated"])
    
    # Wait for deletion to complete
    wait_for_stack_delete_complete(cfn_client, test_stack_name)
    
    # Verify stack is deleted
    with pytest.raises(Exception) as exc_info:
        cfn_client.describe_stacks(StackName=test_stack_name)
    assert "does not exist" in str(exc_info.value)


@pytest.mark.dependency(name="test_delete_with_user_confirmation")
def test_delete_with_user_confirmation(runner, cfn_client):
    """Test CLI deletion with user confirmation (yes response)."""
    # Create a new test stack for this test
    import uuid
    stack_name = f"{TEST_STACK_PREFIX}-confirm-{str(uuid.uuid4())[:8]}"
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


@pytest.mark.dependency(name="test_retain_resources_validation")
def test_retain_resources_validation_error(runner, cfn_client):
    """Test CLI validation of retain-resources parameter on non-DELETE_FAILED stack."""
    # Create a test stack in CREATE_COMPLETE state
    import uuid
    stack_name = f"{TEST_STACK_PREFIX}-retain-{str(uuid.uuid4())[:8]}"
    create_test_stack(cfn_client, stack_name)
    
    try:
        # Try to delete with retain-resources (should fail validation)
        result = runner.invoke(delete_cluster_stack, [
            stack_name,
            "--region", REGION,
            "--retain-resources", "TestBucket"
        ], input='y\n', catch_exceptions=False)
        
        # Should fail with helpful error about retain-resources limitation
        assert result.exit_code != 0
        assert "retain" in result.output.lower()
        assert "only works on failed deletions" in result.output or "DELETE_FAILED" in result.output
        
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


@pytest.mark.dependency(name="test_region_parameter")
def test_region_parameter_handling(runner):
    """Test CLI handling of region parameter."""
    nonexistent_stack = "test-stack-region-param"
    
    # Test with explicit region
    result = runner.invoke(delete_cluster_stack, [
        nonexistent_stack,
        "--region", "us-west-1"
    ], input='y\n', catch_exceptions=False)
    
    # CLI shows user-friendly error message for non-existent stack
    assert "not found" in result.output.lower() or "does not exist" in result.output.lower()
    assert nonexistent_stack in result.output
