"""Integration test for v1.2 custom endpoint new fields via SDK.

Creates a deployment with all new v1.2 SDK fields, verifies via get,
then deletes. No need to wait for InService.
"""
import pytest
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint
from sagemaker.hyperpod.inference.config.hp_endpoint_config import (
    ModelSourceConfig, S3Storage, TlsConfig, Worker, ModelVolumeMount,
    ModelInvocationPort, Resources, EnvironmentVariables, Metrics, ModelMetrics,
    LoadBalancer, IntelligentRoutingSpec, KvCacheSpec, Kubernetes,
    RequestLimits, Probes, Tags,
)
from sagemaker.hyperpod.common.config.metadata import Metadata
from test.integration_tests.utils import get_time_str

NAMESPACE = "integration"
ENDPOINT_NAME = "custom-sdk-v12-" + get_time_str()


@pytest.fixture(scope="module")
def custom_endpoint():
    metadata = Metadata(name=ENDPOINT_NAME, namespace=NAMESPACE)

    model_src = ModelSourceConfig(
        model_source_type="s3",
        model_location="test-model",
        s3_storage=S3Storage(
            bucket_name="sagemaker-hyperpod-beta-integ-test-model-bucket-n",
            region="us-east-2",
        ),
    )

    worker = Worker(
        image="763104351884.dkr.ecr.us-west-2.amazonaws.com/huggingface-pytorch-inference:2.3.0-transformers4.48.0-cpu-py311-ubuntu22.04",
        model_volume_mount=ModelVolumeMount(name="model-weights"),
        model_invocation_port=ModelInvocationPort(container_port=8080),
        resources=Resources(
            requests={"cpu": "1", "memory": "2Gi"},
            limits={"cpu": "2", "memory": "4Gi", "nvidia.com/gpu": "0"},
        ),
        environment_variables=[
            EnvironmentVariables(name="SAGEMAKER_PROGRAM", value="inference.py"),
        ],
        args=["--max-model-len", "4096"],
        working_dir="/opt/ml",
        request_limits=RequestLimits(
            max_concurrent_requests=10,
            max_queue_size=5,
            overflow_status_code=503,
        ),
    )

    return HPEndpoint(
        metadata=metadata,
        endpoint_name=ENDPOINT_NAME,
        instance_type="ml.c5.2xlarge",
        model_name="v12-sdk-field-test",
        model_source_config=model_src,
        worker=worker,
        replicas=1,
        max_deploy_time_in_seconds=7200,
        metrics=Metrics(
            enabled=True,
            metrics_scrape_interval_seconds=30,
            model_metrics=ModelMetrics(path="/metrics", port=8080),
        ),
        load_balancer=LoadBalancer(
            health_check_path="/ping",
            routing_algorithm="round_robin",
        ),
        intelligent_routing_spec=IntelligentRoutingSpec(enabled=False),
        kv_cache_spec=KvCacheSpec(enable_l1_cache=True),
        kubernetes=Kubernetes(service_account_name="default"),
        tags=[Tags(name="team", value="ml"), Tags(name="env", value="integ-test")],
    )


@pytest.mark.dependency(name="sdk_create_v12")
def test_create_endpoint(custom_endpoint):
    custom_endpoint.create()
    assert custom_endpoint.metadata.name == ENDPOINT_NAME


@pytest.mark.dependency(name="sdk_verify_v12", depends=["sdk_create_v12"])
def test_verify_v12_fields():
    """Get endpoint and verify all new v1.2 fields."""
    ep = HPEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)

    assert ep.replicas == 1
    assert ep.maxDeployTimeInSeconds == 7200

    # Worker
    assert ep.worker.args == ["--max-model-len", "4096"]
    assert ep.worker.workingDir == "/opt/ml"
    assert ep.worker.requestLimits.maxConcurrentRequests == 10
    assert ep.worker.requestLimits.maxQueueSize == 5
    assert ep.worker.requestLimits.overflowStatusCode == 503

    # Metrics
    assert ep.metrics.enabled is True
    assert ep.metrics.metricsScrapeIntervalSeconds == 30
    assert ep.metrics.modelMetrics.path == "/metrics"

    # Load balancer
    assert ep.loadBalancer.healthCheckPath == "/ping"
    assert ep.loadBalancer.routingAlgorithm == "round_robin"

    # Intelligent routing
    assert ep.intelligentRoutingSpec.enabled is False

    # KV cache
    assert ep.kvCacheSpec.enableL1Cache is True

    # Kubernetes
    assert ep.kubernetes.serviceAccountName == "default"

    # Tags
    tag_map = {t.name: t.value for t in ep.tags}
    assert tag_map["team"] == "ml"
    assert tag_map["env"] == "integ-test"


@pytest.mark.dependency(depends=["sdk_verify_v12"])
def test_delete_endpoint():
    ep = HPEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    ep.delete()
