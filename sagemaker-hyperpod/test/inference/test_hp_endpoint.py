import unittest
from unittest.mock import patch, MagicMock
import pytest
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint
from sagemaker.hyperpod.inference.config.model_endpoint_config import (
    InferenceEndpointConfigSpec,
)
from sagemaker.hyperpod.inference.config.constants import *


class TestHPEndpoint(unittest.TestCase):
    def setUp(self):
        self.endpoint = HPEndpoint()

    def test_validate_inputs_valid_parameters_s3(self):
        # Test with valid S3 parameters
        self.endpoint._validate_inputs(
            model_name="test-model",
            instance_type="ml.g4dn.xlarge",
            image="test-image:latest",
            container_port=8080,
            model_source_type="s3",
            bucket_name="test-bucket",
            bucket_region="us-west-2",
            fsx_dns_name=None,
            fsx_file_system_id=None,
            fsx_mount_name=None,
        )
        # No exception should be raised

    def test_validate_inputs_valid_parameters_fsx(self):
        self.endpoint._validate_inputs(
            model_name="test-model",
            instance_type="ml.g4dn.xlarge",
            image="test-image:latest",
            container_port=8080,
            model_source_type="fsx",
            bucket_name=None,
            bucket_region=None,
            fsx_dns_name="test-dns",
            fsx_file_system_id="fs-12345",
            fsx_mount_name="test-mount",
        )
        # No exception should be raised

    def test_validate_inputs_missing_required_params(self):
        # Test with missing required parameters
        with pytest.raises(
            ValueError,
            match="When spec is None, model_name, instance_type, image, container_port, and model_source_type must be provided",
        ):
            self.endpoint._validate_inputs(
                model_name=None,
                instance_type="ml.g4dn.xlarge",
                image="test-image:latest",
                container_port=8080,
                model_source_type="s3",
                bucket_name="test-bucket",
                bucket_region="us-west-2",
                fsx_dns_name=None,
                fsx_file_system_id=None,
                fsx_mount_name=None,
            )

    def test_validate_inputs_invalid_model_source_type(self):
        # Test with invalid model_source_type
        with pytest.raises(
            TypeError, match="model_source_type must be either 'fsx' or 's3'"
        ):
            self.endpoint._validate_inputs(
                model_name="test-model",
                instance_type="ml.g4dn.xlarge",
                image="test-image:latest",
                container_port=8080,
                model_source_type="invalid",
                bucket_name="test-bucket",
                bucket_region="us-west-2",
                fsx_dns_name=None,
                fsx_file_system_id=None,
                fsx_mount_name=None,
            )

    def test_validate_inputs_missing_s3_params(self):
        # Test with missing S3 parameters
        with pytest.raises(
            ValueError,
            match="When model_source_type is 's3', bucket_name and bucket_region must be provided",
        ):
            self.endpoint._validate_inputs(
                model_name="test-model",
                instance_type="ml.g4dn.xlarge",
                image="test-image:latest",
                container_port=8080,
                model_source_type="s3",
                bucket_name=None,
                bucket_region="us-west-2",
                fsx_dns_name=None,
                fsx_file_system_id=None,
                fsx_mount_name=None,
            )

    def test_validate_inputs_missing_fsx_params(self):
        # Test with missing FSx parameters
        with pytest.raises(
            ValueError,
            match="When model_source_type is 'fsx', fsx_file_system_id must be provided",
        ):
            self.endpoint._validate_inputs(
                model_name="test-model",
                instance_type="ml.g4dn.xlarge",
                image="test-image:latest",
                container_port=8080,
                model_source_type="fsx",
                bucket_name=None,
                bucket_region=None,
                fsx_dns_name="test-dns",
                fsx_file_system_id=None,
                fsx_mount_name="test-mount",
            )

    @patch("sagemaker.hyperpod.inference.hp_endpoint.datetime")
    def test_get_default_endpoint_name(self, mock_datetime):
        # Setup mock datetime
        mock_now = mock_datetime.now.return_value
        mock_now.strftime.return_value = "230101-120000-123456"

        # Test the method
        result = self.endpoint._get_default_endpoint_name("test-model")

        # Verify results
        self.assertEqual(result, "test-model-230101-120000-123456")
        mock_datetime.now.assert_called_once()
        mock_now.strftime.assert_called_once_with("%y%m%d-%H%M%S-%f")

    # Tests for create method
    @patch.object(HPEndpoint, "_validate_inputs")
    @patch.object(HPEndpoint, "_get_default_endpoint_name")
    @patch.object(HPEndpoint, "call_create_api")
    def test_create_with_s3(
        self, mock_call_create_api, mock_get_default_endpoint_name, mock_validate_inputs
    ):
        mock_get_default_endpoint_name.return_value = "test-model-230101-120000-123456"

        # Call the method with S3 storage
        with patch(
            "sagemaker.hyperpod.inference.hp_endpoint.InferenceEndpointConfigSpec"
        ) as mock_spec_class:
            with patch(
                "sagemaker.hyperpod.inference.hp_endpoint.ModelSourceConfig"
            ) as mock_model_source_config:
                with patch(
                    "sagemaker.hyperpod.inference.hp_endpoint.S3Storage"
                ) as mock_s3_storage:
                    mock_spec = MagicMock()
                    mock_spec.modelName = "test-model"
                    mock_spec_class.return_value = mock_spec

                    self.endpoint.create(
                        namespace="test-namespace",
                        model_name="test-model",
                        instance_type="ml.g4dn.xlarge",
                        image="test-image:latest",
                        container_port=8080,
                        model_source_type="s3",
                        bucket_name="test-bucket",
                        bucket_region="us-west-2",
                    )

                    # Verify _validate_inputs was called with correct parameters
                    mock_validate_inputs.assert_called_once()

                    # Verify _get_default_endpoint_name was called with correct parameters
                    mock_get_default_endpoint_name.assert_called_once_with("test-model")

                    # Verify S3Storage was created with correct parameters
                    mock_s3_storage.assert_called_once_with(
                        bucket_name="test-bucket", region="us-west-2"
                    )

                    # Verify call_create_api was called with correct parameters
                    mock_call_create_api.assert_called_once_with(
                        name="test-model",
                        kind=INFERENCE_ENDPOINT_CONFIG_KIND,
                        namespace="test-namespace",
                        spec=mock_spec,
                    )

    @patch.object(HPEndpoint, "_validate_inputs")
    @patch.object(HPEndpoint, "_get_default_endpoint_name")
    @patch.object(HPEndpoint, "call_create_api")
    def test_create_with_fsx(
        self, mock_call_create_api, mock_get_default_endpoint_name, mock_validate_inputs
    ):
        # Setup mocks
        mock_get_default_endpoint_name.return_value = "test-model-230101-120000-123456"

        # Call the method with FSx storage
        with patch(
            "sagemaker.hyperpod.inference.hp_endpoint.InferenceEndpointConfigSpec"
        ) as mock_spec_class:
            with patch(
                "sagemaker.hyperpod.inference.hp_endpoint.ModelSourceConfig"
            ) as mock_model_source_config:
                with patch(
                    "sagemaker.hyperpod.inference.hp_endpoint.FsxStorage"
                ) as mock_fsx_storage:
                    mock_spec = MagicMock()
                    mock_spec.modelName = "test-model"
                    mock_spec_class.return_value = mock_spec

                    self.endpoint.create(
                        namespace="test-namespace",
                        model_name="test-model",
                        instance_type="ml.g4dn.xlarge",
                        image="test-image:latest",
                        container_port=8080,
                        model_source_type="fsx",
                        fsx_dns_name="test-dns",
                        fsx_file_system_id="fs-12345",
                        fsx_mount_name="test-mount",
                    )

                    # Verify FsxStorage was created with correct parameters
                    mock_fsx_storage.assert_called_once_with(
                        fsx_dns_name="test-dns",
                        file_system_id="fs-12345",
                        mount_name="test-mount",
                    )

    @patch.object(HPEndpoint, "call_create_api")
    def test_create_from_spec(self, mock_call_create_api):
        mock_spec = MagicMock(spec=InferenceEndpointConfigSpec)
        self.endpoint.create_from_spec(spec=mock_spec, namespace="test-namespace")

        mock_call_create_api.assert_called_once_with(
            namespace="test-namespace", spec=mock_spec
        )

    @patch.object(HPEndpoint, "call_create_api")
    def test_create_from_dict(self, mock_call_create_api):
        # Setup test data
        input_dict = {
            "endpoint_name": "test-endpoint",
            "instance_type": "ml.g4dn.xlarge",
            "model_name": "test-model",
            "image": "test-image:latest",
            "container_port": 8080,
            "model_source_config": {
                "model_source_type": "s3",
                "s3_storage": {"bucket_name": "test-bucket", "region": "us-west-2"},
            },
        }

        with patch(
            "sagemaker.hyperpod.inference.hp_endpoint.InferenceEndpointConfigSpec"
        ) as mock_spec_class:
            mock_spec = MagicMock()
            mock_spec_class.model_validate.return_value = mock_spec

            # Call the method
            self.endpoint.create_from_dict(input=input_dict, namespace="test-namespace")

            # Verify InferenceEndpointConfigSpec.model_validate was called with correct parameters
            mock_spec_class.model_validate.assert_called_once_with(
                input_dict, by_name=True
            )

            # Verify call_create_api was called with correct parameters
            mock_call_create_api.assert_called_once_with(
                namespace="test-namespace", spec=mock_spec
            )

    @patch.object(HPEndpoint, "call_list_api")
    def test_list_endpoints(self, mock_call_list_api):
        mock_response = {"items": [{"metadata": {"name": "endpoint-1"}}]}
        mock_call_list_api.return_value = mock_response

        # Call the method
        result = self.endpoint.list_endpoints(namespace="test-namespace")

        # Verify call_list_api was called with correct parameters
        mock_call_list_api.assert_called_once_with(
            kind=INFERENCE_ENDPOINT_CONFIG_KIND, namespace="test-namespace"
        )

        # Verify result
        self.assertEqual(result, mock_response)

    @patch.object(HPEndpoint, "call_get_api")
    def test_describe_endpoint(self, mock_call_get_api):
        mock_response = {"metadata": {"name": "endpoint-1"}}
        mock_call_get_api.return_value = mock_response

        result = self.endpoint.describe_endpoint(
            name="endpoint-1", namespace="test-namespace"
        )

        # Verify call_get_api was called with correct parameters
        mock_call_get_api.assert_called_once_with(
            name="endpoint-1",
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace="test-namespace",
        )

        # Verify result
        self.assertEqual(result, mock_response)

    @patch.object(HPEndpoint, "call_delete_api")
    def test_delete_endpoint(self, mock_call_delete_api):
        # Setup mock response
        mock_response = {"status": "success"}
        mock_call_delete_api.return_value = mock_response

        # Call the method
        result = self.endpoint.delete_endpoint(
            name="endpoint-1", namespace="test-namespace"
        )

        # Verify call_delete_api was called with correct parameters
        mock_call_delete_api.assert_called_once_with(
            name="endpoint-1",
            kind=INFERENCE_ENDPOINT_CONFIG_KIND,
            namespace="test-namespace",
        )

        # Verify result
        self.assertEqual(result, mock_response)
