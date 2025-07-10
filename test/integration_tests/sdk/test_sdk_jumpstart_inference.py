import time
import uuid
import json
import pytest
import boto3

from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import (
    Model, Server, SageMakerEndpoint, TlsConfig
)

# --------- Config ---------
NAMESPACE = "integration"
REGION = "us-east-2"
ENDPOINT_NAME = "js-sdk-integration"

INSTANCE_TYPE = "ml.g5.8xlarge"
MODEL_ID = "deepseek-llm-r1-distill-qwen-1-5b"
MODEL_VERSION = "2.0.4"
TLS_S3_URI = "s3://tls-bucket-inf1-beta2"

TIMEOUT_MINUTES = 15
POLL_INTERVAL_SECONDS = 30

@pytest.fixture(scope="module")
def sagemaker_client():
    return boto3.client("sagemaker", region_name=REGION)

@pytest.fixture(scope="module")
def endpoint_obj():
    model = Model(model_id=MODEL_ID, model_version=MODEL_VERSION)
    server = Server(instance_type=INSTANCE_TYPE)
    sm_endpoint = SageMakerEndpoint(name=ENDPOINT_NAME)
    tls = TlsConfig(tls_certificate_output_s3_uri=TLS_S3_URI)

    return HPJumpStartEndpoint(model=model, server=server, sage_maker_endpoint=sm_endpoint, tls_config=tls)

def test_create_endpoint(endpoint_obj):
    endpoint_obj.create(namespace=NAMESPACE)
    assert endpoint_obj.metadata.name == ENDPOINT_NAME

def test_list_endpoint():
    endpoints = HPJumpStartEndpoint.list(namespace=NAMESPACE)
    names = [ep.metadata.name for ep in endpoints]
    assert ENDPOINT_NAME in names

def test_get_endpoint():
    ep = HPJumpStartEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    assert ep.metadata.name == ENDPOINT_NAME
    assert ep.model.modelId == MODEL_ID

def test_wait_until_inservice():
    """Poll SDK until specific JumpStart endpoint reaches DeploymentComplete"""
    print(f"Waiting for JumpStart endpoint '{ENDPOINT_NAME}' to be DeploymentComplete...")
    deadline = time.time() + (TIMEOUT_MINUTES * 60)

    while time.time() < deadline:
        try:
            ep = HPJumpStartEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
            state = ep.status.deploymentStatus.deploymentObjectOverallState
            if state == "DeploymentComplete":
                return
            elif state == "DeploymentFailed":
                pytest.fail("Endpoint deployment failed.")
        except Exception as e:
            print(f"Error polling endpoint status: {e}")

        time.sleep(POLL_INTERVAL_SECONDS)

    pytest.fail("Timed out waiting for endpoint to be DeploymentComplete")

def test_invoke_endpoint():
    ep = HPJumpStartEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    payload = '{"inputs": "What is the capital of USA?"}'
    response = ep.invoke(payload)
    assert "error" not in str(response).lower()
    time.sleep(5)

def test_get_operator_logs():
    ep = HPJumpStartEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    logs = ep.get_operator_logs(since_hours=1)
    assert logs
    time.sleep(5)

def test_list_pods(runner):
    ep = HPJumpStartEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    pods = ep.list_pods(NAMESPACE)
    assert pods
    time.sleep(5)

def test_delete_endpoint():
    ep = HPJumpStartEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    ep.delete()
