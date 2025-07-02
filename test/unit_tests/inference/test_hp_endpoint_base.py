import unittest
from unittest.mock import (
    MagicMock,
    Mock,
    patch,
)
from sagemaker.hyperpod.inference.hp_endpoint_base import HPEndpointBase
from sagemaker.hyperpod.inference.config.constants import (
    INFERENCE_GROUP,
    INFERENCE_API_VERSION,
    KIND_PLURAL_MAP,
)


class TestHPEndpointBase(unittest.TestCase):
    def setUp(self):
        self.mock_hp_endpoint_base = HPEndpointBase()

    @patch("kubernetes.config.load_kube_config")
    def test_validate_connection(
        self,
        mock_load_kube_config: Mock,
    ):
        self.mock_hp_endpoint_base._validate_connection()
        mock_load_kube_config.assert_called_once()

    @patch("kubernetes.client.CustomObjectsApi")
    @patch(
        "sagemaker.hyperpod.inference.hp_endpoint_base.HPEndpointBase._validate_connection"
    )
    def test_call_create_api(
        self,
        mock_validate_connection: Mock,
        mock_custom_objects_api: Mock,
    ):
        mock_validate_connection.return_value = True

        # Create mock spec
        mock_spec = MagicMock()
        mock_spec.model_dump.return_value = {"key": "value"}
        mock_spec.sageMakerEndpoint.name = "test-endpoint"

        # Setup mock API
        mock_create_namespaced_custom_object = Mock()
        mock_custom_objects_api.return_value = Mock(
            create_namespaced_custom_object=mock_create_namespaced_custom_object
        )

        # Test parameters
        name = "test-name"
        kind = "JumpStartModel"
        namespace = "test-namespace"

        # Call the method
        self.mock_hp_endpoint_base.call_create_api(
            name=name, kind=kind, namespace=namespace, spec=mock_spec
        )

        # Verify the call
        mock_create_namespaced_custom_object.assert_called_once_with(
            group=INFERENCE_GROUP,
            version=INFERENCE_API_VERSION,
            namespace=namespace,
            plural=KIND_PLURAL_MAP[kind],
            body={
                "apiVersion": f"{INFERENCE_GROUP}/{INFERENCE_API_VERSION}",
                "kind": kind,
                "metadata": {"name": name, "namespace": namespace},
                "spec": {"key": "value"},
            },
        )

    @patch("kubernetes.client.CustomObjectsApi")
    @patch(
        "sagemaker.hyperpod.inference.hp_endpoint_base.HPEndpointBase._validate_connection"
    )
    def test_call_get_api(
        self,
        mock_validate_connection: Mock,
        mock_custom_objects_api: Mock,
    ):
        mock_validate_connection.return_value = True

        # Setup mock API
        mock_get_namespaced_custom_object = Mock()
        mock_custom_objects_api.return_value = Mock(
            get_namespaced_custom_object=mock_get_namespaced_custom_object
        )

        # Test parameters
        name = "test-name"
        kind = "JumpStartModel"
        namespace = "test-namespace"

        # Call the method
        self.mock_hp_endpoint_base.call_get_api(
            name=name, kind=kind, namespace=namespace
        )

        # Verify the call
        mock_get_namespaced_custom_object.assert_called_once_with(
            group=INFERENCE_GROUP,
            version=INFERENCE_API_VERSION,
            namespace=namespace,
            plural=KIND_PLURAL_MAP[kind],
            name=name,
        )

    @patch("kubernetes.client.CustomObjectsApi")
    @patch(
        "sagemaker.hyperpod.inference.hp_endpoint_base.HPEndpointBase._validate_connection"
    )
    def test_call_delete_api(
        self,
        mock_validate_connection: Mock,
        mock_custom_objects_api: Mock,
    ):
        mock_validate_connection.return_value = True

        # Setup mock API
        mock_delete_namespaced_custom_object = Mock()
        mock_custom_objects_api.return_value = Mock(
            delete_namespaced_custom_object=mock_delete_namespaced_custom_object
        )

        # Test parameters
        name = "test-name"
        kind = "JumpStartModel"
        namespace = "test-namespace"

        # Call the method
        self.mock_hp_endpoint_base.call_delete_api(
            name=name, kind=kind, namespace=namespace
        )

        # Verify the call
        mock_delete_namespaced_custom_object.assert_called_once_with(
            group=INFERENCE_GROUP,
            version=INFERENCE_API_VERSION,
            namespace=namespace,
            plural=KIND_PLURAL_MAP[kind],
            name=name,
        )

    @patch("kubernetes.client.CustomObjectsApi")
    @patch(
        "sagemaker.hyperpod.inference.hp_endpoint_base.HPEndpointBase._validate_connection"
    )
    def test_call_list_api(
        self,
        mock_validate_connection: Mock,
        mock_custom_objects_api: Mock,
    ):
        mock_validate_connection.return_value = True

        # Setup mock API
        mock_list_namespaced_custom_object = Mock()
        mock_custom_objects_api.return_value = Mock(
            list_namespaced_custom_object=mock_list_namespaced_custom_object
        )

        # Test parameters
        kind = "JumpStartModel"
        namespace = "test-namespace"

        # Call the method
        self.mock_hp_endpoint_base.call_list_api(kind=kind, namespace=namespace)

        # Verify the call
        mock_list_namespaced_custom_object.assert_called_once_with(
            group=INFERENCE_GROUP,
            version=INFERENCE_API_VERSION,
            namespace=namespace,
            plural=KIND_PLURAL_MAP[kind],
        )

    def test_invoke_endpoint_not_initialized(self):
        # Test invoke when endpoint is not initialized
        with self.assertRaises(Exception) as context:
            self.mock_hp_endpoint_base.invoke({"input": "test"})

        self.assertTrue("Endpoint not initialized" in str(context.exception))

    def test_invoke_success(self):
        # Setup mock endpoint
        mock_endpoint = MagicMock()
        mock_endpoint.invoke = MagicMock()
        self.mock_hp_endpoint_base._endpoint = mock_endpoint

        # Test parameters
        body = {"input": "test data"}
        content_type = "application/json"

        # Call the method
        self.mock_hp_endpoint_base.invoke(body, content_type=content_type)

        # Verify the call
        mock_endpoint.invoke.assert_called_once_with(body, content_type=content_type)

    @patch("sagemaker.hyperpod.inference.hp_endpoint_base.get_current_region")
    def test_get_endpoint_with_endpoint_get(self, mock_get_current_region):
        # Setup mocks
        mock_get_current_region.return_value = "us-west-2"

        # Mock the Endpoint.get static method
        with patch("sagemaker_core.main.resources.Endpoint.get") as mock_endpoint_get:
            mock_endpoint_instance = MagicMock()
            mock_endpoint_get.return_value = mock_endpoint_instance

            # Call the method
            result = HPEndpointBase.get("test-endpoint")

            # Verify the call
            mock_endpoint_get.assert_called_once()
            self.assertEqual(result, mock_endpoint_instance)
