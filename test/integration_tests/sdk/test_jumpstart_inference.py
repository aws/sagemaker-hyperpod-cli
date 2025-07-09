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
INSTANCE_TYPE = "ml.g5.8xlarge"
MODEL_ID = "deepseek-llm-r1-distill-qwen-1-5b"
MODEL_VERSION = "2.0.4"
TLS_S3_URI = "s3://tls-bucket-inf1-beta2"
TIMEOUT_MINUTES = 15
POLL_INTERVAL_SECONDS = 30

@pytest.fixture(scope="module")
def endpoint_name():
    return f"js-sdk-integration"

@pytest.fixture(scope="module")
def sagemaker_client():
    return boto3.client("sagemaker")

@pytest.fixture(scope="module")
def endpoint_obj(endpoint_name):
    model = Model(model_id=MODEL_ID, model_version=MODEL_VERSION)
    server = Server(instance_type=INSTANCE_TYPE)
    sm_endpoint = SageMakerEndpoint(name=endpoint_name)
    tls = TlsConfig(tls_certificate_output_s3_uri=TLS_S3_URI)

    return HPJumpStartEndpoint(model=model, server=server, sage_maker_endpoint=sm_endpoint, tls_config=tls)

def test_create_endpoint(endpoint_obj):
    endpoint_obj.create(namespace=NAMESPACE)
    assert endpoint_obj.metadata.name.startswith("js-sdk-integration")

def test_list_endpoint(endpoint_name):
    endpoints = HPJumpStartEndpoint.list(namespace=NAMESPACE)
    names = [ep.metadata.name for ep in endpoints]
    assert endpoint_name in names

def test_get_endpoint(endpoint_name):
    ep = HPJumpStartEndpoint.get(endpoint_name, namespace=NAMESPACE)
    assert ep.metadata.name == endpoint_name
    assert ep.model.modelId == MODEL_ID

def test_js_wait_until_inservice(js_endpoint_name):
    """Poll SDK until specific JumpStart endpoint reaches DeploymentComplete"""
    print(f"Waiting for JumpStart endpoint '{js_endpoint_name}' to be DeploymentComplete...")
    deadline = time.time() + (TIMEOUT_MINUTES * 60)

    while time.time() < deadline:
        try:
            endpoints = HPJumpStartEndpoint.model_construct().list(NAMESPACE)
            for ep in endpoints:
                data = ep.model_dump()
                name = data.get("metadata", {}).get("name", "")
                if name != js_endpoint_name:
                    continue
                state = data.get("status", {}).get("deploymentStatus", {}).get("deploymentObjectOverallState", "")
                print(f"Current state for {name}: {state}")
                if state == "DeploymentComplete":
                    return
                elif state == "DeploymentFailed":
                    pytest.fail("Endpoint deployment failed.")
                break 
        except Exception as e:
            print(f"Error polling endpoint status: {e}")

        time.sleep(POLL_INTERVAL_SECONDS)

    pytest.fail("Timed out waiting for endpoint to be DeploymentComplete")

def test_invoke_endpoint(endpoint_obj):
    payload = {"inputs": "What is the capital of USA?"}
    response = endpoint_obj.invoke(payload)
    assert "error" not in str(response).lower()

def test_get_operator_logs(endpoint_obj):
    logs = endpoint_obj.get_operator_logs(since_hours=1)
    assert logs

def test_delete_endpoint(endpoint_obj):
    endpoint_obj.delete()
