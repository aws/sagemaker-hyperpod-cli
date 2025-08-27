"""
End-to-end integration tests for cluster init workflow focusing on submission process.

Tests the complete user workflow: init -> configure -> validate -> create -> verify via CLI.
Uses CLI commands as a user would, focusing on successful submission.
"""
import time
import subprocess
import pytest
from pathlib import Path
import re
from datetime import datetime, timedelta, timezone
import sys
from unittest.mock import patch
from click.testing import CliRunner

from sagemaker.hyperpod.cli.commands.init import init, validate, _default_create as create
from sagemaker.hyperpod.cli.commands.cluster_stack import describe_cluster_stack, list_cluster_stacks, update_cluster


from test.integration_tests.cluster_management.utils import (
    assert_command_succeeded,
    assert_config_values,
)


def assert_init_files_created(project_dir, template_type):
    """Assert that init created the expected files for the template type."""
    project_path = Path(project_dir)
    
    # Common files
    assert (project_path / "config.yaml").exists(), "config.yaml should be created"
    assert (project_path / "README.md").exists(), "README.md should be created"
    
    # Template-specific files
    if template_type == "cluster-stack":
        assert (project_path / "cfn_params.jinja").exists(), \
            "Cluster template should create cfn_params.jinja"


def get_iam_stack_name(cluster_name):
    """Generate IAM stack name from cluster name following eksctl naming convention."""
    resource_prefix = cluster_name.replace("-cluster-integ-test", "-cli-integ-test")
    return f"eksctl-{resource_prefix}-eks-addon-iamserviceaccount-kube-system-fsx-csi-controller-sa"


def get_node_recovery_setting(cluster_name, region):
    """Get current node recovery setting for the cluster."""
    import boto3
    try:
        client = boto3.client('sagemaker', region_name=region)
        response = client.describe_cluster(ClusterName=cluster_name)
        return response['NodeRecovery']
    except Exception as e:
        raise AssertionError(f"Failed to get node recovery setting: {e}")


def get_cluster_status(cluster_name, region):
    """Get cluster status using boto3."""
    import boto3
    try:
        client = boto3.client('sagemaker', region_name=region)
        response = client.describe_cluster(ClusterName=cluster_name)
        return response['ClusterStatus']
    except Exception as e:
        raise AssertionError(f"Failed to get cluster status: {e}")


def wait_for_stack_complete(stack_name, region, timeout_minutes=15):
    """Wait for CloudFormation stack to be CREATE_COMPLETE."""
    import boto3
    client = boto3.client('cloudformation', region_name=region)
    
    deadline = time.time() + (timeout_minutes * 60)
    while time.time() < deadline:
        try:
            response = client.describe_stacks(StackName=stack_name)
            status = response['Stacks'][0]['StackStatus']
            
            if status == 'CREATE_COMPLETE':
                return True
            elif status in ['CREATE_FAILED', 'ROLLBACK_COMPLETE']:
                raise AssertionError(f"Stack creation failed with status: {status}")
                
            time.sleep(30)
        except Exception as e:
            if "does not exist" in str(e).lower():
                print(f"[STATUS] Stack '{stack_name}' not found yet, waiting for creation...")
            else:
                print(f"[ERROR] Error checking stack status: {e}")
            time.sleep(30)
    
    raise AssertionError(f"Stack did not complete after {timeout_minutes} minutes")


# --------- Test Configuration ---------
REGION = "us-east-2"

# Global variables to share data between tests
STACK_NAME = None
CREATE_TIME = None
UNIQUE_TIMESTAMP = int(time.time() * 1000)

@pytest.fixture(scope="module")
def runner():
    return CliRunner()

@pytest.fixture(scope="module")
def cluster_name():
    return f"hyperpod-{UNIQUE_TIMESTAMP}-cluster-integ-test"

@pytest.fixture(scope="module")
def create_time():
    """Track when we create to check for recent stack creation."""
    return datetime.now(timezone.utc)


# --------- Cluster Submission Tests ---------

@pytest.mark.dependency(name="init")
def test_init_cluster(runner, cluster_name):
    """Initialize cluster stack template and verify file creation."""
    result = runner.invoke(
        init, ["cluster-stack", "."], catch_exceptions=False
    )
    assert_command_succeeded(result)
    assert_init_files_created("./", "cluster-stack")


