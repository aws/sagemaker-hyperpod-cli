import unittest
from unittest.mock import MagicMock, patch
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.config.constants import *
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import (
    Model,
    Server,
    SageMakerEndpoint,
    TlsConfig,
    Validations,
)
from sagemaker.hyperpod.common.config import Metadata


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

    @patch.object(HPJumpStartEndpoint, "validate_instance_type")
    @patch.object(HPJumpStartEndpoint, "call_create_api")
    @patch(
        "sagemaker.hyperpod.inference.hp_jumpstart_endpoint.get_default_namespace",
        return_value="default",
    )
    def test_create(
        self, mock_get_namespace, mock_create_api, mock_validate_instance_type
    ):

        self.endpoint.create()

        mock_create_api.assert_called_once_with(
            metadata=unittest.mock.ANY,
            kind=JUMPSTART_MODEL_KIND,
            spec=unittest.mock.ANY,
            debug=False,
        )
        self.assertEqual(self.endpoint.metadata.name, "bert-testing-jumpstart-7-2-2")

    @patch.object(HPJumpStartEndpoint, "validate_instance_type")
    @patch.object(HPJumpStartEndpoint, "call_create_api")
    def test_create_with_metadata(self, mock_create_api, mock_validate_instance_type):
        """Test create_from_dict uses metadata name and namespace when endpoint name not provided"""

        # Create endpoint without sageMakerEndpoint name to force using metadata
        endpoint_without_name = HPJumpStartEndpoint(
            model=Model(model_id="test-model"),
            server=Server(instance_type="ml.c5.2xlarge"),
            tls_config=TlsConfig(tls_certificate_output_s3_uri="s3://test-bucket"),
            metadata=Metadata(name="metadata-test-name", namespace="metadata-test-ns"),
        )

        endpoint_without_name.create()

        # Verify it uses metadata name and namespace
        mock_create_api.assert_called_once()
        call_args = mock_create_api.call_args[1]
        assert call_args['metadata'].name == 'metadata-test-name'
        assert call_args['metadata'].namespace == 'metadata-test-ns'


    @patch.object(HPJumpStartEndpoint, "validate_instance_type")
    @patch.object(HPJumpStartEndpoint, "call_create_api")
    @patch(
        "sagemaker.hyperpod.inference.hp_jumpstart_endpoint.get_default_namespace",
        return_value="default",
    )
    def test_create_from_dict(
        self, mock_get_namespace, mock_create_api, mock_validate_instance_type
    ):

        input_dict = self.endpoint.model_dump(exclude_none=True)

        self.endpoint.create_from_dict(input_dict)

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

    @patch("sagemaker.hyperpod.common.utils.get_cluster_context")
    @patch("sagemaker_core.main.resources.Endpoint.get")
    def test_invoke(self, mock_endpoint_get, mock_get_cluster_context):
        mock_get_cluster_context.return_value = "test-cluster-arn"

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

    @patch.object(HPJumpStartEndpoint, "call_list_api")
    @patch("kubernetes.client.CoreV1Api")
    @patch.object(HPJumpStartEndpoint, "verify_kube_config")
    def test_list_pods(self, mock_verify_config, mock_core_api, mock_list_api):
        mock_pod1 = MagicMock()
        mock_pod1.metadata.name = "js-endpoint-pod1"
        mock_pod1.metadata.labels = {"app": "js-endpoint"}
        mock_pod2 = MagicMock()
        mock_pod2.metadata.name = "js-endpoint-pod2"
        mock_pod2.metadata.labels = {"app": "js-endpoint"}
        mock_pod3 = MagicMock()
        mock_pod3.metadata.name = "not-js-endpoint-pod"
        mock_pod3.metadata.labels = {"app": "not-js-endpoint"}
        mock_core_api.return_value.list_namespaced_pod.return_value.items = [
            mock_pod1,
            mock_pod2,
            mock_pod3,
        ]

        mock_list_api.return_value = {"items": [{"metadata": {"name": "js-endpoint"}}]}

        result = self.endpoint.list_pods(namespace="test-ns")

        self.assertEqual(result, ["js-endpoint-pod1", "js-endpoint-pod2"])
        mock_core_api.return_value.list_namespaced_pod.assert_called_once_with(
            namespace="test-ns"
        )

    @patch("kubernetes.client.CoreV1Api")
    @patch.object(HPJumpStartEndpoint, "verify_kube_config")
    def test_list_pods_with_endpoint_name(self, mock_verify_config, mock_core_api):
        mock_pod1 = MagicMock()
        mock_pod1.metadata.name = "js-endpoint1-pod1"
        mock_pod1.metadata.labels = {"app": "js-endpoint1"}
        mock_pod2 = MagicMock()
        mock_pod2.metadata.name = "js-endpoint1-pod2"
        mock_pod2.metadata.labels = {"app": "js-endpoint1"}
        mock_pod3 = MagicMock()
        mock_pod3.metadata.name = "js-endpoint2-pod"
        mock_pod3.metadata.labels = {"app": "js-endpoint2"}
        mock_core_api.return_value.list_namespaced_pod.return_value.items = [
            mock_pod1,
            mock_pod2,
            mock_pod3,
        ]

        result = self.endpoint.list_pods(
            namespace="test-ns", endpoint_name="js-endpoint1"
        )

        self.assertEqual(result, ["js-endpoint1-pod1", "js-endpoint1-pod2"])
        mock_core_api.return_value.list_namespaced_pod.assert_called_once_with(
            namespace="test-ns"
        )

    def test_validate_mig_profile_valid(self):
        """Test validate_mig_profile with valid instance type and MIG profile"""
        # Test with valid combinations
        self.endpoint.validate_mig_profile("mig-1g.5gb", "ml.p4d.24xlarge")
        self.endpoint.validate_mig_profile("mig-7g.40gb", "ml.p4d.24xlarge")
        self.endpoint.validate_mig_profile("mig-1g.10gb", "ml.p4de.24xlarge")
        self.endpoint.validate_mig_profile("mig-7g.80gb", "ml.p5.48xlarge")

    def test_validate_mig_profile_invalid_instance_type(self):
        """Test validate_mig_profile with unsupported instance type"""
        with self.assertRaises(ValueError) as context:
            self.endpoint.validate_mig_profile("1g.5gb", "ml.c5.2xlarge")

        self.assertIn(
            "Instance type 'ml.c5.2xlarge' does not support MIG profiles",
            str(context.exception),
        )
        self.assertIn("Supported instance types:", str(context.exception))

    def test_validate_mig_profile_invalid_mig_profile(self):
        """Test validate_mig_profile with unsupported MIG profile for valid instance type"""
        with self.assertRaises(ValueError) as context:
            self.endpoint.validate_mig_profile("invalid.profile", "ml.p4d.24xlarge")

        self.assertIn(
            "MIG profile 'invalid.profile' is not supported for instance type 'ml.p4d.24xlarge'",
            str(context.exception),
        )
        self.assertIn(
            "Supported MIG profiles for ml.p4d.24xlarge:", str(context.exception)
        )

    def test_validate_mig_profile_wrong_profile_for_instance(self):
        """Test validate_mig_profile with MIG profile that exists but not for the specific instance type"""
        # 7g.80gb is valid for p4de but not p4d
        with self.assertRaises(ValueError) as context:
            self.endpoint.validate_mig_profile("7g.80gb", "ml.p4d.24xlarge")

        self.assertIn(
            "MIG profile '7g.80gb' is not supported for instance type 'ml.p4d.24xlarge'",
            str(context.exception),
        )

    @patch.object(HPJumpStartEndpoint, "validate_mig_profile")
    @patch.object(HPJumpStartEndpoint, "call_create_api")
    @patch(
        "sagemaker.hyperpod.inference.hp_jumpstart_endpoint.get_default_namespace",
        return_value="default",
    )
    def test_create_with_accelerator_partition_validation(
        self, mock_get_namespace, mock_create_api, mock_validate_mig
    ):
        """Test create method uses MIG validation when accelerator_partition_validation is True"""
        # Create endpoint with accelerator partition validation enabled
        model = Model(model_id="test-model")
        validations = Validations(
            accelerator_partition_validation=True,
        )
        server = Server(
            instance_type="ml.p4d.24xlarge",
            validations=validations,
            accelerator_partition_type="1g.5gb",
        )
        endpoint = HPJumpStartEndpoint(
            model=model,
            server=server,
            sage_maker_endpoint=SageMakerEndpoint(name="test-endpoint"),
            tls_config=TlsConfig(tls_certificate_output_s3_uri="s3://test-bucket"),
        )

        endpoint.create()

        # Should call validate_mig_profile instead of validate_instance_type
        mock_validate_mig.assert_called_once_with("1g.5gb", "ml.p4d.24xlarge")
        mock_create_api.assert_called_once()

    @patch.object(HPJumpStartEndpoint, "validate_instance_type")
    @patch.object(HPJumpStartEndpoint, "call_create_api")
    @patch(
        "sagemaker.hyperpod.inference.hp_jumpstart_endpoint.get_default_namespace",
        return_value="default",
    )
    def test_create_without_accelerator_partition_validation(
        self, mock_get_namespace, mock_create_api, mock_validate_instance
    ):
        """Test create method uses instance type validation when accelerator_partition_validation is False/None"""
        # Create endpoint without accelerator partition validation (default behavior)
        model = Model(model_id="test-model")
        server = Server(instance_type="ml.c5.2xlarge")
        endpoint = HPJumpStartEndpoint(
            model=model,
            server=server,
            sage_maker_endpoint=SageMakerEndpoint(name="test-endpoint"),
            tls_config=TlsConfig(tls_certificate_output_s3_uri="s3://test-bucket"),
        )

        endpoint.create()

        # Should call validate_instance_type instead of validate_mig_profile
        mock_validate_instance.assert_called_once_with("test-model", "ml.c5.2xlarge")
        mock_create_api.assert_called_once()

    @patch.object(HPJumpStartEndpoint, "validate_mig_profile")
    @patch.object(HPJumpStartEndpoint, "call_create_api")
    @patch(
        "sagemaker.hyperpod.inference.hp_jumpstart_endpoint.get_default_namespace",
        return_value="default",
    )
    def test_create_from_dict_with_accelerator_partition_validation(
        self, mock_get_namespace, mock_create_api, mock_validate_mig
    ):
        """Test create_from_dict method uses MIG validation when accelerator_partition_validation is True"""
        input_dict = {
            "model": {"modelId": "test-model"},
            "server": {
                "instanceType": "ml.p4d.24xlarge",
                "validations": {
                    "acceleratorPartitionValidation": True
                },
                "acceleratorPartitionType": "1g.5gb",
            },
            "sageMakerEndpoint": {"name": "test-endpoint"},
            "tlsConfig": {"tlsCertificateOutputS3Uri": "s3://test-bucket"},
        }

        endpoint = HPJumpStartEndpoint(
            model=Model(model_id="dummy"),
            server=Server(instance_type="dummy"),
            tls_config=TlsConfig(tls_certificate_output_s3_uri="s3://dummy"),
        )
        endpoint.create_from_dict(input_dict)

        # Should call validate_mig_profile instead of validate_instance_type
        mock_validate_mig.assert_called_once_with("1g.5gb", "ml.p4d.24xlarge")
        mock_create_api.assert_called_once()

    @patch.object(HPJumpStartEndpoint, "validate_instance_type")
    @patch.object(HPJumpStartEndpoint, "call_create_api")
    @patch(
        "sagemaker.hyperpod.inference.hp_jumpstart_endpoint.get_default_namespace",
        return_value="default",
    )
    def test_create_from_dict_without_accelerator_partition_validation(
        self, mock_get_namespace, mock_create_api, mock_validate_instance
    ):
        """Test create_from_dict method uses instance type validation when accelerator_partition_validation is False/None"""
        input_dict = {
            "model": {"modelId": "test-model"},
            "server": {"instanceType": "ml.c5.2xlarge"},
            "sageMakerEndpoint": {"name": "test-endpoint"},
            "tlsConfig": {"tlsCertificateOutputS3Uri": "s3://test-bucket"},
        }

        endpoint = HPJumpStartEndpoint(
            model=Model(model_id="dummy"),
            server=Server(instance_type="dummy"),
            tls_config=TlsConfig(tls_certificate_output_s3_uri="s3://dummy"),
        )
        endpoint.create_from_dict(input_dict)

        # Should call validate_instance_type instead of validate_mig_profile
        mock_validate_instance.assert_called_once_with("test-model", "ml.c5.2xlarge")
        mock_create_api.assert_called_once()

    def test_validate_mig_profile_edge_cases(self):
        """Test validate_mig_profile with various edge cases"""
        # Test with different instance types and their specific profiles
        test_cases = [
            ("ml.p4de.24xlarge", "mig-1g.5gb"),
            ("ml.p5.48xlarge", "mig-3g.40gb"),
            ("ml.p5e.48xlarge", "mig-1g.18gb"),
            ("ml.p5en.48xlarge", "mig-7g.141gb"),
            ("p6-b200.48xlarge", "mig-1g.23gb"),
            ("ml.p6e-gb200.36xlarge", "mig-7g.186gb"),
        ]

        for instance_type, mig_profile in test_cases:
            with self.subTest(instance_type=instance_type, mig_profile=mig_profile):
                # Should not raise any exception
                self.endpoint.validate_mig_profile(mig_profile, instance_type)

    def test_validate_mig_profile_case_sensitivity(self):
        """Test that MIG profile validation is case sensitive"""
        with self.assertRaises(ValueError):
            # Test uppercase - should fail as profiles are lowercase
            self.endpoint.validate_mig_profile("1G.5GB", "ml.p4d.24xlarge")

    @patch.object(HPJumpStartEndpoint, "validate_mig_profile")
    @patch.object(HPJumpStartEndpoint, "validate_instance_type")
    @patch.object(HPJumpStartEndpoint, "call_create_api")
    @patch(
        "sagemaker.hyperpod.inference.hp_jumpstart_endpoint.get_default_namespace",
        return_value="default",
    )
    def test_create_validation_logic_priority(
        self,
        mock_get_namespace,
        mock_create_api,
        mock_validate_instance,
        mock_validate_mig,
    ):
        """Test that accelerator_partition_validation takes priority over regular validation"""
        # Create endpoint with both accelerator partition validation and regular fields
        model = Model(model_id="test-model")
        validations = Validations(
            accelerator_partition_validation=True,
        )
        server = Server(
            instance_type="ml.p4d.24xlarge",
            validations=validations,
            accelerator_partition_type="1g.5gb",
        )
        endpoint = HPJumpStartEndpoint(
            model=model,
            server=server,
            sage_maker_endpoint=SageMakerEndpoint(name="test-endpoint"),
            tls_config=TlsConfig(tls_certificate_output_s3_uri="s3://test-bucket"),
        )

        endpoint.create()

        # Should only call validate_mig_profile, not validate_instance_type
        mock_validate_mig.assert_called_once_with("1g.5gb", "ml.p4d.24xlarge")
        mock_validate_instance.assert_not_called()
        mock_create_api.assert_called_once()

    def test_create_missing_name_and_endpoint_name(self):
        """Test create method raises exception when both metadata name and endpoint name are missing"""
        model = Model(model_id="test-model")
        server = Server(instance_type="ml.c5.2xlarge")
        endpoint = HPJumpStartEndpoint(
            model=model,
            server=server,
            tls_config=TlsConfig(tls_certificate_output_s3_uri="s3://test-bucket"),
            # No sageMakerEndpoint name and no metadata
        )

        with self.assertRaises(Exception) as context:
            endpoint.create()

        self.assertIn(
            "Either metadata name or endpoint name must be provided",
            str(context.exception),
        )

    def test_create_from_dict_missing_name_and_endpoint_name(self):
        """Test create_from_dict method raises exception when both name and endpoint name are missing"""
        input_dict = {
            "model": {"modelId": "test-model"},
            "server": {"instanceType": "ml.c5.2xlarge"},
            "tlsConfig": {"tlsCertificateOutputS3Uri": "s3://test-bucket"},
            # No sageMakerEndpoint name
        }

        endpoint = HPJumpStartEndpoint(
            model=Model(model_id="dummy"),
            server=Server(instance_type="dummy"),
            tls_config=TlsConfig(tls_certificate_output_s3_uri="s3://dummy"),
            # No metadata
        )

        with self.assertRaises(Exception) as context:
            endpoint.create_from_dict(input_dict)

        self.assertIn(
            'Input "name" is required if endpoint name is not provided',
            str(context.exception),
        )