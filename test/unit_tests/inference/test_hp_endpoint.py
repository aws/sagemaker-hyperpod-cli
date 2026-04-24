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
    Kubernetes,
    CustomCertificateConfig,
    NodeAffinity,
    NodeSelectorTerm,
    NodeSelectorRequirement,
    NodeSelector,
    PreferredSchedulingTerm,
    Probe,
    Probes,
    RequestLimits,
    Tags,
    HuggingFaceModel,
    TokenSecretRef,
    DataCapture,
    DataCaptureLoadBalancer,
    DataCaptureModelPod,
    DataCaptureSagemakerEndpoint,
    CaptureOptions,
    CaptureContentTypeHeader,
    BufferConfig,
    PayloadConfig,
    DnsConfig,
    DnsStatus,
    InferenceEndpointConfigStatus,
    TlsCertificate,
    Status,
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


class TestServiceAccountName(unittest.TestCase):
    def test_kubernetes_with_service_account_name(self):
        k8s = Kubernetes(service_account_name="my-inference-sa", scheduler_name="default-scheduler")
        self.assertEqual(k8s.serviceAccountName, "my-inference-sa")

    def test_kubernetes_service_account_name_camel_case(self):
        k8s = Kubernetes(serviceAccountName="my-sa")
        self.assertEqual(k8s.serviceAccountName, "my-sa")

    def test_kubernetes_service_account_name_none_by_default(self):
        k8s = Kubernetes()
        self.assertIsNone(k8s.serviceAccountName)


class TestHuggingFaceModelConfig(unittest.TestCase):
    def test_huggingface_model_basic(self):
        hf = HuggingFaceModel(model_id="meta-llama/Llama-3.1-8B-Instruct")
        self.assertEqual(hf.modelId, "meta-llama/Llama-3.1-8B-Instruct")
        self.assertIsNone(hf.commitSHA)
        self.assertIsNone(hf.tokenSecretRef)

    def test_huggingface_model_with_token(self):
        hf = HuggingFaceModel(
            model_id="meta-llama/Llama-3.1-8B-Instruct",
            commit_sha="a" * 40,
            token_secret_ref=TokenSecretRef(name="hf-secret", key="token"),
        )
        self.assertEqual(hf.commitSHA, "a" * 40)
        self.assertEqual(hf.tokenSecretRef.name, "hf-secret")

    def test_model_source_config_huggingface(self):
        src = ModelSourceConfig(
            model_source_type="huggingface",
            hugging_face_model=HuggingFaceModel(model_id="meta-llama/Llama-3.1-8B-Instruct"),
        )
        self.assertEqual(src.modelSourceType, "huggingface")
        self.assertIsNotNone(src.huggingFaceModel)

    def test_model_source_config_kubernetes_volume(self):
        src = ModelSourceConfig(model_source_type="kubernetesVolume", model_location="/mnt/models/my-model")
        self.assertEqual(src.modelSourceType, "kubernetesVolume")


class TestDataCaptureConfig(unittest.TestCase):
    def test_data_capture_sagemaker_endpoint(self):
        dc = DataCapture(sagemaker_endpoint=DataCaptureSagemakerEndpoint(enabled=True))
        self.assertTrue(dc.sagemakerEndpoint.enabled)

    def test_data_capture_model_pod(self):
        dc = DataCapture(
            model_pod=DataCaptureModelPod(
                enabled=True, initial_sampling_percentage=50,
                buffer_config=BufferConfig(batch_size=20, flush_interval_seconds=120),
                capture_options=[CaptureOptions(capture_mode="Input"), CaptureOptions(capture_mode="Output")],
            ),
            s3_uri="s3://my-bucket/captures",
        )
        self.assertTrue(dc.modelPod.enabled)
        self.assertEqual(dc.modelPod.bufferConfig.batchSize, 20)
        self.assertEqual(len(dc.modelPod.captureOptions), 2)

    def test_data_capture_full(self):
        dc = DataCapture(
            sagemaker_endpoint=DataCaptureSagemakerEndpoint(
                enabled=True,
                capture_content_type_header=CaptureContentTypeHeader(
                    csv_content_types=["text/csv"], json_content_types=["application/json"],
                ),
            ),
            load_balancer=DataCaptureLoadBalancer(enabled=False),
            model_pod=DataCaptureModelPod(
                enabled=True, payload_config=PayloadConfig(max_payload_size_kb=1024),
                kms_key_id="arn:aws:kms:us-east-2:123:key/abc",
            ),
            s3_uri="s3://bucket/prefix",
        )
        self.assertEqual(dc.sagemakerEndpoint.captureContentTypeHeader.csvContentTypes, ["text/csv"])
        self.assertFalse(dc.loadBalancer.enabled)
        self.assertEqual(dc.modelPod.payloadConfig.maxPayloadSizeKB, 1024)


class TestDnsConfigAndStatus(unittest.TestCase):
    def test_dns_config(self):
        dns = DnsConfig(hosted_zone_id="Z1234567890")
        self.assertEqual(dns.hostedZoneId, "Z1234567890")

    def test_dns_status(self):
        ds = DnsStatus(dns_health="Active", hosted_zone_id="Z123", managed_by_operator=True, record_name="test.example.com")
        self.assertEqual(ds.dnsHealth, "Active")
        self.assertTrue(ds.managedByOperator)

    def test_inference_status_with_dns(self):
        status = InferenceEndpointConfigStatus(dns_status=DnsStatus(managed_by_operator=True, dns_health="Pending"))
        self.assertEqual(status.dnsStatus.dnsHealth, "Pending")
