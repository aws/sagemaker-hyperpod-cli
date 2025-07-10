import time
import uuid
import json
import pytest
import boto3

from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint
from sagemaker.hyperpod.inference.config.hp_endpoint_config import (
    ModelSourceConfig, S3Storage, TlsConfig, Worker, ModelVolumeMount,
    ModelInvocationPort, Resources, EnvironmentVariables, AutoScalingSpec,
    CloudWatchTrigger, Dimensions, Metrics
)
import sagemaker_core.main.code_injection.codec as codec

# --------- Test Configuration ---------
NAMESPACE = "integration"
REGION = "us-east-2"
ENDPOINT_NAME = f"custom-sdk-integration"

MODEL_NAME = f"ds-model-integration"
S3_BUCKET = "test-model-s3-zhaoqi"
MODEL_LOCATION = "deepseek15b"
IMAGE_URI = "763104351884.dkr.ecr.us-east-2.amazonaws.com/huggingface-pytorch-tgi-inference:2.4.0-tgi2.3.1-gpu-py311-cu124-ubuntu22.04-v2.0"
TLS_URI = "s3://tls-bucket-inf1-beta2"

TIMEOUT_MINUTES = 15
POLL_INTERVAL_SECONDS = 30

@pytest.fixture(scope="module")
def sagemaker_client():
    return boto3.client("sagemaker", region_name=REGION)

@pytest.fixture(scope="module")
def custom_endpoint():
    # TLS
    tls = TlsConfig(tls_certificate_output_s3_uri=TLS_URI)

    # Model Source
    model_src = ModelSourceConfig(
        model_source_type="s3",
        model_location=MODEL_LOCATION,
        s3_storage=S3Storage(
            bucket_name=S3_BUCKET,
            region=REGION
        )
    )

    # Env vars
    env_vars = [
        EnvironmentVariables(name="HF_MODEL_ID", value="/opt/ml/model"),
        EnvironmentVariables(name="SAGEMAKER_PROGRAM", value="inference.py"),
        EnvironmentVariables(name="SAGEMAKER_SUBMIT_DIRECTORY", value="/opt/ml/model/code"),
        EnvironmentVariables(name="MODEL_CACHE_ROOT", value="/opt/ml/model"),
        EnvironmentVariables(name="SAGEMAKER_ENV", value="1"),
    ]

    # Worker
    worker = Worker(
        image=IMAGE_URI,
        model_volume_mount=ModelVolumeMount(name="model-weights"),
        model_invocation_port=ModelInvocationPort(container_port=8080),
        resources=Resources(
            requests={"cpu": "30000m", "nvidia.com/gpu": 1, "memory": "100Gi"},
            limits={"nvidia.com/gpu": 1}
        ),
        environment_variables=env_vars
    )

    # AutoScaling
    dimensions = [
        Dimensions(name="EndpointName", value=ENDPOINT_NAME),
        Dimensions(name="VariantName", value="AllTraffic"),
    ]
    cw_trigger = CloudWatchTrigger(
        dimensions=dimensions,
        metric_collection_period=30,
        metric_name="Invocations",
        metric_stat="Sum",
        metric_type="Average",
        min_value=0.0,
        name="SageMaker-Invocations",
        namespace="AWS/SageMaker",
        target_value=10,
        use_cached_metrics=True
    )
    auto_scaling = AutoScalingSpec(cloud_watch_trigger=cw_trigger)

    # Metrics
    metrics = Metrics(enabled=True)

    return HPEndpoint(
        endpoint_name=ENDPOINT_NAME,
        instance_type="ml.g5.8xlarge",
        model_name=MODEL_NAME,
        tls_config=tls,
        model_source_config=model_src,
        worker=worker,
        auto_scaling_spec=auto_scaling,
        metrics=metrics
    )

def test_create_endpoint(custom_endpoint):
    custom_endpoint.create(namespace=NAMESPACE)
    assert custom_endpoint.metadata.name == ENDPOINT_NAME

def test_list_endpoint():
    endpoints = HPEndpoint.list(namespace=NAMESPACE)
    names = [ep.metadata.name for ep in endpoints]
    assert ENDPOINT_NAME in names

def test_get_endpoint():
    ep = HPEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    assert ep.modelName == MODEL_NAME

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

def test_invoke_endpoint(monkeypatch):
    original_transform = codec.transform  # Save original

    def mock_transform(data, shape, object_instance=None):
        if "Body" in data:
            return {"body": data["Body"].read().decode("utf-8")}
        return original_transform(data, shape, object_instance)  # Call original

    monkeypatch.setattr("sagemaker_core.main.resources.transform", mock_transform)

    ep = HPEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    data = '{"inputs":"What is the capital of USA?"}'
    response = ep.invoke(body=data)
    
    assert "error" not in response.body.lower()


def test_get_operator_logs():
    ep = HPEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    logs = ep.get_operator_logs(since_hours=1)
    assert logs


def test_list_pods():
    ep = HPEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    pods = ep.list_pods(NAMESPACE)
    assert pods


def test_delete_endpoint():
    ep = HPEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    ep.delete()
