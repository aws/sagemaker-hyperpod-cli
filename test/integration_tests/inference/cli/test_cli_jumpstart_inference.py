import time
import pytest
import boto3
from click.testing import CliRunner
from sagemaker.hyperpod.cli.commands.inference import (
    js_create, custom_invoke, js_list, js_describe, js_delete, js_get_operator_logs, js_list_pods
)
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from test.integration_tests.utils import get_time_str

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
    return "js-cli-integration-" + get_time_str()

@pytest.fixture(scope="module")
def sagemaker_client():
    return boto3.client("sagemaker", region_name=REGION)

# --------- JumpStart Endpoint Tests ---------
@pytest.mark.dependency(name="create")
def test_js_create(runner, js_endpoint_name):
    result = runner.invoke(js_create, [
        "--namespace", NAMESPACE,
        "--version", VERSION,
        "--model-id", "deepseek-llm-r1-distill-qwen-1-5b",
        "--instance-type", "ml.g5.8xlarge",
        "--endpoint-name", js_endpoint_name,
    ])
    assert result.exit_code == 0, result.output


@pytest.mark.dependency(depends=["create"])
def test_js_list(runner, js_endpoint_name):
    result = runner.invoke(js_list, ["--namespace", NAMESPACE])
    assert result.exit_code == 0
    assert js_endpoint_name in result.output


@pytest.mark.dependency(name="describe", depends=["create"])
def test_js_describe(runner, js_endpoint_name):
    result = runner.invoke(js_describe, [
        "--name", js_endpoint_name,
        "--namespace", NAMESPACE,
        "--full"
    ])
    assert result.exit_code == 0
    assert js_endpoint_name in result.output


@pytest.mark.dependency(depends=["create", "describe"])
def test_wait_until_inservice(js_endpoint_name):
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


@pytest.mark.dependency(depends=["create"])
@pytest.mark.skip
def test_custom_invoke(runner, js_endpoint_name):
    result = runner.invoke(custom_invoke, [
        "--endpoint-name", js_endpoint_name,
        "--body", '{"inputs": "What is the capital of USA?"}'
    ])
    assert result.exit_code == 0
    assert "error" not in result.output.lower()


def test_js_get_operator_logs(runner):
    result = runner.invoke(js_get_operator_logs, ["--since-hours", "1"])
    assert result.exit_code == 0


def test_js_list_pods(runner):
    result = runner.invoke(js_list_pods, ["--namespace", NAMESPACE])
    assert result.exit_code == 0


@pytest.mark.dependency(depends=["create"])
def test_js_delete(runner, js_endpoint_name):
    result = runner.invoke(js_delete, [
        "--name", js_endpoint_name,
        "--namespace", NAMESPACE
    ])
    assert result.exit_code == 0
