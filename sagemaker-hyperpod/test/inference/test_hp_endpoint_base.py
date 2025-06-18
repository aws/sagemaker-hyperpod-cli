import os
import unittest
from unittest.mock import (
    MagicMock,
    Mock,
    mock_open,
    patch,
)
import yaml
from kubernetes import client
from kubernetes.config import (
    KUBE_CONFIG_DEFAULT_LOCATION,
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
