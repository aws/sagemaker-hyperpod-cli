import time
import pytest
import boto3
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import (
    Model, Server, SageMakerEndpoint
)
import sagemaker_core.main.code_injection.codec as codec
from test.integration_tests.utils import get_time_str
from sagemaker.hyperpod.common.config.metadata import Metadata

# --------- Config ---------
NAMESPACE = "integration"
REGION = "us-east-2"
ENDPOINT_NAME = "js-sdk-integration-" + get_time_str()

INSTANCE_TYPE = "ml.g5.8xlarge"
MODEL_ID = "deepseek-llm-r1-distill-qwen-1-5b"

TIMEOUT_MINUTES = 20
POLL_INTERVAL_SECONDS = 30

@pytest.fixture(scope="module")
def sagemaker_client():
    return boto3.client("sagemaker", region_name=REGION)

@pytest.fixture(scope="module")
def endpoint_obj():
    model = Model(model_id=MODEL_ID)
    server = Server(instance_type=INSTANCE_TYPE)
    sm_endpoint = SageMakerEndpoint(name=ENDPOINT_NAME)
    metadata = Metadata(name=ENDPOINT_NAME, namespace=NAMESPACE)

    return HPJumpStartEndpoint(metadata=metadata, model=model, server=server, sage_maker_endpoint=sm_endpoint)

@pytest.mark.dependency(name="create")
def test_create_endpoint(endpoint_obj):
    endpoint_obj.create()
    assert endpoint_obj.metadata.name == ENDPOINT_NAME

@pytest.mark.dependency(depends=["create"])
def test_list_endpoint():
    endpoints = HPJumpStartEndpoint.list(namespace=NAMESPACE)
    names = [ep.metadata.name for ep in endpoints]
    assert ENDPOINT_NAME in names

@pytest.mark.dependency(name="describe", depends=["create"])
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


@pytest.mark.dependency(depends=["create"])
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

@pytest.mark.dependency(depends=["create"])
def test_delete_endpoint():
    ep = HPJumpStartEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    ep.delete()
