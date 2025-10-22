"""
End-to-end integration tests for init workflow with PyTorch job template.

SAFETY WARNING: This test involves creating real PyTorch training jobs on HyperPod clusters.
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
from sagemaker.hyperpod.cli.commands.init import init, configure, validate, _default_create as create
from sagemaker.hyperpod.cli.hyp_cli import delete
from sagemaker.hyperpod.training.hyperpod_pytorch_job import HyperPodPytorchJob
from test.integration_tests.init.utils import (
    assert_command_succeeded,
    assert_init_files_created,
    assert_config_values,
)
from test.integration_tests.utils import get_time_str, execute_command

# --------- Test Configuration ---------
NAMESPACE = "default"
VERSION = "1.0"
REGION = "us-east-2"
TIMEOUT_MINUTES = 10
POLL_INTERVAL_SECONDS = 30

@pytest.fixture(scope="module")
def runner():
    """CLI test runner for invoking commands."""
    return CliRunner()


@pytest.fixture(scope="module")
def pytorch_job_name():
    """Generate unique PyTorch job name with timestamp."""
    return "torch-integ-" + get_time_str()


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


# # --------- PyTorch Job Tests ---------
@pytest.mark.dependency(name="init")
def test_init_pytorch_job(runner, pytorch_job_name, test_directory):
    """Initialize PyTorch job template and verify file creation."""
    result = runner.invoke(
        init, ["hyp-pytorch-job", "."], catch_exceptions=False
    )
    assert_command_succeeded(result)
    assert_init_files_created("./", "hyp-pytorch-job")


@pytest.mark.dependency(name="configure", depends=["init"])
def test_configure_pytorch_job(runner, pytorch_job_name, test_directory):
    """Configure PyTorch job with training parameters and verify config persistence."""
    with patch.object(sys, 'argv', ['hyp', 'configure']):
        import importlib
        from sagemaker.hyperpod.cli.commands import init
        importlib.reload(init)
        configure = init.configure
    
    result = runner.invoke(
        configure, [
        # Required fields only
        "--job-name", pytorch_job_name,
        "--image", "pytorch/pytorch:2.0.1-cuda11.7-cudnn8-devel",
        "--command", '["python", "-c", "import torch; print(torch.__version__); import time; time.sleep(3600)"]',
    ], catch_exceptions=False
    )
    assert_command_succeeded(result)

    # Simplified expected_config
    expected_config = {
        "job_name": pytorch_job_name,
        "image": "pytorch/pytorch:2.0.1-cuda11.7-cudnn8-devel",
        "command": ["python", "-c", "import torch; print(torch.__version__); import time; time.sleep(3600)"],
    }
    assert_config_values("./", expected_config)


@pytest.mark.dependency(name="validate", depends=["configure", "init"])
def test_validate_pytorch_job(runner, pytorch_job_name, test_directory):
    """Validate PyTorch job configuration for correctness."""
    result = runner.invoke(validate, [], catch_exceptions=False)
    assert_command_succeeded(result)


@pytest.mark.dependency(name="create", depends=["validate", "configure", "init"])
def test_create_pytorch_job(runner, pytorch_job_name, test_directory):
    """Create PyTorch job for deployment and verify template rendering."""
    result = runner.invoke(create, [], catch_exceptions=False)
    assert_command_succeeded(result)
                             
    # Verify expected submission messages appear
    assert "Submitted!" in result.output
    assert "Successfully submitted HyperPodPytorchJob" in result.output
    assert pytorch_job_name in result.output


@pytest.mark.dependency(name="wait", depends=["create"])
def test_wait_for_job_running(pytorch_job_name, test_directory):
    """Poll SDK until PyTorch job reaches Running state."""
    print(f"[INFO] Waiting for PyTorch job '{pytorch_job_name}' to be Running...")
    deadline = time.time() + (TIMEOUT_MINUTES * 60)
    poll_count = 0

    while time.time() < deadline:
        poll_count += 1
        print(f"[DEBUG] Poll #{poll_count}: Checking job status...")

        try:
            job = HyperPodPytorchJob.get(name=pytorch_job_name, namespace=NAMESPACE)
            if job.status and hasattr(job.status, 'conditions'):
                # Check for Running condition
                for condition in job.status.conditions:
                    if condition.type in ["PodsRunning", "Running"] and condition.status == "True":
                        print(f"[INFO] Job {pytorch_job_name} is now Running")
                        return
                    elif condition.type == "Failed" and condition.status == "True":
                        pytest.fail(f"Job {pytorch_job_name} failed: {condition.reason}")
                
                print(f"[DEBUG] Job status conditions: {[c.type for c in job.status.conditions]}")
            else:
                print(f"[DEBUG] Job status not yet available")

        except Exception as e:
            print(f"[DEBUG] Exception during polling: {e}")

        time.sleep(POLL_INTERVAL_SECONDS)

    pytest.fail(f"[ERROR] Timed out waiting for job {pytorch_job_name} to be Running")


@pytest.mark.dependency(name="list_pods", depends=["wait"])
def test_list_pods(pytorch_job_name, test_directory):
    """Test listing pods for a specific job."""
    # Wait a moment to ensure pods are created
    time.sleep(10)

    list_pods_result = execute_command([
        "hyp", "list-pods", "hyp-pytorch-job",
        "--job-name", pytorch_job_name,
        "--namespace", NAMESPACE
    ])
    assert list_pods_result.returncode == 0

    # Verify the output contains expected headers and job name
    output = list_pods_result.stdout.strip()
    assert f"Pods for job: {pytorch_job_name}" in output
    assert "POD NAME" in output
    assert "NAMESPACE" in output

    # Verify at least one pod is listed (should contain the job name in the pod name)
    assert f"{pytorch_job_name}-pod-" in output

    print(f"[INFO] Successfully listed pods for job: {pytorch_job_name}")


@pytest.mark.dependency(depends=["list_pods"])
def test_pytorch_job_delete(pytorch_job_name, test_directory):
    """Clean up deployed PyTorch job using CLI delete command and verify deletion."""
    delete_result = execute_command([
        "hyp", "delete", "hyp-pytorch-job",
        "--job-name", pytorch_job_name,
        "--namespace", NAMESPACE
    ])
    assert delete_result.returncode == 0
    print(f"[INFO] Successfully deleted job: {pytorch_job_name}")

    # Wait a moment for the job to be deleted
    time.sleep(5)

    # Verify the job is no longer listed
    list_result = execute_command(["hyp", "list", "hyp-pytorch-job", "--namespace", NAMESPACE])
    assert list_result.returncode == 0

    # The job name should no longer be in the output
    assert pytorch_job_name not in list_result.stdout
    print(f"[INFO] Verified job {pytorch_job_name} is no longer listed after deletion")