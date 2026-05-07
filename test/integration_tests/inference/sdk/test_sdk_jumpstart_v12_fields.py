"""Integration test for v1.2 JumpStart endpoint new fields via SDK.

Creates a deployment with all new v1.2 SDK fields, verifies via get,
then deletes. No need to wait for InService.
"""
import pytest
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import (
    Model, Server, SageMakerEndpoint, Metrics, ModelMetrics,
    EnvironmentVariables, IntelligentRoutingSpec, KvCacheSpec, LoadBalancer,
)
from sagemaker.hyperpod.common.config.metadata import Metadata
from test.integration_tests.utils import get_time_str

NAMESPACE = "integration"
ENDPOINT_NAME = "js-sdk-v12-" + get_time_str()


@pytest.fixture(scope="module")
def endpoint_obj():
    metadata = Metadata(name=ENDPOINT_NAME, namespace=NAMESPACE)

    return HPJumpStartEndpoint(
        metadata=metadata,
        model=Model(model_id="deepseek-llm-r1-distill-qwen-1-5b", accept_eula=True),
        server=Server(instance_type="ml.g5.8xlarge"),
        sage_maker_endpoint=SageMakerEndpoint(name=ENDPOINT_NAME),
        replicas=1,
        max_deploy_time_in_seconds=5400,
        metrics=Metrics(
            enabled=True,
            metrics_scrape_interval_seconds=30,
            model_metrics=ModelMetrics(path="/metrics", port=8080),
        ),
        intelligent_routing_spec=IntelligentRoutingSpec(enabled=False),
        kv_cache_spec=KvCacheSpec(enable_l1_cache=True),
        load_balancer=LoadBalancer(
            health_check_path="/ping",
            routing_algorithm="round_robin",
        ),
        environment_variables=[
            EnvironmentVariables(name="TEST_KEY", value="test_value"),
        ],
    )


@pytest.mark.dependency(name="js_sdk_create_v12")
def test_create_endpoint(endpoint_obj):
    endpoint_obj.create()
    assert endpoint_obj.metadata.name == ENDPOINT_NAME


@pytest.mark.dependency(name="js_sdk_verify_v12", depends=["js_sdk_create_v12"])
def test_verify_v12_fields():
    """Get endpoint and verify all new v1.2 fields."""
    ep = HPJumpStartEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)

    assert ep.replicas == 1
    assert ep.maxDeployTimeInSeconds == 5400

    # Metrics
    assert ep.metrics.enabled is True
    assert ep.metrics.metricsScrapeIntervalSeconds == 30
    assert ep.metrics.modelMetrics.path == "/metrics"
    assert ep.metrics.modelMetrics.port == 8080

    # Intelligent routing
    assert ep.intelligentRoutingSpec.enabled is False

    # KV cache
    assert ep.kvCacheSpec.enableL1Cache is True

    # Load balancer
    assert ep.loadBalancer.healthCheckPath == "/ping"
    assert ep.loadBalancer.routingAlgorithm == "round_robin"

    # Environment variables
    env_map = {e.name: e.value for e in ep.environmentVariables}
    assert env_map["TEST_KEY"] == "test_value"


@pytest.mark.dependency(depends=["js_sdk_verify_v12"])
def test_delete_endpoint():
    ep = HPJumpStartEndpoint.get(name=ENDPOINT_NAME, namespace=NAMESPACE)
    ep.delete()
