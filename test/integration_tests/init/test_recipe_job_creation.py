"""
End-to-end integration tests for hyp-recipe-job template.

SAFETY WARNING: This test submits a real HyperPodPyTorchJob to a live cluster.
Only run with proper cost controls and cleanup procedures in place.

Tests complete user workflow: init -> configure -> validate -> create -> wait -> delete.
Uses real AWS resources (SageMaker Hub, S3, Kubernetes) with cost implications.
"""
import time
import yaml
import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner
from sagemaker.hyperpod.cli.commands.init import init, configure, validate, reset
from test.integration_tests.init.utils import (
    assert_command_succeeded,
    assert_config_values,
    get_most_recent_run_directory,
)
from test.integration_tests.utils import get_time_str, execute_command, execute_command_with_retry

# --------- Test Configuration ---------
NAMESPACE = "default"
REGION = "us-east-2"
INSTANCE_TYPE = "ml.g5.48xlarge"
HF_MODEL_ID = "Qwen/Qwen3-4B"
TECHNIQUE = "SFT"
TIMEOUT_MINUTES = 30
POLL_INTERVAL_SECONDS = 30


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


@pytest.fixture(scope="module")
def job_name():
    return "recipe-integ-" + get_time_str()


@pytest.fixture(scope="module")
def test_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        try:
            yield temp_dir
        finally:
            os.chdir(original_cwd)


# --------- Recipe Job Tests ---------

@pytest.mark.dependency(name="init")
def test_init_recipe_job(runner, job_name, test_directory):
    """Initialize recipe job from SageMaker Hub and verify files are created."""
    result = runner.invoke(init, [
        "hyp-recipe-job", ".",
        "--huggingface-model-id", HF_MODEL_ID,
        "--technique", TECHNIQUE,
        "--instance-type", INSTANCE_TYPE,
    ], catch_exceptions=False)

    assert_command_succeeded(result)
    base = Path(test_directory)
    assert (base / "config.yaml").exists(), f"config.yaml not found in {test_directory}. Output: {result.output}"
    assert (base / ".override_spec.json").exists(), f".override_spec.json not found in {test_directory}"
    assert (base / "k8s.jinja").exists(), f"k8s.jinja not found in {test_directory}"


@pytest.mark.dependency(name="configure", depends=["init"])
def test_configure_recipe_job(runner, job_name, test_directory):
    """Configure recipe job with training parameters."""
    # Patch EFA to 1 in k8s.jinja — the S3 template may ship with a higher value
    import re
    k8s_jinja = Path("k8s.jinja")
    k8s_jinja.write_text(
        re.sub(r'(vpc\.amazonaws\.com/efa:\s*)\d+', r'\g<1>1', k8s_jinja.read_text())
    )

    with patch.object(sys, 'argv', ['hyp', 'configure']):
        import importlib
        from sagemaker.hyperpod.cli.commands import init as init_mod
        importlib.reload(init_mod)
        configure_cmd = init_mod.configure

    result = runner.invoke(configure_cmd, [
        "--name", job_name,
        "--namespace", NAMESPACE,
        "--data-path", "/data/recipes-data/sft/zc_train_256.jsonl",
        "--global-batch-size", "8",
        "--learning-rate", "0.0001",
        "--lr-warmup-ratio", "0.1",
        "--max-epochs", "20", 
        "--output-path", "/data/output/qwen3-sft",
        "--results-directory", "/data/results/qwen3-sft",
        "--resume-from-path", "/data/output/qwen3-sft",
        "--training-data-name", "zc_train_256",
        "--validation-data-name", "zc_train_256",
        "--validation-data-path", "/data/recipes-data/sft/zc_train_256.jsonl",
        "--train-val-split-ratio", "0.9",
        "--instance-type", INSTANCE_TYPE,
    ], catch_exceptions=False)

    assert_command_succeeded(result)
    assert_config_values(test_directory, {
        "name": job_name,
        "namespace": NAMESPACE,
        "instance_type": INSTANCE_TYPE,
    })


@pytest.mark.dependency(name="validate", depends=["configure", "init"])
def test_validate_recipe_job(runner, job_name, test_directory):
    """Validate recipe job configuration."""
    result = runner.invoke(validate, [], catch_exceptions=False)
    assert_command_succeeded(result)


@pytest.mark.dependency(name="create", depends=["validate", "configure", "init"])
def test_create_recipe_job(runner, job_name, test_directory):
    """Submit recipe job to Kubernetes and verify submission."""
    from sagemaker.hyperpod.cli.commands.init import _default_create as create_cmd

    result = runner.invoke(create_cmd, [], catch_exceptions=False)
    assert_command_succeeded(result)

    # Verify run directory was created with rendered k8s.yaml
    run_dir = get_most_recent_run_directory(test_directory)
    assert (run_dir / "k8s.yaml").exists()
    assert (run_dir / "config.yaml").exists()

    # Verify job name appears in rendered output
    k8s_yaml = (run_dir / "k8s.yaml").read_text()
    assert job_name in k8s_yaml


