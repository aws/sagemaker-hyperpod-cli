"""
End-to-end integration tests for init workflow with JumpStart endpoint template.

SAFETY WARNING: This test involves creating real AWS SageMaker endpoints.
Only run with proper cost controls and cleanup procedures in place.

Tests complete user workflow: init -> configure -> validate -> create -> wait -> delete.
Uses real AWS resources with cost implications.
"""
import time
import yaml
import pytest
import boto3
from pathlib import Path
import tempfile
import os

import sys
from unittest.mock import patch

from click.testing import CliRunner
from sagemaker.hyperpod.cli.commands.inference import custom_invoke
from sagemaker.hyperpod.cli.commands.init import init, validate, _default_create as create
from sagemaker.hyperpod.cli.hyp_cli import delete
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from test.integration_tests.init.utils import (
    assert_command_succeeded,
    assert_init_files_created,
    assert_config_values,
)
from test.integration_tests.utils import get_time_str

# --------- Test Configuration ---------
NAMESPACE = "default"
VERSION = "1.0"
REGION = "us-east-2"
TIMEOUT_MINUTES = 20
POLL_INTERVAL_SECONDS = 30

@pytest.fixture(scope="module")
def runner():
    """CLI test runner for invoking commands."""
    return CliRunner()


@pytest.fixture(scope="module")
def js_endpoint_name():
    """Generate unique JumpStart endpoint name with timestamp."""
    return "js-cli-integration-" + get_time_str()


@pytest.fixture(scope="module")
def sagemaker_client():
    """AWS SageMaker client for resource verification."""
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


# --------- JumpStart Tests ---------
@pytest.mark.dependency(name="init")
def test_init_jumpstart(runner, js_endpoint_name, test_directory):
    """Initialize JumpStart endpoint template and verify file creation."""
    result = runner.invoke(
        init, ["hyp-jumpstart-endpoint", "."], catch_exceptions=False
    )
    assert_command_succeeded(result)
    assert_init_files_created("./", "hyp-jumpstart-endpoint")


@pytest.mark.dependency(name="configure", depends=["init"])
def test_configure_jumpstart(runner, js_endpoint_name, test_directory):
    """Configure JumpStart endpoint with model parameters and verify config persistence."""
    with patch.object(sys, 'argv', ['hyp', 'configure']):
        import importlib
        from sagemaker.hyperpod.cli.commands import init
        importlib.reload(init)
        configure = init.configure
    result = runner.invoke(
        configure, [
            "--model-id", "deepseek-llm-r1-distill-qwen-1-5b",
            "--instance-type", "ml.g5.8xlarge", 
            "--endpoint-name", js_endpoint_name
        ], catch_exceptions=False
    )
    assert_command_succeeded(result)
    
    # Verify configuration was saved correctly
    expected_config = {
        "model_id": "deepseek-llm-r1-distill-qwen-1-5b",
        "instance_type": "ml.g5.8xlarge",
        "endpoint_name": js_endpoint_name
    }
    assert_config_values("./", expected_config)


@pytest.mark.dependency(name="validate", depends=["configure", "init"])
def test_validate_jumpstart(runner, js_endpoint_name, test_directory):
    """Validate JumpStart endpoint configuration for correctness."""
    result = runner.invoke(validate, [], catch_exceptions=False)
    assert_command_succeeded(result)


@pytest.mark.dependency(name="create", depends=["validate", "configure", "init"])
def test_create_jumpstart(runner, js_endpoint_name, test_directory):
    """Create JumpStart endpoint for deployment and verify template rendering."""
    result = runner.invoke(create, [], catch_exceptions=False)
    assert_command_succeeded(result)

    assert "Submitted!" in result.output


@pytest.mark.dependency(name="wait", depends=["create"])
def test_wait_until_inservice(js_endpoint_name, test_directory):
    """Poll SDK until specific JumpStart endpoint reaches DeploymentComplete"""
    print(f"[INFO] Waiting for JumpStart endpoint '{js_endpoint_name}' to be DeploymentComplete...")
    deadline = time.time() + (TIMEOUT_MINUTES * 60)
    poll_count = 0

    while time.time() < deadline:
        poll_count += 1
        print(f"[DEBUG] Poll #{poll_count}: Checking endpoint status...")

        try:
            ep = HPJumpStartEndpoint.get(name=js_endpoint_name, namespace=NAMESPACE)
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
def test_custom_invoke(runner, js_endpoint_name, test_directory):
    result = runner.invoke(custom_invoke, [
        "--endpoint-name", js_endpoint_name,
        "--body", '{"inputs": "What is the capital of USA?"}'
    ])
    assert result.exit_code == 0
    assert "error" not in result.output.lower()


@pytest.mark.dependency(depends=["invoke"])
def test_js_delete(runner, js_endpoint_name, test_directory):
    """Clean up deployed JumpStart endpoint using CLI delete command."""
    result = runner.invoke(delete, [
        "hyp-jumpstart-endpoint",
        "--name", js_endpoint_name,
        "--namespace", NAMESPACE
    ])
    assert_command_succeeded(result)
