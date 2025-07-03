import unittest
from unittest.mock import MagicMock, patch
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint
from sagemaker.hyperpod.inference.config.hp_endpoint_config import CloudWatchTrigger, Dimensions, PrometheusTrigger, AutoScalingSpec, ModelMetrics, Metrics, FsxStorage, S3Storage, ModelSourceConfig, Tags, TlsConfig, ConfigMapKeyRef, FieldRef, ResourceFieldRef, SecretKeyRef, ValueFrom, EnvironmentVariables, ModelInvocationPort, ModelVolumeMount, Claims, Resources, Worker
from sagemaker.hyperpod.inference.config.constants import *


class TestHPEndpoint(unittest.TestCase):
    def setUp(self):
        tls_config=TlsConfig(tls_certificate_output_s3_uri='s3://tls-bucket-inf1-beta2')

        model_source_config = ModelSourceConfig(
            model_source_type='s3',
            model_location="deepseek15b",
            s3_storage=S3Storage(
                bucket_name='test-model-s3-zhaoqi',
                region='us-east-2',
            ),
        )

        environment_variables = [
            EnvironmentVariables(name="HF_MODEL_ID", value="/opt/ml/model"),
            EnvironmentVariables(name="SAGEMAKER_PROGRAM", value="inference.py"),
            EnvironmentVariables(name="SAGEMAKER_SUBMIT_DIRECTORY", value="/opt/ml/model/code"),
            EnvironmentVariables(name="MODEL_CACHE_ROOT", value="/opt/ml/model"),
            EnvironmentVariables(name="SAGEMAKER_ENV", value="1"),
        ]

        worker = Worker(
            image='763104351884.dkr.ecr.us-east-2.amazonaws.com/huggingface-pytorch-tgi-inference:2.4.0-tgi2.3.1-gpu-py311-cu124-ubuntu22.04-v2.0',
            model_volume_mount=ModelVolumeMount(
                name='model-weights',
            ),
            model_invocation_port=ModelInvocationPort(container_port=8080),
            resources=Resources(
                    requests={"cpu": "30000m", "nvidia.com/gpu": 1, "memory": "100Gi"},
                    limits={"nvidia.com/gpu": 1}
            ),
            environment_variables=environment_variables,
        )

        # Create dimensions
        dimensions = [
            Dimensions(name="EndpointName", value="test-endpoint-name-07-01-2"),
            Dimensions(name="VariantName", value="AllTraffic")
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
            use_cached_metrics=False
        )

        # Create autoscaling spec
        auto_scaling_spec = AutoScalingSpec(
            cloud_watch_trigger=cloudwatch_trigger
        )

        # Create metrics
        metrics = Metrics(enabled=True)

        self.endpoint = HPEndpoint(
            endpoint_name='s3-test-endpoint-name',
            instance_type='ml.g5.8xlarge',
            model_name='deepseek15b-test-model-name',  
            tls_config=tls_config,
            model_source_config=model_source_config,
            worker=worker,
            auto_scaling_spec=auto_scaling_spec,
            metrics=metrics,
        )

    @patch.object(HPEndpoint, "call_create_api")
    def test_create(self, mock_create_api):
        self.endpoint.modelName = "test-model"
        
        self.endpoint.create(name="test-name", namespace="test-ns")
        
        mock_create_api.assert_called_once_with(
            name="test-name",
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace="test-ns",
            spec=unittest.mock.ANY
        )
        self.assertEqual(self.endpoint.metadata.name, "test-name")

    @patch.object(HPEndpoint, "call_create_api")
    def test_create_from_dict(self, mock_create_api):
        input_dict = self.endpoint.model_dump(exclude_none=True)
        
        self.endpoint.create_from_dict(input_dict, namespace="test-ns")
        
        mock_create_api.assert_called_once()

    @patch.object(HPEndpoint, "call_get_api")
    def test_refresh(self, mock_get_api):
        self.endpoint.metadata = MagicMock()
        self.endpoint.metadata.name = "test-name"
        self.endpoint.metadata.namespace = "test-ns"
        mock_get_api.return_value = {"status": {"state": "DeploymentComplete"}}
        
        result = self.endpoint.refresh()
        
        mock_get_api.assert_called_once_with(
            name="test-name",
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace="test-ns"
        )
        self.assertEqual(result, self.endpoint)

    @patch.object(HPEndpoint, "get")
    @patch.object(HPEndpoint, "call_list_api")
    def test_list(self, mock_list_api, mock_get):
        mock_list_api.return_value = {"items": [{"metadata": {"name": "test-endpoint"}}]}
        mock_get.return_value = MagicMock()
        
        result = HPEndpoint.list(namespace="test-ns")
        
        mock_list_api.assert_called_once_with(
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace="test-ns"
        )
        mock_get.assert_called_once_with("test-endpoint", namespace="test-ns")
        self.assertIsInstance(result, list)

    @patch.object(HPEndpoint, "call_get_api")
    def test_get(self, mock_get_api):
        mock_get_api.return_value = {
            "spec": self.endpoint.model_dump(exclude_none=True),
            "status": {"state": "DeploymentComplete"},
            "metadata": {"name": self.endpoint.modelName, "namespace": "test-ns"}
        }
        
        result = HPEndpoint.get(self.endpoint.modelName, namespace="test-ns")
        
        mock_get_api.assert_called_once_with(
            name=self.endpoint.modelName,
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace="test-ns"
        )
        self.assertIsInstance(result, HPEndpoint)

    @patch.object(HPEndpoint, "call_delete_api")
    def test_delete(self, mock_delete_api):
        self.endpoint.metadata = MagicMock()
        self.endpoint.metadata.name = "test-name"
        self.endpoint.metadata.namespace = "test-ns"
        
        self.endpoint.delete()
        
        mock_delete_api.assert_called_once_with(
            name="test-name",
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace="test-ns"
        )

    @patch("sagemaker_core.main.resources.Endpoint.get")
    def test_invoke(self, mock_endpoint_get):
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