import time
import uuid
import pytest
import boto3
from click.testing import CliRunner
from sagemaker.hyperpod.cli.commands.inference import (
    js_create, custom_invoke, js_list, js_describe, js_delete, js_get_operator_logs, js_list_pods
)
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint

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
def js_endpoint_name():
    return f"jumpstart-cli-integ"

@pytest.fixture(scope="module")
def sagemaker_client():
    return boto3.client("sagemaker", region_name=REGION)

# --------- JumpStart Endpoint Tests ---------

def test_js_create(runner, js_endpoint_name):
    result = runner.invoke(js_create, [
        "--namespace", NAMESPACE,
        "--version", VERSION,
        "--model-id", "deepseek-llm-r1-distill-qwen-1-5b",
        "--model-version", "2.0.4",
        "--instance-type", "ml.g5.8xlarge",
        "--endpoint-name", js_endpoint_name,
        "--tls-certificate-output-s3-uri", "s3://tls-bucket-inf1-beta2"
    ])
    assert result.exit_code == 0, result.output


def test_js_list(runner, js_endpoint_name):
    result = runner.invoke(js_list, ["--namespace", NAMESPACE])
    assert result.exit_code == 0
    assert js_endpoint_name in result.output


def test_js_describe(runner, js_endpoint_name):
    result = runner.invoke(js_describe, [
        "--name", js_endpoint_name,
        "--namespace", NAMESPACE,
        "--full"
    ])
    assert result.exit_code == 0
    assert js_endpoint_name in result.output


def test_wait_until_inservice(js_endpoint_name):
    """Poll SDK until specific JumpStart endpoint reaches DeploymentComplete"""
    print(f"Waiting for JumpStart endpoint '{js_endpoint_name}' to be DeploymentComplete...")
    deadline = time.time() + (TIMEOUT_MINUTES * 60)

    while time.time() < deadline:
        try:
            ep = HPJumpStartEndpoint.get(name=js_endpoint_name, namespace=NAMESPACE)
            state = ep.status.deploymentStatus.deploymentObjectOverallState
            if state == "DeploymentComplete":
                return
            elif state == "DeploymentFailed":
                pytest.fail("Endpoint deployment failed.")
        except Exception as e:
            print(f"Error polling endpoint status: {e}")

        time.sleep(POLL_INTERVAL_SECONDS)

    pytest.fail("Timed out waiting for endpoint to be DeploymentComplete")


def test_custom_invoke(runner, js_endpoint_name):
    result = runner.invoke(custom_invoke, [
        "--endpoint-name", js_endpoint_name,
        "--body", '{"inputs": "What is the capital of USA?"}'
    ])
    assert result.exit_code == 0
    assert "error" not in result.output.lower()
    time.sleep(5)


def test_js_get_operator_logs(runner):
    result = runner.invoke(js_get_operator_logs, ["--since-hours", "1"])
    assert result.exit_code == 0


def test_js_list_pods(runner):
    result = runner.invoke(js_list_pods, ["--namespace", NAMESPACE])
    assert result.exit_code == 0
    time.sleep(5)


def test_js_delete(runner, js_endpoint_name):
    result = runner.invoke(js_delete, [
        "--name", js_endpoint_name,
        "--namespace", NAMESPACE
    ])
    assert result.exit_code == 0
