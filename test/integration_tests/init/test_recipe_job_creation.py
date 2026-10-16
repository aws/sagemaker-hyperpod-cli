"""
End-to-end integration tests for hyp-recipe-job template.

SAFETY WARNING: This test submits a real HyperPodPyTorchJob to a live cluster.
Only run with proper cost controls and cleanup procedures in place.

Tests complete user workflow: init -> configure -> validate -> create -> wait -> delete.
Uses real AWS resources (SageMaker Hub, S3, Kubernetes) with cost implications.
"""
import os
import re
import sys
import tempfile
import time
import uuid
from pathlib import Path
from unittest.mock import patch

import boto3
import pytest
import yaml
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
    return "recipe-integ-{}-{}".format(get_time_str(), uuid.uuid4().hex[:8])


@pytest.fixture(scope="module")
def test_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        try:
            yield temp_dir
        finally:
            os.chdir(original_cwd)


def _run_cleanup_command(command, errors):
    try:
        execute_command(command)
    except RuntimeError as error:
        errors.append(str(error))


@pytest.fixture(scope="module")
def recipe_fsx_resources(job_name, test_directory):
    """Create an isolated static FSx PV/PVC for this recipe test run."""
    fsx_id = os.getenv("FSX_ID")
    assert fsx_id, "FSX_ID must be set for recipe integration tests"

    response = boto3.client("fsx", region_name=REGION).describe_file_systems(
        FileSystemIds=[fsx_id]
    )
    file_systems = response.get("FileSystems", [])
    assert len(file_systems) == 1, "Expected exactly one FSx filesystem"

    file_system = file_systems[0]
    assert file_system.get("FileSystemType") == "LUSTRE"
    assert file_system.get("Lifecycle") == "AVAILABLE"

    lustre_config = file_system.get("LustreConfiguration", {})
    dns_name = file_system.get("DNSName")
    mount_name = lustre_config.get("MountName")
    storage = "{}Gi".format(file_system.get("StorageCapacity"))
    assert dns_name and mount_name

    pv_name = "{}-fsx-pv".format(job_name)
    pvc_name = "{}-fsx-pvc".format(job_name)
    assert pv_name != "fsx-pv-new"
    assert pvc_name != "fsx-claim"

    manifest = [
        {
            "apiVersion": "v1",
            "kind": "PersistentVolume",
            "metadata": {"name": pv_name},
            "spec": {
                "capacity": {"storage": storage},
                "volumeMode": "Filesystem",
                "accessModes": ["ReadWriteMany"],
                "mountOptions": ["flock"],
                "persistentVolumeReclaimPolicy": "Retain",
                "storageClassName": "",
                "csi": {
                    "driver": "fsx.csi.aws.com",
                    "volumeHandle": fsx_id,
                    "volumeAttributes": {
                        "dnsname": dns_name,
                        "mountname": mount_name,
                    },
                },
            },
        },
        {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": pvc_name, "namespace": NAMESPACE},
            "spec": {
                "accessModes": ["ReadWriteMany"],
                "volumeMode": "Filesystem",
                "storageClassName": "",
                "volumeName": pv_name,
                "resources": {"requests": {"storage": storage}},
            },
        },
    ]
    manifest_path = Path(test_directory) / ".recipe-fsx-resources.yaml"
    manifest_path.write_text(yaml.safe_dump_all(manifest, sort_keys=False))

    try:
        execute_command(["kubectl", "apply", "-f", str(manifest_path)])
        execute_command([
            "kubectl", "wait",
            "--for=jsonpath={.status.phase}=Bound",
            "persistentvolumeclaim/{}".format(pvc_name),
            "--namespace", NAMESPACE,
            "--timeout=120s",
        ])
        yield {"pv_name": pv_name, "pvc_name": pvc_name}
    finally:
        cleanup_errors = []
        _run_cleanup_command([
            "kubectl", "delete", "hyperpodpytorchjob", job_name,
            "--namespace", NAMESPACE,
            "--ignore-not-found=true", "--wait=true", "--timeout=180s",
        ], cleanup_errors)
        _run_cleanup_command([
            "kubectl", "delete", "pod",
            "--selector", "HPJob={}".format(job_name),
            "--namespace", NAMESPACE,
            "--ignore-not-found=true", "--wait=true", "--timeout=180s",
        ], cleanup_errors)
        _run_cleanup_command([
            "kubectl", "delete", "configmap", "training-config-{}".format(job_name),
            "--namespace", NAMESPACE,
            "--ignore-not-found=true", "--wait=true", "--timeout=180s",
        ], cleanup_errors)
        _run_cleanup_command([
            "kubectl", "delete", "persistentvolumeclaim", pvc_name,
            "--namespace", NAMESPACE,
            "--ignore-not-found=true", "--wait=true", "--timeout=180s",
        ], cleanup_errors)
        _run_cleanup_command([
            "kubectl", "delete", "persistentvolume", pv_name,
            "--ignore-not-found=true", "--wait=true", "--timeout=180s",
        ], cleanup_errors)
        if cleanup_errors:
            raise RuntimeError("Recipe resource cleanup failed: {}".format(
                "; ".join(cleanup_errors)
            ))


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
    assert "claimName: fsx-claim" in (base / "k8s.jinja").read_text()


