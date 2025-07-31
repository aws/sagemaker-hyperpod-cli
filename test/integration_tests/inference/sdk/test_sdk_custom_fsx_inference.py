import time
import pytest
import boto3
import os
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint
from sagemaker.hyperpod.inference.config.hp_endpoint_config import (
    ModelSourceConfig, FsxStorage, TlsConfig, Worker, ModelVolumeMount,
    ModelInvocationPort, Resources, EnvironmentVariables,
)
import sagemaker_core.main.code_injection.codec as codec
from test.integration_tests.utils import get_time_str

# --------- Test Configuration ---------
NAMESPACE = "integration"
REGION = "us-east-2"
ENDPOINT_NAME = "custom-sdk-integration-fsx-" + get_time_str()

MODEL_NAME = f"test-model-integration-sdk-fsx"
MODEL_LOCATION = "hf-eqa"
IMAGE_URI = "763104351884.dkr.ecr.us-west-2.amazonaws.com/huggingface-pytorch-inference:2.3.0-transformers4.48.0-cpu-py311-ubuntu22.04"

TIMEOUT_MINUTES = 15
POLL_INTERVAL_SECONDS = 30

BETA_FSX = "fs-0402c3308e6aba65c"    # fsx id for beta integration test cluster
PROD_FSX = "fs-0839e3bb2a0b2dacf"    # fsx id for prod integration test cluster
stage = os.getenv("STAGE", "BETA").upper()
DEFAULT_FSX_ID = BETA_FSX if stage == "BETA" else PROD_FSX

FSX_LOCATION = os.getenv("FSX_ID", DEFAULT_FSX_ID)

@pytest.fixture(scope="module")
def sagemaker_client():
    return boto3.client("sagemaker", region_name=REGION)

@pytest.fixture(scope="module")
def custom_endpoint():
    # Model Source
    model_src = ModelSourceConfig(
        model_source_type="fsx",
        model_location=MODEL_LOCATION,
        fsx_storage=FsxStorage(
            file_system_id=FSX_LOCATION
        ),
    )

    # Env vars
    env_vars = [
        EnvironmentVariables(name="SAGEMAKER_PROGRAM", value="inference.py"),
        EnvironmentVariables(name="SAGEMAKER_SUBMIT_DIRECTORY", value="/opt/ml/model/code"),
        EnvironmentVariables(name="SAGEMAKER_CONTAINER_LOG_LEVEL", value="20"),
        EnvironmentVariables(name="SAGEMAKER_MODEL_SERVER_TIMEOUT", value="3600"),
        EnvironmentVariables(name="ENDPOINT_SERVER_TIMEOUT", value="3600"),
        EnvironmentVariables(name="MODEL_CACHE_ROOT", value="/opt/ml/model"),
        EnvironmentVariables(name="SAGEMAKER_ENV", value="1"),
        EnvironmentVariables(name="SAGEMAKER_MODEL_SERVER_WORKERS", value="1"),
    ]

    # Worker
    worker = Worker(
        image=IMAGE_URI,
        model_volume_mount=ModelVolumeMount(name="model-weights"),
        model_invocation_port=ModelInvocationPort(container_port=8080),
        resources=Resources(
            requests={"cpu": "3200m", "nvidia.com/gpu": 0, "memory": "12Gi"},
            limits={"nvidia.com/gpu": 0}
        ),
        environment_variables=env_vars
    )

    return HPEndpoint(
        endpoint_name=ENDPOINT_NAME,
        instance_type="ml.c5.2xlarge",
        model_name=MODEL_NAME,
        model_source_config=model_src,
        worker=worker,
    )

@pytest.mark.dependency(name="create")
def test_create_endpoint(custom_endpoint):
    custom_endpoint.create(namespace=NAMESPACE)
    assert custom_endpoint.metadata.name == ENDPOINT_NAME

@pytest.mark.dependency(depends=["create"])
def test_list_endpoint():
    endpoints = HPEndpoint.list(namespace=NAMESPACE)
    names = [ep.metadata.name for ep in endpoints]
    assert ENDPOINT_NAME in names

@pytest.mark.dependency(name="describe", depends=["create"])
def test_get_endpoint():
    ep = HPEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    assert ep.modelName == MODEL_NAME

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
            ep = HPEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
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
    original_transform = codec.transform

    def mock_transform(data, shape, object_instance=None):
        if "Body" in data:
            return {"body": data["Body"].read().decode("utf-8")}
        return original_transform(data, shape, object_instance)

    monkeypatch.setattr("sagemaker_core.main.resources.transform", mock_transform)

    ep = HPEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    data = '{"question" :"what is the name of the planet?", "context":"mars"}'
    response = ep.invoke(body=data, content_type="application/list-text")
    
    assert "error" not in response.body.lower()


def test_get_operator_logs():
    ep = HPEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    logs = ep.get_operator_logs(since_hours=1)
    assert logs


def test_list_pods():
    ep = HPEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    pods = ep.list_pods(NAMESPACE)
    assert pods

@pytest.mark.dependency(depends=["create"])
def test_delete_endpoint():
    ep = HPEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    ep.delete()
