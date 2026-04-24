"""Integration test for v1.2 custom endpoint new fields.

Creates a deployment with all new v1.2 flags, then verifies via describe/get
that the fields are persisted correctly in the CRD, then deletes.
No need to wait for InService — we only validate spec field round-trip.
"""
import pytest
from click.testing import CliRunner
from sagemaker.hyperpod.cli.commands.inference import (
    custom_create,
    custom_describe,
    custom_delete,
)
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint
from test.integration_tests.utils import get_time_str

NAMESPACE = "integration"
VERSION = "1.2"


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


@pytest.fixture(scope="module")
def endpoint_name():
    return "custom-v12-fields-" + get_time_str()


@pytest.mark.dependency(name="create_v12")
def test_create_with_v12_fields(runner, endpoint_name):
    """Create custom endpoint with all new v1.2 fields."""
    result = runner.invoke(custom_create, [
        "--namespace", NAMESPACE,
        "--version", VERSION,
        "--endpoint-name", endpoint_name,
        "--model-name", "v12-field-test",
        "--model-source-type", "s3",
        "--model-location", "test-model",
        "--s3-bucket-name", "sagemaker-hyperpod-beta-integ-test-model-bucket-n",
        "--s3-region", "us-east-2",
        "--instance-types", "ml.c5.2xlarge,ml.c5.4xlarge",
        "--image-uri", "763104351884.dkr.ecr.us-west-2.amazonaws.com/huggingface-pytorch-inference:2.3.0-transformers4.48.0-cpu-py311-ubuntu22.04",
        "--container-port", "8080",
        "--model-volume-mount-name", "model-weights",
        # v1.2 new fields
        "--replicas", "1",
        "--initial-replica-count", "1",
        "--max-deploy-time-in-seconds", "7200",
        "--invocation-endpoint", "invocations",
        "--worker-args", "--max-model-len,4096",
        "--worker-command", "python,-m,vllm.entrypoints.openai.api_server",
        "--working-dir", "/opt/ml",
        "--metrics-enabled", "True",
        "--metrics-scrape-interval-seconds", "30",
        "--model-metrics-path", "/metrics",
        "--model-metrics-port", "8080",
        "--max-concurrent-requests", "10",
        "--max-queue-size", "5",
        "--overflow-status-code", "503",
        "--load-balancer-health-check-path", "/ping",
        "--load-balancer-routing-algorithm", "round_robin",
        "--intelligent-routing-enabled", "False",
        "--enable-l1-cache", "True",
        "--instance-types", "ml.c5.2xlarge,ml.c5.4xlarge",
        "--kubernetes", '{"serviceAccountName":"default"}',
        "--tags", '{"team":"ml","env":"integ-test"}',
        "--node-affinity", '{"requiredDuringSchedulingIgnoredDuringExecution":{"nodeSelectorTerms":[{"matchExpressions":[{"key":"node.kubernetes.io/instance-type","operator":"In","values":["ml.c5.2xlarge"]}]}]}}',
        "--probes", '{"livenessProbe":{"httpGet":{"path":"/ping","port":8080},"periodSeconds":30}}',
        "--auto-scaling-spec", '{"minReplicaCount":1,"maxReplicaCount":3,"pollingInterval":60}',
        "--resources-requests", '{"cpu":"1","memory":"2Gi"}',
        "--resources-limits", '{"cpu":"2","memory":"4Gi","nvidia.com/gpu":"0"}',
        "--custom-certificate-acm-arn", "arn:aws:acm:us-east-2:249127818294:certificate/test-cert",
        "--custom-certificate-domain-name", "test.example.com",
    ])
    assert result.exit_code == 0, result.output


@pytest.mark.dependency(name="verify_v12", depends=["create_v12"])
def test_verify_v12_fields_via_sdk(endpoint_name):
    """Get the endpoint via SDK and verify all new v1.2 fields are correct."""
    ep = HPEndpoint.get(name=endpoint_name, namespace=NAMESPACE)

    # Basic fields
    assert ep.replicas == 1
    assert ep.InitialReplicaCount == 1
    assert ep.maxDeployTimeInSeconds == 7200
    assert ep.invocationEndpoint == "invocations"

    # Instance types (list, not single)
    assert ep.instanceTypes == ["ml.c5.2xlarge", "ml.c5.4xlarge"]

    # Worker fields
    assert ep.worker.args == ["--max-model-len", "4096"]
    assert ep.worker.command == ["python", "-m", "vllm.entrypoints.openai.api_server"]
    assert ep.worker.workingDir == "/opt/ml"

    # Metrics
    assert ep.metrics.enabled is True
    assert ep.metrics.metricsScrapeIntervalSeconds == 30
    assert ep.metrics.modelMetrics.path == "/metrics"
    assert ep.metrics.modelMetrics.port == 8080

    # Request limits
    assert ep.worker.requestLimits.maxConcurrentRequests == 10
    assert ep.worker.requestLimits.maxQueueSize == 5
    assert ep.worker.requestLimits.overflowStatusCode == 503

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

    # Resources
    assert ep.worker.resources.requests["cpu"] == "1"
    assert ep.worker.resources.limits["nvidia.com/gpu"] == "0"

    # Node affinity
    assert ep.nodeAffinity is not None
    terms = ep.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution.nodeSelectorTerms
    assert terms[0].matchExpressions[0].key == "node.kubernetes.io/instance-type"

    # Probes
    assert ep.worker.probes is not None
    assert ep.worker.probes.livenessProbe is not None

    # Auto scaling spec
    assert ep.autoScalingSpec.minReplicaCount == 1
    assert ep.autoScalingSpec.maxReplicaCount == 3
    assert ep.autoScalingSpec.pollingInterval == 60

    # Custom certificate
    assert ep.tlsConfig.customCertificateConfig.acmArn == "arn:aws:acm:us-east-2:249127818294:certificate/test-cert"
    assert ep.tlsConfig.customCertificateConfig.domainName == "test.example.com"


@pytest.mark.dependency(name="describe_v12", depends=["create_v12"])
def test_describe_shows_v12_fields(runner, endpoint_name):
    """Verify describe CLI output contains new v1.2 field values."""
    result = runner.invoke(custom_describe, [
        "--name", endpoint_name,
        "--namespace", NAMESPACE,
        "--full",
    ])
    assert result.exit_code == 0
    output = result.output
    assert endpoint_name in output
    assert "7200" in output  # maxDeployTimeInSeconds
    assert "round_robin" in output  # loadBalancer routing


@pytest.mark.dependency(depends=["verify_v12", "describe_v12"])
def test_delete_v12_endpoint(runner, endpoint_name):
    """Clean up the test endpoint."""
    result = runner.invoke(custom_delete, [
        "--name", endpoint_name,
        "--namespace", NAMESPACE,
    ])
    assert result.exit_code == 0