@pytest.mark.dependency(name="configure", depends=["init"])
def test_configure_recipe_job(
    runner, job_name, test_directory, recipe_fsx_resources
):
    """Configure recipe job with training parameters."""
    # Patch this run's PVC and reduce EFA in the downloaded template.
    k8s_jinja = Path("k8s.jinja")
    template = k8s_jinja.read_text()
    default_claim = "claimName: fsx-claim"
    assert template.count(default_claim) == 1
    template = template.replace(
        default_claim,
        "claimName: {}".format(recipe_fsx_resources["pvc_name"]),
        1,
    )
    template = re.sub(
        r"(vpc\.amazonaws\.com/efa:\s*)\d+", r"\g<1>1", template
    )
    k8s_jinja.write_text(template)

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
        "--lr-warmup-steps-ratio", "0.1",
        "--max-epochs", "20", 
        "--output-path", "/data/output/{}".format(job_name),
        "--results-directory", "/data/results/{}".format(job_name),
        "--resume-from-path", "/data/output/{}".format(job_name),
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
def test_create_recipe_job(
    runner, job_name, test_directory, recipe_fsx_resources
):
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
    assert "claimName: {}".format(recipe_fsx_resources["pvc_name"]) in k8s_yaml
    assert "claimName: fsx-claim" not in k8s_yaml


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
                remaining_seconds = max(1, int(deadline - time.time()))
                wait_timeout = min(POLL_INTERVAL_SECONDS, remaining_seconds)
                print(
                    f"[INFO] Job {job_name} is Running; waiting for its pods "
                    "to be Ready..."
                )
                execute_command([
                    "kubectl", "wait",
                    "--for=condition=Ready",
                    "pod",
                    "--selector", f"HPJob={job_name}",
                    "--namespace", NAMESPACE,
                    f"--timeout={wait_timeout}s",
                ])
                print(f"[INFO] Job {job_name} pods are Ready")
                return

        except RuntimeError as e:
            print(f"[DEBUG] Exception during polling: {e}")

        remaining_seconds = deadline - time.time()
        if remaining_seconds <= 0:
            break
        time.sleep(min(POLL_INTERVAL_SECONDS, remaining_seconds))

    pytest.fail(
        f"[ERROR] Timed out waiting for job {job_name} pods to be Ready "
        f"after {TIMEOUT_MINUTES}m"
    )


@pytest.mark.dependency(name="list_pods", depends=["wait"])
def test_list_pods_recipe_job(job_name, test_directory):
    """List pods associated with the recipe job."""
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
    pod_result = execute_command([
        "kubectl", "get", "pods",
        "--namespace", NAMESPACE,
        "--selector", "HPJob={}".format(job_name),
        "--output", "jsonpath={.items[0].metadata.name}",
    ])
    pod_name = pod_result.stdout.strip()
    assert pod_name, "No pod found for job"

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
