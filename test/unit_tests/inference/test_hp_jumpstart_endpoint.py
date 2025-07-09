import unittest
from unittest.mock import MagicMock, patch
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.config.constants import *
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import (
    Model,
    Server,
    SageMakerEndpoint,
    TlsConfig,
    EnvironmentVariables,
)


class TestHPJumpStartEndpoint(unittest.TestCase):
    def setUp(self):

        # create configs
        model = Model(
            model_id="huggingface-eqa-bert-base-cased",
        )
        server = Server(
            instance_type="ml.c5.2xlarge",
        )
        endpoint_name = SageMakerEndpoint(name="bert-testing-jumpstart-7-2-2")
        tls_config = TlsConfig(
            tls_certificate_output_s3_uri="s3://bugbash-02-bucket-269413952707-us-east-2"
        )

        # create spec
        self.endpoint = HPJumpStartEndpoint(
            model=model,
            server=server,
            sage_maker_endpoint=endpoint_name,
            tls_config=tls_config,
        )

    @patch("sagemaker.hyperpod.hyperpod_manager.HyperPodManager.get_current_cluster")
    @patch("sagemaker.hyperpod.hyperpod_manager.HyperPodManager.get_current_region")
    @patch("sagemaker.hyperpod.common.utils.get_cluster_instance_types")
    @patch("sagemaker.hyperpod.common.utils.get_jumpstart_model_instance_types")
    @patch.object(HPJumpStartEndpoint, "call_create_api")
    def test_create(
        self,
        mock_create_api,
        mock_get_model_types,
        mock_get_cluster_types,
        mock_get_region,
        mock_get_cluster,
    ):
        mock_get_model_types.return_value = ["ml.c5.2xlarge"]
        mock_get_cluster_types.return_value = ["ml.c5.2xlarge"]
        mock_get_region.return_value = "us-west-2"
        mock_get_cluster.return_value = "test-cluster"

        self.endpoint.create(name="test-name", namespace="test-ns")

        mock_create_api.assert_called_once_with(
            name="test-name",
            kind=JUMPSTART_MODEL_KIND,
            namespace="test-ns",
            spec=unittest.mock.ANY,
        )
        self.assertEqual(self.endpoint.metadata.name, "test-name")

    @patch("sagemaker.hyperpod.hyperpod_manager.HyperPodManager.get_current_cluster")
    @patch("sagemaker.hyperpod.hyperpod_manager.HyperPodManager.get_current_region")
    @patch("sagemaker.hyperpod.common.utils.get_cluster_instance_types")
    @patch("sagemaker.hyperpod.common.utils.get_jumpstart_model_instance_types")
    @patch.object(HPJumpStartEndpoint, "call_create_api")
    def test_create_from_dict(
        self,
        mock_create_api,
        mock_get_model_types,
        mock_get_cluster_types,
        mock_get_region,
        mock_get_cluster,
    ):
        mock_get_model_types.return_value = ["ml.c5.2xlarge"]
        mock_get_cluster_types.return_value = ["ml.c5.2xlarge"]
        mock_get_region.return_value = "us-west-2"
        mock_get_cluster.return_value = "test-cluster"

        input_dict = {
            "model": {"modelId": "test-model"},
            "server": {"instance_type": "ml.c5.2xlarge"},
        }

        self.endpoint.create_from_dict(
            input_dict, name="test-name", namespace="test-ns"
        )

        mock_create_api.assert_called_once()

    @patch.object(HPJumpStartEndpoint, "call_get_api")
    def test_refresh(self, mock_get_api):
        self.endpoint.metadata = MagicMock()
        self.endpoint.metadata.name = "test-name"
        self.endpoint.metadata.namespace = "test-ns"
        mock_get_api.return_value = {"status": {"state": "DeploymentComplete"}}

        result = self.endpoint.refresh()

        mock_get_api.assert_called_once_with(
            name="test-name", kind=JUMPSTART_MODEL_KIND, namespace="test-ns"
        )
        self.assertEqual(result, self.endpoint)

    @patch.object(HPJumpStartEndpoint, "get")
    @patch.object(HPJumpStartEndpoint, "call_list_api")
    def test_list(self, mock_list_api, mock_get):
        mock_list_api.return_value = {
            "items": [{"metadata": {"name": "test-endpoint"}}]
        }
        mock_get.return_value = MagicMock()

        result = HPJumpStartEndpoint.list(namespace="test-ns")

        mock_list_api.assert_called_once_with(
            kind=JUMPSTART_MODEL_KIND, namespace="test-ns"
        )
        mock_get.assert_called_once_with("test-endpoint", namespace="test-ns")
        self.assertIsInstance(result, list)

    @patch.object(HPJumpStartEndpoint, "call_get_api")
    def test_get(self, mock_get_api):
        mock_get_api.return_value = {
            "spec": {
                "model": {"modelId": "test-model"},
                "server": {"instance_type": "ml.c5.2xlarge"},
            },
            "status": {"state": "Ready"},
            "metadata": {"name": "test-name", "namespace": "test-ns"},
        }

        result = HPJumpStartEndpoint.get("test-name", namespace="test-ns")

        mock_get_api.assert_called_once_with(
            name="test-name", kind=JUMPSTART_MODEL_KIND, namespace="test-ns"
        )
        self.assertIsInstance(result, HPJumpStartEndpoint)

    @patch.object(HPJumpStartEndpoint, "call_delete_api")
    def test_delete(self, mock_delete_api):
        self.endpoint.metadata = MagicMock()
        self.endpoint.metadata.name = "test-name"
        self.endpoint.metadata.namespace = "test-ns"

        self.endpoint.delete()

        mock_delete_api.assert_called_once_with(
            name="test-name", kind=JUMPSTART_MODEL_KIND, namespace="test-ns"
        )

    @patch("sagemaker_core.main.resources.Endpoint.get")
    def test_invoke(self, mock_endpoint_get):
        self.endpoint.sageMakerEndpoint = MagicMock()
        self.endpoint.sageMakerEndpoint.name = "test-endpoint"
        mock_endpoint = MagicMock()
        mock_endpoint.invoke.return_value = "response"
        mock_endpoint_get.return_value = mock_endpoint

        result = self.endpoint.invoke({"input": "test"})

        mock_endpoint_get.assert_called_once()
        mock_endpoint.invoke.assert_called_once_with(
            body={"input": "test"}, content_type="application/json"
        )
        self.assertEqual(result, "response")

    @patch("sagemaker.hyperpod.hyperpod_manager.HyperPodManager.get_current_cluster")
    @patch("sagemaker.hyperpod.hyperpod_manager.HyperPodManager.get_current_region")
    @patch("sagemaker.hyperpod.common.utils.get_cluster_instance_types")
    @patch("sagemaker.hyperpod.common.utils.get_jumpstart_model_instance_types")
    def test_validate_instance_type_success(
        self,
        mock_get_model_types,
        mock_get_cluster_types,
        mock_get_region,
        mock_get_cluster,
    ):
        mock_get_model_types.return_value = ["ml.c5.2xlarge", "ml.m5.large"]
        mock_get_cluster_types.return_value = ["ml.c5.2xlarge", "ml.m5.large"]
        mock_get_region.return_value = "us-west-2"
        mock_get_cluster.return_value = "test-cluster"

        self.endpoint.validate_instance_type("test-model", "ml.c5.2xlarge")
