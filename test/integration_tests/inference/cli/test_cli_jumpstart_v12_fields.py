"""Integration test for v1.2 JumpStart endpoint new fields.

Creates a deployment with all new v1.2 flags, then verifies via describe/get
that the fields are persisted correctly in the CRD, then deletes.
"""
import pytest
from click.testing import CliRunner
from sagemaker.hyperpod.cli.commands.inference import (
    js_create,
    js_describe,
    js_delete,
)
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from test.integration_tests.utils import get_time_str

NAMESPACE = "integration"
VERSION = "1.2"


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


@pytest.fixture(scope="module")
def endpoint_name():
    return "js-v12-fields-" + get_time_str()


@pytest.mark.dependency(name="js_create_v12")
def test_create_with_v12_fields(runner, endpoint_name):
    """Create JumpStart endpoint with all new v1.2 fields."""
    result = runner.invoke(js_create, [
        "--namespace", NAMESPACE,
        "--version", VERSION,
        "--model-id", "deepseek-llm-r1-distill-qwen-1-5b",
        "--instance-type", "ml.g5.8xlarge",
        "--endpoint-name", endpoint_name,
        "--accept-eula", "True",
        # v1.2 new fields
        "--replicas", "1",
        "--max-deploy-time-in-seconds", "5400",
        "--execution-role", "arn:aws:iam::249127818294:role/test-role",
        "--metrics-enabled", "True",
        "--metrics-scrape-interval-seconds", "30",
        "--model-metrics-path", "/metrics",
        "--model-metrics-port", "8080",
        "--intelligent-routing-enabled", "False",
        "--routing-strategy", "roundrobin",
        "--enable-l1-cache", "True",
        "--enable-l2-cache", "True",
        "--l2-cache-backend", "redis",
        "--l2-cache-local-url", "redis://localhost:6379",
        "--cache-config-file", "/opt/config/kv.yaml",
        "--load-balancer-health-check-path", "/ping",
        "--load-balancer-routing-algorithm", "round_robin",
        "--env", '{"TEST_KEY":"test_value"}',
        "--additional-configs", '{"config1":"value1"}',
        "--auto-scaling-spec", '{"min_replica_count":1,"max_replica_count":5,"polling_interval":60}',
        "--custom-certificate-acm-arn", "arn:aws:acm:us-east-2:249127818294:certificate/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "--custom-certificate-domain-name", "test.example.com",
        "--gated-model-download-role", "arn:aws:iam::249127818294:role/gated-download",
        "--model-hub-name", "SageMakerPublicHub",
    ])
    assert result.exit_code == 0, result.output

    # Verify the CR was actually created on the cluster
    from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
    ep = HPJumpStartEndpoint.get(name=endpoint_name, namespace=NAMESPACE)
    assert ep is not None, f"Endpoint {endpoint_name} not found on cluster after creation"


@pytest.mark.dependency(name="js_verify_v12", depends=["js_create_v12"])
def test_verify_v12_fields_via_sdk(endpoint_name):
    """Get the endpoint via SDK and verify all new v1.2 fields are correct."""
    ep = HPJumpStartEndpoint.get(name=endpoint_name, namespace=NAMESPACE)

    # Basic fields
    assert ep.replicas == 1
    assert ep.maxDeployTimeInSeconds == 5400

    # Server
    assert ep.server.executionRole == "arn:aws:iam::249127818294:role/test-role"

    # Metrics
    assert ep.metrics.enabled is True
    assert ep.metrics.metricsScrapeIntervalSeconds == 30
    assert ep.metrics.modelMetrics.path == "/metrics"
    assert ep.metrics.modelMetrics.port == 8080

    # Intelligent routing
    assert ep.intelligentRoutingSpec.enabled is False
    assert ep.intelligentRoutingSpec.routingStrategy == "roundrobin"

    # KV cache
    assert ep.kvCacheSpec.enableL1Cache is True
    assert ep.kvCacheSpec.enableL2Cache is True
    assert ep.kvCacheSpec.l2CacheSpec.l2CacheBackend == "redis"
    assert ep.kvCacheSpec.l2CacheSpec.l2CacheLocalUrl == "redis://localhost:6379"
    assert ep.kvCacheSpec.cacheConfigFile == "/opt/config/kv.yaml"

    # Load balancer
    assert ep.loadBalancer.healthCheckPath == "/ping"
    assert ep.loadBalancer.routingAlgorithm == "round_robin"

    # Environment variables
    env_map = {e.name: e.value for e in ep.environmentVariables}
    assert env_map["TEST_KEY"] == "test_value"

    # Additional configs
    config_map = {c.name: c.value for c in ep.model.additionalConfigs}
    assert config_map["config1"] == "value1"

    # Model
    assert ep.model.gatedModelDownloadRole == "arn:aws:iam::249127818294:role/gated-download"
    assert ep.model.modelHubName == "SageMakerPublicHub"

    # Auto scaling spec
    assert ep.autoScalingSpec.minReplicaCount == 1
    assert ep.autoScalingSpec.maxReplicaCount == 5
    assert ep.autoScalingSpec.pollingInterval == 60

    # Custom certificate
    assert ep.tlsConfig.customCertificateConfig.acmArn == "arn:aws:acm:us-east-2:249127818294:certificate/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    assert ep.tlsConfig.customCertificateConfig.domainName == "test.example.com"


@pytest.mark.dependency(name="js_describe_v12", depends=["js_create_v12"])
def test_describe_shows_v12_fields(runner, endpoint_name):
    """Verify describe CLI output contains new v1.2 field values."""
    result = runner.invoke(js_describe, [
        "--name", endpoint_name,
        "--namespace", NAMESPACE,
        "--full",
    ])
    assert result.exit_code == 0
    output = result.output
    assert endpoint_name in output
    assert "5400" in output  # maxDeployTimeInSeconds


@pytest.mark.dependency(depends=["js_verify_v12", "js_describe_v12"])
def test_delete_v12_endpoint(runner, endpoint_name):
    """Clean up the test endpoint."""
    result = runner.invoke(js_delete, [
        "--name", endpoint_name,
        "--namespace", NAMESPACE,
    ])
    assert result.exit_code == 0
