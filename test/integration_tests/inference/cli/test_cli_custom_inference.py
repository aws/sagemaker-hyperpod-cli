import time
import uuid
import pytest
import boto3
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

# --------- Test Configuration ---------
NAMESPACE = "integration"
VERSION = "1.0"
REGION = "us-east-2"
TIMEOUT_MINUTES = 15
POLL_INTERVAL_SECONDS = 30

@pytest.fixture(scope="module")
def runner():
    return CliRunner()

@pytest.fixture(scope="module")
def custom_endpoint_name():
    return f"custom-cli-integration"

@pytest.fixture(scope="module")
def sagemaker_client():
    return boto3.client("sagemaker", region_name=REGION)

# --------- Custom Endpoint Tests ---------

def test_custom_create(runner, custom_endpoint_name):
    result = runner.invoke(custom_create, [
        "--namespace", NAMESPACE,
        "--version", VERSION,
        "--instance-type", "ml.g5.8xlarge",
        "--model-name", "test-model-integration",
        "--model-source-type", "s3",
        "--model-location", "deepseek15b",
        "--s3-bucket-name", "test-model-s3-zhaoqi",
        "--s3-region", REGION,
        "--image-uri", "763104351884.dkr.ecr.us-east-2.amazonaws.com/huggingface-pytorch-tgi-inference:2.4.0-tgi2.3.1-gpu-py311-cu124-ubuntu22.04-v2.0",
        "--container-port", "8080",
        "--model-volume-mount-name", "model-weights",
        "--endpoint-name", custom_endpoint_name,
        "--resources-requests", '{"cpu": "30000m", "nvidia.com/gpu": 1, "memory": "100Gi"}',
        "--resources-limits", '{"nvidia.com/gpu": 1}',
        "--tls-certificate-output-s3-uri", "s3://tls-bucket-inf1-beta2",
        "--metrics-enabled", "true",
        "--metric-collection-period", "30",
        "--metric-name", "Invocations",
        "--metric-stat", "Sum",
        "--metric-type", "Average",
        "--min-value", "0.0",
        "--cloud-watch-trigger-name", "SageMaker-Invocations-new",
        "--cloud-watch-trigger-namespace", "AWS/SageMaker",
        "--target-value", "10",
        "--use-cached-metrics", "true",
        "--dimensions", '{"EndpointName": "' + custom_endpoint_name + '", "VariantName": "AllTraffic"}',
        "--env", '{ "HF_MODEL_ID": "/opt/ml/model", "SAGEMAKER_PROGRAM": "inference.py", "SAGEMAKER_SUBMIT_DIRECTORY": "/opt/ml/model/code", "MODEL_CACHE_ROOT": "/opt/ml/model", "SAGEMAKER_ENV": "1" }',

    ])
    assert result.exit_code == 0, result.output


def test_custom_list(runner, custom_endpoint_name):
    result = runner.invoke(custom_list, ["--namespace", NAMESPACE])
    assert result.exit_code == 0
    assert custom_endpoint_name in result.output


def test_custom_describe(runner, custom_endpoint_name):
    result = runner.invoke(custom_describe, [
        "--name", custom_endpoint_name,
        "--namespace", NAMESPACE,
        "--full"
    ])
    assert result.exit_code == 0
    assert custom_endpoint_name in result.output


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


def test_custom_invoke(runner, custom_endpoint_name):
    result = runner.invoke(custom_invoke, [
        "--endpoint-name", custom_endpoint_name,
        "--body", '{"inputs": "What is the capital of USA?"}'
    ])
    assert result.exit_code == 0
    assert "error" not in result.output.lower()


def test_custom_get_operator_logs(runner):
    result = runner.invoke(custom_get_operator_logs, ["--since-hours", "1"])
    assert result.exit_code == 0


def test_custom_list_pods(runner):
    result = runner.invoke(custom_list_pods, ["--namespace", NAMESPACE])
    assert result.exit_code == 0
    

def test_custom_delete(runner, custom_endpoint_name):
    result = runner.invoke(custom_delete, [
        "--name", custom_endpoint_name,
        "--namespace", NAMESPACE
    ])
    assert result.exit_code == 0