@pytest.mark.dependency(name="wait", depends=["create"])
def test_wait_for_recipe_job_running(job_name, test_directory):
    """Poll hyp describe until recipe job pods reach Running state without crash-looping."""
    print(f"[INFO] Waiting for recipe job '{job_name}' to be Running...")
    deadline = time.time() + (TIMEOUT_MINUTES * 60)
    poll_count = 0

    while time.time() < deadline:
        poll_count += 1
        print(f"[DEBUG] Poll #{poll_count}: Checking job status...")

        try:
            result = execute_command([
                "hyp", "describe", "hyp-recipe-job",
                "--job-name", job_name,
                "--namespace", NAMESPACE,
            ])
            output = result.stdout

            if "Failed" in output and "Status:             True" in output:
                pytest.fail(f"Job {job_name} failed")

            # Check for crash-looping pods via list-pods
            pods_result = execute_command([
                "hyp", "list-pods", "hyp-recipe-job",
                "--job-name", job_name,
                "--namespace", NAMESPACE,
            ])
            # hyp list-pods returns pod names; check restart counts via describe output
            if "restartCount" in pods_result.stdout:
                restart_counts = [
                    int(x) for x in pods_result.stdout.split()
                    if x.isdigit()
                ]
                if any(c > 3 for c in restart_counts):
                    pytest.fail(f"Job {job_name} pods are crash-looping")

            if "Running" in output and "Status:             True" in output:
                print(f"[INFO] Job {job_name} is Running")
                return

        except RuntimeError as e:
            print(f"[DEBUG] Exception during polling: {e}")

        time.sleep(POLL_INTERVAL_SECONDS)

    pytest.fail(f"[ERROR] Timed out waiting for job {job_name} to be Running after {TIMEOUT_MINUTES}m")


@pytest.mark.dependency(name="list_pods", depends=["wait"])
def test_list_pods_recipe_job(job_name, test_directory):
    """List pods associated with the recipe job."""
    time.sleep(10)

    result = execute_command([
        "hyp", "list-pods", "hyp-recipe-job",
        "--job-name", job_name,
        "--namespace", NAMESPACE,
    ])
    assert result.returncode == 0
    assert f"Pods for job: {job_name}" in result.stdout
    assert "POD NAME" in result.stdout
    assert "NAMESPACE" in result.stdout
    print(f"[INFO] list-pods output:\n{result.stdout}")


@pytest.mark.dependency(name="get_logs", depends=["wait"])
def test_get_logs_recipe_job(job_name, test_directory):
    """Get logs from the first pod of the recipe job."""
    pods_result = execute_command([
        "hyp", "list-pods", "hyp-recipe-job",
        "--job-name", job_name,
        "--namespace", NAMESPACE,
    ])
    assert pods_result.returncode == 0
    # Extract first pod name — pod rows start with the job name
    lines = [l for l in pods_result.stdout.splitlines() if l.strip().startswith(job_name)]
    assert lines, "No pod found for job"
    pod_name = lines[0].split()[0]

    result = execute_command([
        "hyp", "get-logs", "hyp-recipe-job",
        "--job-name", job_name,
        "--pod-name", pod_name,
        "--namespace", NAMESPACE,
    ])
    assert result.returncode == 0
    print(f"[INFO] get-logs output for pod {pod_name}:\n{result.stdout[:500]}")


@pytest.mark.dependency(name="get_operator_logs", depends=["create"])
def test_get_operator_logs_recipe_job(job_name, test_directory):
    """Get operator logs for the recipe job."""
    result = execute_command([
        "hyp", "get-operator-logs", "hyp-recipe-job",
        "--since-hours", "1",
    ])
    assert result.returncode == 0
    print(f"[INFO] get-operator-logs output:\n{result.stdout[:500]}")


@pytest.mark.dependency(name="exec_cmd", depends=["wait"])
def test_exec_recipe_job(job_name, test_directory):
    """Exec a simple command in the recipe job pod."""
    result = execute_command([
        "hyp", "exec", "hyp-recipe-job",
        "--job-name", job_name,
        "--namespace", NAMESPACE,
        "--all-pods",
        "--", "echo", "hello",
    ])
    assert result.returncode == 0
    assert "hello" in result.stdout
    print(f"[INFO] exec output:\n{result.stdout}")


@pytest.mark.dependency(name="list", depends=["create"])
def test_list_recipe_jobs(job_name, test_directory):
    """List recipe jobs and verify the created job appears."""
    result = execute_command_with_retry([
        "hyp", "list", "hyp-recipe-job",
        "--namespace", NAMESPACE,
    ])
    assert result.returncode == 0
    assert job_name in result.stdout
    print(f"[INFO] Job {job_name} found in list output")


@pytest.mark.dependency(name="describe", depends=["create"])
def test_describe_recipe_job(job_name, test_directory):
    """Describe the created recipe job and verify key fields."""
    result = execute_command_with_retry([
        "hyp", "describe", "hyp-recipe-job",
        "--job-name", job_name,
        "--namespace", NAMESPACE,
    ])
    assert result.returncode == 0
    assert job_name in result.stdout
    print(f"[INFO] Describe output for {job_name}:\n{result.stdout}")


@pytest.mark.run(order=99)
@pytest.mark.dependency(depends=["create"])
def test_recipe_job_delete(job_name, test_directory):
    """Clean up submitted recipe job."""
    delete_result = execute_command([
        "hyp", "delete", "hyp-recipe-job",
        "--job-name", job_name,
        "--namespace", NAMESPACE,
    ])
    assert delete_result.returncode == 0
    print(f"[INFO] Successfully deleted job: {job_name}")
