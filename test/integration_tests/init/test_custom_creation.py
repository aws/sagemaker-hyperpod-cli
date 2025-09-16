"""
End-to-end integration tests for init workflow with custom endpoint template.

SAFETY WARNING: This test involves creating real AWS SageMaker endpoints.
Only run with proper cost controls and cleanup procedures in place.

Tests complete user workflow: init -> configure -> validate -> create -> wait -> invoke -> delete.
Uses real AWS resources with cost implications.
"""
import time
import yaml
import pytest
import boto3
from pathlib import Path
import os
import tempfile

import sys
from unittest.mock import patch

from test.integration_tests.init.utils import (
    assert_command_succeeded,
    assert_init_files_created,
    assert_config_values,
)

from click.testing import CliRunner
from sagemaker.hyperpod.cli.commands.inference import custom_invoke
from sagemaker.hyperpod.cli.commands.init import init, configure, validate, _default_create as create
from sagemaker.hyperpod.cli.hyp_cli import delete
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint
from test.integration_tests.utils import get_time_str

# --------- Test Configuration ---------
NAMESPACE = "default" 
VERSION = "1.0"
REGION = "us-east-2"
TIMEOUT_MINUTES = 15
POLL_INTERVAL_SECONDS = 30

BETA_BUCKET = "sagemaker-hyperpod-beta-integ-test-model-bucket-n"
PROD_BUCKET = "sagemaker-hyperpod-prod-integ-test-model-bucket"
stage = os.getenv("STAGE", "BETA").upper()
BUCKET_LOCATION = BETA_BUCKET if stage == "BETA" else PROD_BUCKET

@pytest.fixture(scope="module")
def runner():
    return CliRunner()

@pytest.fixture(scope="module")
def custom_endpoint_name():
    return "custom-cli-integration-" + get_time_str()

@pytest.fixture(scope="module")
def sagemaker_client():
    return boto3.client("sagemaker", region_name=REGION)


