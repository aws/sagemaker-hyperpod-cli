import time
import uuid
import json
import pytest
import boto3

from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import (
    Model, Server, SageMakerEndpoint, TlsConfig
)
import sagemaker_core.main.code_injection.codec as codec

# --------- Config ---------
NAMESPACE = "integration"
REGION = "us-east-2"
ENDPOINT_NAME = "js-sdk-integration"

INSTANCE_TYPE = "ml.g5.4xlarge"
MODEL_ID = "deepseek-llm-r1-distill-qwen-1-5b"

TIMEOUT_MINUTES = 15
POLL_INTERVAL_SECONDS = 30

@pytest.fixture(scope="module")
def sagemaker_client():
    return boto3.client("sagemaker", region_name=REGION)

@pytest.fixture(scope="module")
def endpoint_obj():
    model = Model(model_id=MODEL_ID)
    server = Server(instance_type=INSTANCE_TYPE)
    sm_endpoint = SageMakerEndpoint(name=ENDPOINT_NAME)

    return HPJumpStartEndpoint(model=model, server=server, sage_maker_endpoint=sm_endpoint)

@pytest.mark.dependency(name="create")
def test_create_endpoint(endpoint_obj):
    endpoint_obj.create(namespace=NAMESPACE)
    assert endpoint_obj.metadata.name == ENDPOINT_NAME

def test_list_endpoint():
    endpoints = HPJumpStartEndpoint.list(namespace=NAMESPACE)
    names = [ep.metadata.name for ep in endpoints]
    assert ENDPOINT_NAME in names

@pytest.mark.dependency(name="describe")
def test_get_endpoint():
    ep = HPJumpStartEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    assert ep.metadata.name == ENDPOINT_NAME
    assert ep.model.modelId == MODEL_ID

@pytest.mark.dependency(depends=["create", "describe"])
def test_wait_until_inservice():
    """Poll SDK until specific JumpStart endpoint reaches DeploymentComplete"""
    print(f"[INFO] Waiting for JumpStart endpoint '{ENDPOINT_NAME}' to be DeploymentComplete...")
    deadline = time.time() + (TIMEOUT_MINUTES * 60)
    poll_count = 0

    while time.time() < deadline:
        poll_count += 1
        print(f"[DEBUG] Poll #{poll_count}: Checking endpoint status...")

        try:
            ep = HPJumpStartEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
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


def test_invoke_endpoint(monkeypatch):
    original_transform = codec.transform  # Save original

    def mock_transform(data, shape, object_instance=None):
        if "Body" in data:
            return {"body": data["Body"].read().decode("utf-8")}
        return original_transform(data, shape, object_instance)  # Call original

    monkeypatch.setattr("sagemaker_core.main.resources.transform", mock_transform)

    ep = HPJumpStartEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    data = '{"inputs":"What is the capital of USA?"}'
    response = ep.invoke(body=data)
    
    assert "error" not in response.body.lower()


def test_get_operator_logs():
    ep = HPJumpStartEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    logs = ep.get_operator_logs(since_hours=1)
    assert logs

def test_list_pods():
    ep = HPJumpStartEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    pods = ep.list_pods(NAMESPACE)
    assert pods

def test_delete_endpoint():
    ep = HPJumpStartEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    ep.delete()
