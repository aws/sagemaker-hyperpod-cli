import time
import uuid
import pytest
import boto3
import os
from click.testing import CliRunner
from sagemaker.hyperpod.cli.commands.inference import (
    custom_create, 
    custom_invoke,
    custom_list,
    custom_describe,
    custom_delete,
    custom_get_operator_logs,
    custom_list_pods
)
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint
from test.integration_tests.utils import get_time_str

# --------- Test Configuration ---------
NAMESPACE = "integration"
VERSION = "1.0"
REGION = "us-east-2"
TIMEOUT_MINUTES = 20
POLL_INTERVAL_SECONDS = 30

BETA_FSX = "fs-0402c3308e6aba65c"    # fsx id for beta integration test cluster

FSX_LOCATION = os.getenv("FSX_ID", BETA_FSX)
stage = os.getenv("STAGE", "BETA").upper()

@pytest.fixture(scope="module")
def runner():
    return CliRunner()

@pytest.fixture(scope="module")
def custom_endpoint_name():
    return "custom-cli-integration-fsx-" + get_time_str()

@pytest.fixture(scope="module")
def sagemaker_client():
    return boto3.client("sagemaker", region_name=REGION)

# --------- Custom Endpoint Tests ---------
@pytest.mark.dependency(name="create")
def test_custom_create(runner, custom_endpoint_name):
    result = runner.invoke(custom_create, [
        "--namespace", NAMESPACE,
        "--version", VERSION,
        "--instance-type", "ml.c5.2xlarge",
        "--model-name", "test-model-integration-cli-fsx",
        "--model-source-type", "fsx",
        "--model-location", "hf-eqa",
        "--fsx-file-system-id", FSX_LOCATION,
        "--image-uri", "763104351884.dkr.ecr.us-west-2.amazonaws.com/huggingface-pytorch-inference:2.3.0-transformers4.48.0-cpu-py311-ubuntu22.04",
        "--container-port", "8080",
        "--model-volume-mount-name", "model-weights",
        "--endpoint-name", custom_endpoint_name,
        "--resources-requests", '{"cpu": "3200m", "nvidia.com/gpu": 0, "memory": "12Gi"}',
        "--resources-limits", '{"nvidia.com/gpu": 0}',
        "--env", '{ "SAGEMAKER_PROGRAM": "inference.py", "SAGEMAKER_SUBMIT_DIRECTORY": "/opt/ml/model/code", "SAGEMAKER_CONTAINER_LOG_LEVEL": "20", "SAGEMAKER_MODEL_SERVER_TIMEOUT": "3600", "ENDPOINT_SERVER_TIMEOUT": "3600", "MODEL_CACHE_ROOT": "/opt/ml/model", "SAGEMAKER_ENV": "1", "SAGEMAKER_MODEL_SERVER_WORKERS": "1" }'
    ])
    assert result.exit_code == 0, result.output


@pytest.mark.dependency(depends=["create"])
def test_custom_list(runner, custom_endpoint_name):
    result = runner.invoke(custom_list, ["--namespace", NAMESPACE])
    assert result.exit_code == 0
    assert custom_endpoint_name in result.output


@pytest.mark.dependency(name="describe", depends=["create"])
def test_custom_describe(runner, custom_endpoint_name):
    result = runner.invoke(custom_describe, [
        "--name", custom_endpoint_name,
        "--namespace", NAMESPACE,
        "--full"
    ])
    assert result.exit_code == 0
    assert custom_endpoint_name in result.output


@pytest.mark.dependency(depends=["create", "describe"])
def test_wait_until_inservice(custom_endpoint_name):
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


@pytest.mark.dependency(depends=["create"])
def test_custom_invoke(runner, custom_endpoint_name):
    result = runner.invoke(custom_invoke, [
        "--endpoint-name", custom_endpoint_name,
        "--body", '{"question" :"what is the name of the planet?", "context":"mars"}',
        "--content-type", "application/list-text"
    ])
    assert result.exit_code == 0
    assert "error" not in result.output.lower()


def test_custom_get_operator_logs(runner):
    result = runner.invoke(custom_get_operator_logs, ["--since-hours", "1"])
    assert result.exit_code == 0


def test_custom_list_pods(runner):
    result = runner.invoke(custom_list_pods, ["--namespace", NAMESPACE])
    assert result.exit_code == 0
    
    
@pytest.mark.dependency(depends=["create"])
def test_custom_delete(runner, custom_endpoint_name):
    result = runner.invoke(custom_delete, [
        "--name", custom_endpoint_name,
        "--namespace", NAMESPACE
    ])
    assert result.exit_code == 0
