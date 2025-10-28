import unittest
from unittest.mock import MagicMock, patch
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint
from sagemaker.hyperpod.inference.config.hp_endpoint_config import (
    CloudWatchTrigger,
    CloudWatchTriggerList,
    PrometheusTrigger,
    PrometheusTriggerList,
    Dimensions,
    AutoScalingSpec,
    IntelligentRoutingSpec,
    KvCacheSpec,
    L2CacheSpec,
    LoadBalancer,
    Metrics,
    S3Storage,
    ModelSourceConfig,
    TlsConfig,
    EnvironmentVariables,
    ModelInvocationPort,
    ModelVolumeMount,
    Resources,
    Worker,
)
from sagemaker.hyperpod.inference.config.constants import *
from sagemaker.hyperpod.common.config import Metadata


class TestHPEndpoint(unittest.TestCase):
    def setUp(self):
        tls_config = TlsConfig(
            tls_certificate_output_s3_uri="s3://tls-bucket-inf1-beta2"
        )

        model_source_config = ModelSourceConfig(
            model_source_type="s3",
            model_location="deepseek15b",
            s3_storage=S3Storage(
                bucket_name="test-model-s3-zhaoqi",
                region="us-east-2",
            ),
        )

        environment_variables = [
            EnvironmentVariables(name="HF_MODEL_ID", value="/opt/ml/model"),
            EnvironmentVariables(name="SAGEMAKER_PROGRAM", value="inference.py"),
            EnvironmentVariables(
                name="SAGEMAKER_SUBMIT_DIRECTORY", value="/opt/ml/model/code"
            ),
            EnvironmentVariables(name="MODEL_CACHE_ROOT", value="/opt/ml/model"),
            EnvironmentVariables(name="SAGEMAKER_ENV", value="1"),
        ]

        worker = Worker(
            image="763104351884.dkr.ecr.us-east-2.amazonaws.com/huggingface-pytorch-tgi-inference:2.4.0-tgi2.3.1-gpu-py311-cu124-ubuntu22.04-v2.0",
            model_volume_mount=ModelVolumeMount(
                name="model-weights",
            ),
            model_invocation_port=ModelInvocationPort(container_port=8080),
            resources=Resources(
                requests={"cpu": "30000m", "nvidia.com/gpu": 1, "memory": "100Gi"},
                limits={"nvidia.com/gpu": 1},
            ),
            environment_variables=environment_variables,
        )

        # Create dimensions
        dimensions = [
            Dimensions(name="EndpointName", value="test-endpoint-name-07-01-2"),
            Dimensions(name="VariantName", value="AllTraffic"),
        ]

        # Create CloudWatch trigger
        cloudwatch_trigger = CloudWatchTrigger(
            dimensions=dimensions,
            metric_collection_period=30,
            metric_name="Invocations",
            metric_stat="Sum",
            metric_type="Average",
            min_value=0.0,
            name="SageMaker-Invocations",
            namespace="AWS/SageMaker",
            target_value=10,
            use_cached_metrics=False,
        )

        # Create autoscaling spec
        auto_scaling_spec = AutoScalingSpec(cloud_watch_trigger=cloudwatch_trigger)

        # Create metrics
        metrics = Metrics(enabled=True)

        # Create intelligent routing spec
        intelligent_routing_spec = IntelligentRoutingSpec(
            enabled=True,
            routing_strategy="prefixaware",
            auto_scaling_spec=auto_scaling_spec
        )

        # Create KV cache spec
        l2_cache_spec = L2CacheSpec(
            l2_cache_backend="redis",
            l2_cache_local_url="redis://localhost:6379"
        )
        kv_cache_spec = KvCacheSpec(
            enable_l1_cache=True,
            enable_l2_cache=True,
            l2_cache_spec=l2_cache_spec
        )

        # Create load balancer
        load_balancer = LoadBalancer(
            health_check_path="/health",
            routing_algorithm="least_outstanding_requests"
        )

        self.endpoint = HPEndpoint(
            endpoint_name="s3-test-endpoint-name",
            instance_type="ml.g5.xlarge",
            model_name="deepseek15b-test-model-name",
            tls_config=tls_config,
            model_source_config=model_source_config,
            worker=worker,
            auto_scaling_spec=auto_scaling_spec,
            intelligent_routing_spec=intelligent_routing_spec,
            kv_cache_spec=kv_cache_spec,
            load_balancer=load_balancer,
            metrics=metrics,
        )

    @patch.object(HPEndpoint, "validate_instance_type")
    @patch.object(HPEndpoint, "call_create_api")
    @patch('sagemaker.hyperpod.inference.hp_endpoint.get_default_namespace', return_value='default')
    def test_create(self, mock_get_namespace, mock_create_api, mock_validate_instance_type):

        self.endpoint.create()

        mock_create_api.assert_called_once_with(
            metadata=unittest.mock.ANY,
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            spec=unittest.mock.ANY,
            debug=False,
        )
        self.assertEqual(self.endpoint.metadata.name, "s3-test-endpoint-name")

    @patch.object(HPEndpoint, "validate_instance_type")
    @patch.object(HPEndpoint, "call_create_api")
    def test_create_with_metadata(self, mock_create_api, mock_validate_instance_type):
        """Test create_from_dict uses metadata name and namespace when endpoint name not provided"""
        
        # Create endpoint without sageMakerEndpoint name to force using metadata
        endpoint_without_name = HPEndpoint(
            model_source_config = ModelSourceConfig(
                model_source_type="s3",
                model_location="deepseek15b",
                s3_storage=S3Storage(
                    bucket_name="test-model-s3-zhaoqi",
                    region="us-east-2",
                ),
            ),
            tls_config=TlsConfig(tls_certificate_output_s3_uri="s3://test-bucket"),
            metadata=Metadata(name="metadata-test-name", namespace="metadata-test-ns"),
            instance_type="ml.g5.xlarge",
            model_name="deepseek15b-test-model-name",
            worker=Worker(
                image="763104351884.dkr.ecr.us-east-2.amazonaws.com/huggingface-pytorch-tgi-inference:2.4.0-tgi2.3.1-gpu-py311-cu124-ubuntu22.04-v2.0",
                model_volume_mount=ModelVolumeMount(
                    name="model-weights",
                ),
                model_invocation_port=ModelInvocationPort(container_port=8080),
                resources=Resources(
                    requests={"cpu": "30000m", "nvidia.com/gpu": 1, "memory": "100Gi"},
                    limits={"nvidia.com/gpu": 1},
                )
            )
        )

        endpoint_without_name.create()

        # Verify it uses metadata name and namespace
        mock_create_api.assert_called_once()
        call_args = mock_create_api.call_args[1]
        assert call_args['metadata'].name == 'metadata-test-name'
        assert call_args['metadata'].namespace == 'metadata-test-ns'

    @patch.object(HPEndpoint, "validate_instance_type")
    @patch.object(HPEndpoint, "call_create_api")
    @patch('sagemaker.hyperpod.inference.hp_endpoint.get_default_namespace', return_value='default')
    def test_create_from_dict(self, mock_get_namespace, mock_create_api, mock_validate_instance_type):

        input_dict = self.endpoint.model_dump(exclude_none=True)

        self.endpoint.create_from_dict(input_dict)

        mock_create_api.assert_called_once()

    @patch.object(HPEndpoint, "call_get_api")
    def test_refresh(self, mock_get_api):
        self.endpoint.metadata = MagicMock()
        self.endpoint.metadata.name = "s3-test-endpoint-name"
        self.endpoint.metadata.namespace = "default"
        mock_get_api.return_value = {"status": {"state": "DeploymentComplete"}}

        result = self.endpoint.refresh()

        mock_get_api.assert_called_once_with(
            name="s3-test-endpoint-name", kind=INFERENCE_ENDPOINT_CONFIG_KIND, namespace="default"
        )
        self.assertEqual(result, self.endpoint)

    @patch.object(HPEndpoint, "get")
    @patch.object(HPEndpoint, "call_list_api")
    def test_list(self, mock_list_api, mock_get):
        mock_list_api.return_value = {
            "items": [{"metadata": {"name": "test-endpoint"}}]
        }
        mock_get.return_value = MagicMock()

        result = HPEndpoint.list(namespace="default")

        mock_list_api.assert_called_once_with(
            kind=INFERENCE_ENDPOINT_CONFIG_KIND, namespace="default"
        )
        mock_get.assert_called_once_with("test-endpoint", namespace="default")
        self.assertIsInstance(result, list)

    @patch.object(HPEndpoint, "call_get_api")
    def test_get(self, mock_get_api):
        mock_get_api.return_value = {
            "spec": self.endpoint.model_dump(exclude_none=True),
            "status": {"state": "DeploymentComplete"},
            "metadata": {"name": self.endpoint.modelName, "namespace": "default"},
        }

        result = HPEndpoint.get(self.endpoint.modelName, namespace="default")

        mock_get_api.assert_called_once_with(
            name=self.endpoint.modelName,
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace="default",
        )
        self.assertIsInstance(result, HPEndpoint)

    @patch.object(HPEndpoint, "call_delete_api")
    def test_delete(self, mock_delete_api):
        self.endpoint.metadata = MagicMock()
        self.endpoint.metadata.name = "test-name"
        self.endpoint.metadata.namespace = "default"

        self.endpoint.delete()

        mock_delete_api.assert_called_once_with(
            name="test-name", kind=INFERENCE_ENDPOINT_CONFIG_KIND, namespace="default"
        )

    @patch("sagemaker.hyperpod.common.utils.get_cluster_context")
    @patch("sagemaker_core.main.resources.Endpoint.get")
    def test_invoke(self, mock_endpoint_get, mock_get_cluster_context):

        mock_get_cluster_context.return_value = "test-cluster-arn"

        self.endpoint.endpointName = "test-endpoint"
        mock_endpoint = MagicMock()
        mock_endpoint.invoke.return_value = "response"
        mock_endpoint_get.return_value = mock_endpoint

        result = self.endpoint.invoke({"input": "test"})

        mock_endpoint_get.assert_called_once()
        mock_endpoint.invoke.assert_called_once_with(
            body={"input": "test"}, content_type="application/json"
        )
        self.assertEqual(result, "response")

    @patch.object(HPEndpoint, "call_list_api")
    @patch("kubernetes.client.CoreV1Api")
    @patch.object(HPEndpoint, "verify_kube_config")
    def test_list_pods(self, mock_verify_config, mock_core_api, mock_list_api):
        mock_pod1 = MagicMock()
        mock_pod1.metadata.name = "custom-endpoint-pod1"
        mock_pod1.metadata.labels = {"app": "custom-endpoint"}
        mock_pod2 = MagicMock()
        mock_pod2.metadata.name = "custom-endpoint-pod2"
        mock_pod2.metadata.labels = {"app": "custom-endpoint"}
        mock_pod3 = MagicMock()
        mock_pod3.metadata.name = "not-custom-endpoint-pod"
        mock_pod3.metadata.labels = {"app": "not-custom-endpoint"}
        mock_core_api.return_value.list_namespaced_pod.return_value.items = [
            mock_pod1,
            mock_pod2,
            mock_pod3,
        ]

        mock_list_api.return_value = {
            "items": [
                {
                    "metadata": {"name": "custom-endpoint"}
                }
            ]
        }

        result = self.endpoint.list_pods(namespace="default")

        self.assertEqual(result, ["custom-endpoint-pod1", "custom-endpoint-pod2"])
        mock_core_api.return_value.list_namespaced_pod.assert_called_once_with(
            namespace="default"
        )

    @patch("kubernetes.client.CoreV1Api")
    @patch.object(HPEndpoint, "verify_kube_config")
    def test_list_pods_with_endpoint_name(self, mock_verify_config, mock_core_api):
        mock_pod1 = MagicMock()
        mock_pod1.metadata.name = "custom-endpoint1-pod1"
        mock_pod1.metadata.labels = {"app": "custom-endpoint1"}
        mock_pod2 = MagicMock()
        mock_pod2.metadata.name = "custom-endpoint1-pod2"
        mock_pod2.metadata.labels = {"app": "custom-endpoint1"}
        mock_pod3 = MagicMock()
        mock_pod3.metadata.name = "custom-endpoint2-pod2"
        mock_pod3.metadata.labels = {"app": "custom-endpoint2"}
        mock_core_api.return_value.list_namespaced_pod.return_value.items = [
            mock_pod1,
            mock_pod2,
            mock_pod3,
        ]

        result = self.endpoint.list_pods(namespace="default", endpoint_name="custom-endpoint1")

        self.assertEqual(result, ["custom-endpoint1-pod1", "custom-endpoint1-pod2"])
        mock_core_api.return_value.list_namespaced_pod.assert_called_once_with(
            namespace="default"
        )