@pytest.fixture(scope="module")
def test_directory():
    """Create a temporary directory for test isolation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        try:
            yield temp_dir
        finally:
            os.chdir(original_cwd)


# --------- Custom Endpoint Tests ---------
@pytest.mark.dependency(name="init")
def test_init_custom(runner, custom_endpoint_name, test_directory):
    """Initialize custom endpoint template and verify file creation."""
    result = runner.invoke(
        init, ["hyp-custom-endpoint", "."], catch_exceptions=False
    )
    assert_command_succeeded(result)
    assert_init_files_created("./", "hyp-custom-endpoint")


@pytest.mark.dependency(name="configure", depends=["init"])
def test_configure_custom(runner, custom_endpoint_name, test_directory):
    """Configure custom endpoint with S3 model source and verify config persistence."""
    with patch.object(sys, 'argv', ['hyp', 'configure']):
        import importlib
        from sagemaker.hyperpod.cli.commands import init
        importlib.reload(init)
        configure = init.configure
    
    result = runner.invoke(
        configure, [
        # Required fields
        "--endpoint-name", custom_endpoint_name,
        "--model-name", "test-pytorch-model", 
        "--instance-type", "ml.c5.2xlarge",
        "--model-source-type", "s3",
        "--image-uri", "763104351884.dkr.ecr.us-west-2.amazonaws.com/huggingface-pytorch-inference:2.3.0-transformers4.48.0-cpu-py311-ubuntu22.04",
        "--container-port", "8080",
        "--model-volume-mount-name", "model-weights",
        
        # S3-specific required fields
        "--s3-bucket-name", BUCKET_LOCATION,
        "--model-location", "hf-eqa",
        "--s3-region", REGION,
        
        # Optional Params, but likely needed
        "--env", '{ "SAGEMAKER_PROGRAM": "inference.py", "SAGEMAKER_SUBMIT_DIRECTORY": "/opt/ml/model/code", "SAGEMAKER_CONTAINER_LOG_LEVEL": "20", "SAGEMAKER_MODEL_SERVER_TIMEOUT": "3600", "ENDPOINT_SERVER_TIMEOUT": "3600", "MODEL_CACHE_ROOT": "/opt/ml/model", "SAGEMAKER_ENV": "1", "SAGEMAKER_MODEL_SERVER_WORKERS": "1" }',
        "--resources-requests", '{"cpu": "3200m", "nvidia.com/gpu": 0, "memory": "12Gi"}',
        "--resources-limits", '{"cpu": "3200m", "memory": "12Gi", "nvidia.com/gpu": 0}',
    ], catch_exceptions=False
    )
    assert_command_succeeded(result)
    
    # Verify configuration was saved correctly
    expected_config = {
        # Required fields
        "endpoint_name": custom_endpoint_name,
        "model_name": "test-pytorch-model", 
        "instance_type": "ml.c5.2xlarge",
        "model_source_type": "s3",
        "image_uri": "763104351884.dkr.ecr.us-west-2.amazonaws.com/huggingface-pytorch-inference:2.3.0-transformers4.48.0-cpu-py311-ubuntu22.04",
        "container_port": 8080,
        "model_volume_mount_name": "model-weights",
        
        # S3-specific required fields
        "s3_bucket_name": BUCKET_LOCATION,
        "model_location": "hf-eqa",
        "s3_region": REGION,
        
        # Optional Params, but likely needed
        "env": {'SAGEMAKER_PROGRAM': 'inference.py', 'SAGEMAKER_SUBMIT_DIRECTORY': '/opt/ml/model/code', 'SAGEMAKER_CONTAINER_LOG_LEVEL': '20', 'SAGEMAKER_MODEL_SERVER_TIMEOUT': '3600', 'ENDPOINT_SERVER_TIMEOUT': '3600', 'MODEL_CACHE_ROOT': '/opt/ml/model', 'SAGEMAKER_ENV': '1', 'SAGEMAKER_MODEL_SERVER_WORKERS': '1'},
        "resources_requests": {'cpu': '3200m', 'nvidia.com/gpu': 0, 'memory': '12Gi'},
        "resources_limits": {'cpu': '3200m', 'memory': '12Gi', 'nvidia.com/gpu': 0},
    }
    assert_config_values("./", expected_config)


@pytest.mark.dependency(name="validate", depends=["configure", "init"])
def test_validate_custom(runner, custom_endpoint_name, test_directory):
    """Validate custom endpoint configuration for correctness."""
    result = runner.invoke(validate, [], catch_exceptions=False)
    assert_command_succeeded(result)


@pytest.mark.dependency(name="create", depends=["validate", "configure", "init"])
def test_create_custom(runner, custom_endpoint_name, test_directory):
    """Create custom endpoint for deployment and verify template rendering."""
    result = runner.invoke(create, [], catch_exceptions=False)
    assert_command_succeeded(result)

    # Verify expected submission messages appear  
    assert "Submitted!" in result.output
    assert "Creating sagemaker model and endpoint" in result.output
    assert custom_endpoint_name in result.output
    assert "The process may take a few minutes" in result.output


@pytest.mark.dependency(name="wait", depends=["create"])
def test_wait_until_inservice(custom_endpoint_name, test_directory):
    """Poll SDK until specific JumpStart endpoint reaches DeploymentComplete"""
    print(f"[INFO] Waiting for JumpStart endpoint '{custom_endpoint_name}' to be DeploymentComplete...")
    deadline = time.time() + (TIMEOUT_MINUTES * 60)
    poll_count = 0

    while time.time() < deadline:
        poll_count += 1
        print(f"[DEBUG] Poll #{poll_count}: Checking endpoint status...")

        try:
            ep = HPEndpoint.get(name=custom_endpoint_name, namespace=NAMESPACE)
            state = ep.status.endpoints.sagemaker.state
            print(f"[DEBUG] Current state: {state}")
            if state == "CreationCompleted":
                print("[INFO] Endpoint is in CreationCompleted state.")
                return
            
            deployment_state = ep.status.deploymentStatus.deploymentObjectOverallState
            if deployment_state == "DeploymentFailed":
                pytest.fail("Endpoint deployment failed.")

        except Exception as e:
            print(f"[ERROR] Exception during polling: {e}")

        time.sleep(POLL_INTERVAL_SECONDS)

    pytest.fail("[ERROR] Timed out waiting for endpoint to be DeploymentComplete")


@pytest.mark.dependency(name="invoke", depends=["wait"])
def test_custom_invoke(runner, custom_endpoint_name, test_directory):
    result = runner.invoke(custom_invoke, [
        "--endpoint-name", custom_endpoint_name,
        "--body", '{"question" :"what is the name of the planet?", "context":"mars"}',
        "--content-type", "application/list-text"
    ])
    assert result.exit_code == 0
    assert "error" not in result.output.lower()


@pytest.mark.dependency(depends=["invoke"])
def test_custom_delete(runner, custom_endpoint_name, test_directory):
    """Clean up deployed custom endpoint using CLI delete command."""
    result = runner.invoke(delete, [
        "hyp-custom-endpoint",
        "--name", custom_endpoint_name,
        "--namespace", NAMESPACE
    ])
    assert_command_succeeded(result)
