import unittest
from unittest.mock import patch, MagicMock
import pytest
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.config.jumpstart_model_endpoint_config import (
    JumpStartModelSpec,
    Model,
    Server,
    SageMakerEndpoint,
)
from sagemaker.hyperpod.inference.config.constants import *


class TestHPJumpStartEndpoint(unittest.TestCase):
    def setUp(self):
        self.endpoint = HPJumpStartEndpoint()

    # Tests for _validate_inputs
    def test_validate_inputs_valid_parameters(self):
        # Should not raise any exceptions
        self.endpoint._validate_inputs(
            model_id="model-123", instance_type="ml.g4dn.xlarge"
        )

    def test_validate_inputs_none_parameters(self):
        with pytest.raises(
            ValueError, match="Must provide both model_id and instance_type."
        ):
            self.endpoint._validate_inputs(
                model_id=None, instance_type="ml.g4dn.xlarge"
            )

        with pytest.raises(
            ValueError, match="Must provide both model_id and instance_type."
        ):
            self.endpoint._validate_inputs(model_id="model-123", instance_type=None)

        with pytest.raises(
            ValueError, match="Must provide both model_id and instance_type."
        ):
            self.endpoint._validate_inputs(model_id=None, instance_type=None)

    def test_validate_inputs_invalid_types(self):
        with pytest.raises(
            TypeError, match="model_id must be of type str, got <class 'int'>"
        ):
            self.endpoint._validate_inputs(model_id=123, instance_type="ml.g4dn.xlarge")

        with pytest.raises(
            TypeError, match="instance_type must be of type str, got <class 'int'>"
        ):
            self.endpoint._validate_inputs(model_id="model-123", instance_type=456)

    @patch("sagemaker.hyperpod.inference.hp_jumpstart_endpoint.datetime")
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

    @patch.object(HPJumpStartEndpoint, "_validate_inputs")
    @patch.object(HPJumpStartEndpoint, "_get_default_endpoint_name")
    @patch.object(HPJumpStartEndpoint, "call_create_api")
    def test_create(
        self, mock_call_create_api, mock_get_default_endpoint_name, mock_validate_inputs
    ):
        # Setup mocks
        mock_get_default_endpoint_name.return_value = "test-model-230101-120000-123456"

        # Call the method
        with patch(
            "sagemaker.hyperpod.inference.hp_jumpstart_endpoint.JumpStartModelSpec"
        ) as mock_spec_class:
            with patch(
                "sagemaker.hyperpod.inference.hp_jumpstart_endpoint.Model"
            ) as mock_model_class:
                with patch(
                    "sagemaker.hyperpod.inference.hp_jumpstart_endpoint.Server"
                ) as mock_server_class:
                    with patch(
                        "sagemaker.hyperpod.inference.hp_jumpstart_endpoint.SageMakerEndpoint"
                    ) as mock_endpoint_class:
                        # Setup mock objects
                        mock_model = MagicMock()
                        mock_server = MagicMock()
                        mock_sagemaker_endpoint = MagicMock()
                        mock_spec = MagicMock()

                        mock_model_class.return_value = mock_model
                        mock_server_class.return_value = mock_server
                        mock_endpoint_class.return_value = mock_sagemaker_endpoint
                        mock_spec_class.return_value = mock_spec

                        mock_spec.model.modelId = "test-model"

                        # Call the method
                        self.endpoint.create(
                            namespace="test-namespace",
                            model_id="test-model",
                            instance_type="ml.g4dn.xlarge",
                        )

                        # Verify method calls
                        mock_validate_inputs.assert_called_once_with(
                            "test-model", "ml.g4dn.xlarge"
                        )
                        mock_get_default_endpoint_name.assert_called_once_with(
                            "test-model"
                        )

                        # Verify object creation
                        mock_model_class.assert_called_once_with(model_id="test-model")
                        mock_server_class.assert_called_once_with(
                            instance_type="ml.g4dn.xlarge"
                        )
                        mock_endpoint_class.assert_called_once_with(
                            name="test-model-230101-120000-123456"
                        )

                        # Verify API call
                        mock_call_create_api.assert_called_once_with(
                            name="test-model",
                            kind=JUMPSTART_MODEL_KIND,
                            namespace="test-namespace",
                            spec=mock_spec,
                        )

    @patch.object(HPJumpStartEndpoint, "call_create_api")
    def test_create_from_spec(self, mock_call_create_api):
        # Create a mock spec with proper structure
        mock_spec = MagicMock()
        mock_model = MagicMock()
        mock_model.modelId = "test-model-id"
        mock_spec.model = mock_model

        # Call the method
        self.endpoint.create_from_spec(spec=mock_spec, namespace="test-namespace")

        # Verify call_create_api was called with correct parameters
        mock_call_create_api.assert_called_once_with(
            name="test-model-id",
            kind=JUMPSTART_MODEL_KIND,
            namespace="test-namespace",
            spec=mock_spec,
        )

    @patch.object(HPJumpStartEndpoint, "call_create_api")
    def test_create_from_dict(self, mock_call_create_api):
        # Setup test data
        input_dict = {
            "model": {"model_id": "test-model"},
            "server": {"instance_type": "ml.g4dn.xlarge"},
            "sage_maker_endpoint": {"name": "test-endpoint"},
        }

        # Setup mock for JumpStartModelSpec
        with patch(
            "sagemaker.hyperpod.inference.hp_jumpstart_endpoint.JumpStartModelSpec"
        ) as mock_spec_class:
            mock_spec = MagicMock()
            mock_spec_class.model_validate.return_value = mock_spec

            # Call the method
            self.endpoint.create_from_dict(input=input_dict, namespace="test-namespace")

            # Verify JumpStartModelSpec.model_validate was called with correct parameters
            mock_spec_class.model_validate.assert_called_once_with(
                input_dict, by_name=True
            )

            # Verify call_create_api was called with correct parameters
            mock_call_create_api.assert_called_once_with(
                namespace="test-namespace", spec=mock_spec
            )

    @patch.object(HPJumpStartEndpoint, "call_list_api")
    def test_list_endpoints(self, mock_call_list_api):
        # Setup mock response
        mock_response = {
            "items": [
                {
                    "metadata": {
                        "name": "endpoint-1",
                        "creationTimestamp": "2023-01-01T12:00:00Z",
                    }
                },
                {
                    "metadata": {
                        "name": "endpoint-2",
                        "creationTimestamp": "2023-01-02T12:00:00Z",
                    }
                },
            ]
        }
        mock_call_list_api.return_value = mock_response

        # Call the method with print capture
        with patch(
            "sagemaker.hyperpod.inference.hp_jumpstart_endpoint.tabulate"
        ) as mock_tabulate:
            self.endpoint.list_endpoints(namespace="test-namespace")

            # Verify call_list_api was called with correct parameters
            mock_call_list_api.assert_called_once_with(
                kind=JUMPSTART_MODEL_KIND, namespace="test-namespace"
            )

            # Verify tabulate was called with correct data
            expected_data = [
                ("endpoint-1", "2023-01-01T12:00:00Z"),
                ("endpoint-2", "2023-01-02T12:00:00Z"),
            ]
            mock_tabulate.assert_called_once_with(
                expected_data, headers=["METADATA NAME", "CREATE TIME"]
            )

    @patch.object(HPJumpStartEndpoint, "call_get_api")
    def test_describe_endpoint(self, mock_call_get_api):
        # Setup mock response
        mock_response = {
            "metadata": {"name": "endpoint-1", "managedFields": {"field1": "value1"}}
        }
        mock_call_get_api.return_value = mock_response

        # Call the method with print capture
        with patch(
            "sagemaker.hyperpod.inference.hp_jumpstart_endpoint.yaml.dump"
        ) as mock_yaml_dump:
            self.endpoint.describe_endpoint(
                name="test-endpoint", namespace="test-namespace"
            )

            # Verify call_get_api was called with correct parameters
            mock_call_get_api.assert_called_once_with(
                name="test-endpoint",
                kind=JUMPSTART_MODEL_KIND,
                namespace="test-namespace",
            )

            # Verify managedFields was removed and yaml.dump was called
            expected_response = {"metadata": {"name": "endpoint-1"}}
            mock_yaml_dump.assert_called_once_with(expected_response)

    @patch.object(HPJumpStartEndpoint, "call_delete_api")
    def test_delete_endpoint(self, mock_call_delete_api):
        # Call the method
        self.endpoint.delete_endpoint(name="test-endpoint", namespace="test-namespace")

        # Verify call_delete_api was called with correct parameters
        mock_call_delete_api.assert_called_once_with(
            name="test-endpoint", kind=JUMPSTART_MODEL_KIND, namespace="test-namespace"
        )