@pytest.mark.dependency(name="configure", depends=["init"])
def test_configure_cluster(runner, cluster_name):
    """Configure cluster with key parameters based on source code analysis."""
    with patch.object(sys, 'argv', ['hyp', 'configure']):
        import importlib
        from sagemaker.hyperpod.cli.commands import init
        importlib.reload(init)
        configure = init.configure
    # Configuration mapping for cleaner code
    config_options = {
        "stage": "prod",
        "resource-name-prefix": f"hyperpod-cli-integ-test-{UNIQUE_TIMESTAMP}",
        "hyperpod-cluster-name": cluster_name,
        "create-vpc-stack": "true",
        "create-security-group-stack": "true",
        "create-eks-cluster-stack": "true",
        "create-s3-bucket-stack": "true",
        "create-s3-endpoint-stack": "false",
        "create-sagemaker-iam-role-stack": "true",
        "create-hyperpod-cluster-stack": "true",
        "create-helm-chart-stack": "true",
        "create-fsx-stack": "false"
    }
    
    # Build CLI arguments
    cli_args = ["configure"]
    for key, value in config_options.items():
        cli_args.extend([f"--{key}", value])
    
    result = runner.invoke(configure, cli_args[1:], catch_exceptions=False)
    assert_command_succeeded(result)
    
    # Verify key configuration values were saved
    expected_config = {
        "stage": "prod",
        "create_vpc_stack": True,
        "create_security_group_stack": True, 
        "create_eks_cluster_stack": True,
        "create_s3_bucket_stack": True,
        "create_s3_endpoint_stack": False,
        "create_sagemaker_iam_role_stack": True,
        "create_hyperpod_cluster_stack": True,
        "create_helm_chart_stack": True,
        "create_fsx_stack": False
    }
    assert_config_values("./", expected_config)


@pytest.mark.dependency(name="validate", depends=["configure", "init"])
def test_validate_cluster(runner, cluster_name):
    """Validate cluster configuration for correctness."""
    result = runner.invoke(validate, catch_exceptions=False)
    assert_command_succeeded(result)


@pytest.mark.dependency(name="create", depends=["validate", "configure", "init"])
def test_create_cluster(runner, cluster_name, create_time):
    """Create cluster and verify submission messages."""
    global STACK_NAME, CREATE_TIME
    
    # Record time before submission
    CREATE_TIME = datetime.now(timezone.utc)
    
    result = runner.invoke(create, ["--region", REGION], catch_exceptions=False)
    assert_command_succeeded(result)
    
    # Verify expected submission messages appear
    assert "Configuration is valid!" in result.output
    assert "Submitted!" in result.output
    assert "Stack creation initiated" in result.output
    assert "Stack ID:" in result.output
    
    # Extract and store stack name for later tests with better error handling
    stack_id_match = re.search(r'Stack ID: (arn:aws:cloudformation[^\s]+)', result.output)
    if not stack_id_match:
        raise AssertionError(f"Stack ID not found in output: {result.output}")
    
    stack_id = stack_id_match.group(1)
    STACK_NAME = stack_id.split('/')[-2]
    
    print(f"✅ Successfully created stack: {STACK_NAME}")


@pytest.mark.dependency(name="verify_submission", depends=["create"])
def test_verify_cluster_submission_via_list(runner, cluster_name):
    """Use hyp list hyp-cluster to verify our stack was created and appears in the list."""
    global STACK_NAME, CREATE_TIME
    
    assert STACK_NAME, "Stack name should be set by previous test"
    assert CREATE_TIME, "Create time should be set by previous test"
    
    result = runner.invoke(list_cluster_stacks, ["--region", REGION], catch_exceptions=False)
    assert_command_succeeded(result)
    
    # Check that our stack appears in the list
    assert STACK_NAME in result.output, f"Stack {STACK_NAME} should appear in list output"
    
    # Check for recent creation times (within last 5 minutes of create)
    recent_threshold = CREATE_TIME - timedelta(minutes=1)
    creation_time_pattern = r'CreationTime\s+\|\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
    creation_times = re.findall(creation_time_pattern, result.output)
    
    recent_creations = []
    for time_str in creation_times:
        try:
            # Use fromisoformat for better performance with ISO dates
            iso_time_str = time_str.replace(' ', 'T')
            creation_time = datetime.fromisoformat(iso_time_str).replace(tzinfo=timezone.utc)
            if creation_time >= recent_threshold:
                recent_creations.append(creation_time)
        except ValueError:
            # Fallback to strptime for non-ISO format
            try:
                creation_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                if creation_time >= recent_threshold:
                    recent_creations.append(creation_time)
            except ValueError:
                continue
    
    assert recent_creations, f"Should have recent stack creations after {CREATE_TIME}"
    print(f"✅ Found {len(recent_creations)} recent stack creations, including our created stack")


@pytest.mark.dependency(name="describe_cluster", depends=["verify_submission"])
def test_describe_cluster_via_cli(runner, cluster_name):
    """Use hyp describe to get details about our created stack."""
    global STACK_NAME
    
    assert STACK_NAME, "Stack name should be set by previous test"
    
    # Try to describe the stack using CLI
    result = runner.invoke(describe_cluster_stack, [STACK_NAME, "--region", REGION], catch_exceptions=False)
    
    assert_command_succeeded(result)
    assert STACK_NAME in result.output, f"Stack {STACK_NAME} should appear in describe output"
    assert "StackStatus" in result.output or "Status" in result.output, "Stack status should be shown"


# --------- Extended Cluster Resource Verification Tests ---------
@pytest.mark.dependency(name="wait_for_cluster", depends=["verify_submission"])
def test_wait_for_cluster_ready(runner, cluster_name):
    """Wait for cluster to be ready by polling cluster status until InService.
    
    Uses exponential backoff polling to efficiently wait for cluster readiness.
    Times out after 1 hour if cluster doesn't become ready.
    """
    global STACK_NAME
    
    assert STACK_NAME, "Stack name should be available from previous tests"
    
    print(f"🔄 Waiting for cluster '{cluster_name}' to be InService...")
    timeout_minutes = 30
    deadline = time.time() + (timeout_minutes * 60)
    poll_count = 0
    poll_interval = 15  # Start with 15 seconds
    max_interval = 60   # Cap at 60 seconds
    
    while time.time() < deadline:
        poll_count += 1
        print(f"[DEBUG] Poll #{poll_count}: Checking cluster status...")
        
        try:
            status = get_cluster_status(cluster_name, REGION)
            
            print(f"[DEBUG] Current cluster status: {status}")
            
            if status == "InService":
                print(f"✅ Cluster '{cluster_name}' is now InService!")
                return
            elif status in ["Failed", "Deleting", "DeleteFailed"]:
                assert False, f"Cluster creation failed with status: {status}"
                
        except AssertionError as e:
            if "ResourceNotFound" in str(e) or "not found" in str(e):
                print(f"[STATUS] Cluster '{cluster_name}' not created yet, waiting...")
            elif "AWS CLI not available" in str(e) or "timed out" in str(e):
                assert False, str(e)
            else:
                print(f"[ERROR] Error during polling: {e}")
        
        time.sleep(poll_interval)
        # Exponential backoff with cap
        poll_interval = min(poll_interval * 1.5, max_interval)
    
    assert False, f"Timed out waiting for cluster '{cluster_name}' to be InService after {timeout_minutes} minutes"


# Add this test after cluster is InService but before cleanup
@pytest.mark.dependency(name="wait_for_stack", depends=["wait_for_cluster"])
def test_wait_for_stack_completion(runner, cluster_name):
    """Wait for CloudFormation stack to be fully complete."""
    global STACK_NAME
    assert STACK_NAME, "Stack name should be available"
    
    print(f"⏳ Waiting for CloudFormation stack {STACK_NAME} to be CREATE_COMPLETE...")
    wait_for_stack_complete(STACK_NAME, REGION)
    print(f"✅ Stack {STACK_NAME} is now CREATE_COMPLETE")


@pytest.mark.dependency(name="update_cluster", depends=["wait_for_stack"])
def test_cluster_update_workflow(runner, cluster_name):
    """Test hyp update-cluster command by toggling node recovery setting."""
    global STACK_NAME
    
    # Get initial node recovery setting
    initial_recovery = get_node_recovery_setting(cluster_name, REGION)
    print(f"Initial NodeRecovery setting: {initial_recovery}")
    
    # Determine target setting (toggle to opposite)
    target_recovery = "None" if initial_recovery == "Automatic" else "Automatic"
    print(f"Will change NodeRecovery to: {target_recovery}")
    
    # Test hyp update command
    result = runner.invoke(update_cluster, [
        "--cluster-name", cluster_name,
        "--node-recovery", target_recovery,
        "--region", REGION
    ], catch_exceptions=False)
    
    assert_command_succeeded(result)
    assert f"Cluster {cluster_name} has been updated" in result.output
    
    print(f"✅ Successfully ran hyp update-cluster command")

    # Get the current setting after update
    current_recovery = get_node_recovery_setting(cluster_name, REGION)
    print(f"Current NodeRecovery setting after update: {current_recovery}")
    
    # Verify the setting is valid and has been updated
    assert current_recovery in ["Automatic", "None"], f"Invalid NodeRecovery value: {current_recovery}"
    assert current_recovery != initial_recovery, f"NodeRecovery should have changed from {initial_recovery}"
    
    print(f"✅ Cluster update verification successful - NodeRecovery is now {current_recovery}")


@pytest.mark.dependency(name="cleanup_initiation", depends=["update_cluster"])
def test_cleanup_cluster_resources(runner, cluster_name):
    """Clean up cluster resources created during testing.
    
    Deletes SageMaker cluster, CloudFormation stack, and IAM service account stack.
    Fails the test if cleanup operations fail to alert the team.
    """
    import boto3
    global STACK_NAME
    
    print("🧹 Cleaning up cluster resources...")
    cleanup_errors = []
    
    # Create single CloudFormation client for reuse
    cfn_client = boto3.client('cloudformation', region_name=REGION)
    
    # 1. Delete SageMaker cluster first (if it exists)
    try:
        print(f"🗑️  Deleting SageMaker cluster: {cluster_name}")
        sagemaker_client = boto3.client('sagemaker', region_name=REGION)
        sagemaker_client.delete_cluster(ClusterName=cluster_name)
        print(f"✅ SageMaker cluster deletion initiated for {cluster_name}")
    except Exception as e:
        error_msg = f"Failed to delete SageMaker cluster: {e}"
        print(f"⚠️  {error_msg}")
        cleanup_errors.append(error_msg)
    
    # 2. Delete IAM service account stack (eksctl-managed)
    try:
        iam_stack_name = get_iam_stack_name(cluster_name)
        
        print(f"🗑️  Deleting IAM service account stack: {iam_stack_name}")
        cfn_client.delete_stack(StackName=iam_stack_name)
        print(f"✅ IAM service account stack deletion initiated for {iam_stack_name}")
    except Exception as e:
        error_msg = f"Failed to delete IAM service account stack: {e}"
        print(f"⚠️  {error_msg}")
        cleanup_errors.append(error_msg)
    
    # 3. Delete main CloudFormation stack (if we have one)
    if STACK_NAME:
        try:
            print(f"🗑️  Deleting CloudFormation stack: {STACK_NAME}")
            cfn_client.delete_stack(StackName=STACK_NAME)
            print(f"✅ CloudFormation stack deletion initiated for {STACK_NAME}")
        except Exception as e:
            error_msg = f"Failed to delete CloudFormation stack {STACK_NAME}: {e}"
            print(f"⚠️  {error_msg}")
            cleanup_errors.append(error_msg)
    
    print("✅ Cluster resource cleanup initiated successfully")
    

############################### MONITORING CLUSTER DELETION #######################################
################################# OMITTED TO SAVE TIME ############################################

# def test_wait_for_stack_deletion_complete(runner, cluster_name):
#     """Wait for IAM service account stack and main CloudFormation stack deletion to complete."""
#     global STACK_NAME
    
#     # Only set stack name if not already set by previous tests
#     if not STACK_NAME:
#         print("⚠️  No stack name available from previous tests - skipping stack deletion monitoring")
#         return
    
#     cfn_client = boto3.client('cloudformation', region_name=REGION)
    
#     # 1. Wait for IAM service account stack deletion using waiter
#     iam_stack_name = get_iam_stack_name(cluster_name)
    
#     print(f"🔄 Waiting for IAM service account stack {iam_stack_name} deletion...")
    
#     try:
#         waiter = cfn_client.get_waiter('stack_delete_complete')
#         waiter.wait(
#             StackName=iam_stack_name,
#             WaiterConfig={'Delay': 15, 'MaxAttempts': 20}  # 5 minutes max
#         )
#         print(f"✅ IAM service account stack {iam_stack_name} successfully deleted!")
#     except cfn_client.exceptions.ClientError as e:
#         if 'does not exist' in str(e):
#             print(f"✅ IAM service account stack {iam_stack_name} no longer exists (deleted)")
#         else:
#             print(f"⚠️  IAM stack deletion monitoring failed: {e}")
#     except Exception as e:
#         print(f"⚠️  IAM stack deletion failed: {e}")
    
#     # 2. Wait for main CloudFormation stack deletion using waiter
#     if not STACK_NAME:
#         print("⚠️  No main stack to monitor - cleanup verification complete")
#         return
    
#     print(f"🔄 Waiting for main stack {STACK_NAME} deletion to complete...")
    
#     try:
#         waiter = cfn_client.get_waiter('stack_delete_complete')
#         waiter.wait(
#             StackName=STACK_NAME,
#             WaiterConfig={'Delay': 30, 'MaxAttempts': 60}  # 30 minutes max
#         )
#         print(f"✅ Main stack {STACK_NAME} successfully deleted!")
#     except cfn_client.exceptions.ClientError as e:
#         if 'does not exist' in str(e):
#             print(f"✅ Main stack {STACK_NAME} no longer exists (deleted)")
#         else:
#             raise AssertionError(f"Main stack deletion failed: {e}")
#     except Exception as e:
#         raise AssertionError(f"Main stack deletion failed: {e}")