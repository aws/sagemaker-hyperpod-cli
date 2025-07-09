import unittest
from unittest.mock import MagicMock, patch
from sagemaker.hyperpod.inference.hp_endpoint_base import HPEndpointBase
from sagemaker.hyperpod.inference.config.constants import *


class TestHPEndpointBase(unittest.TestCase):
    def setUp(self):
        self.base = HPEndpointBase()

    @patch("kubernetes.client.CustomObjectsApi")
    @patch(
        "sagemaker.hyperpod.common.utils.validate_cluster_connection", return_value=True
    )
    def test_call_create_api(self, mock_validate_connection, mock_custom_api):
        mock_spec = MagicMock()
        mock_spec.model_dump.return_value = {"test": "data"}

        self.base.call_create_api("test-name", "JumpStartModel", "test-ns", mock_spec)

        mock_custom_api.return_value.create_namespaced_custom_object.assert_called_once()

    @patch("kubernetes.client.CustomObjectsApi")
    @patch(
        "sagemaker.hyperpod.common.utils.validate_cluster_connection", return_value=True
    )
    def test_call_list_api(self, mock_validate_connection, mock_custom_api):
        mock_custom_api.return_value.list_namespaced_custom_object.return_value = {
            "items": []
        }

        result = self.base.call_list_api("JumpStartModel", "test-ns")

        mock_custom_api.return_value.list_namespaced_custom_object.assert_called_once()
        self.assertEqual(result, {"items": []})

    @patch("kubernetes.client.CustomObjectsApi")
    @patch(
        "sagemaker.hyperpod.common.utils.validate_cluster_connection", return_value=True
    )
    def test_call_get_api(self, mock_validate_connection, mock_custom_api):
        mock_custom_api.return_value.get_namespaced_custom_object.return_value = {
            "name": "test"
        }

        result = self.base.call_get_api("test-name", "JumpStartModel", "test-ns")

        mock_custom_api.return_value.get_namespaced_custom_object.assert_called_once()
        self.assertEqual(result, {"name": "test"})

    @patch("kubernetes.client.CustomObjectsApi")
    @patch(
        "sagemaker.hyperpod.common.utils.validate_cluster_connection", return_value=True
    )
    def test_call_delete_api(self, mock_validate_connection, mock_custom_api):
        self.base.call_delete_api("test-name", "JumpStartModel", "test-ns")

        mock_custom_api.return_value.delete_namespaced_custom_object.assert_called_once()

    @patch("kubernetes.client.CoreV1Api")
    @patch(
        "sagemaker.hyperpod.common.utils.validate_cluster_connection", return_value=True
    )
    def test_get_operator_logs(self, mock_validate_connection, mock_core_api):
        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod"
        mock_core_api.return_value.list_namespaced_pod.return_value.items = [mock_pod]
        mock_core_api.return_value.read_namespaced_pod_log.return_value = "test logs"

        result = self.base.get_operator_logs(2)

        self.assertEqual(result, "test logs")
        mock_core_api.return_value.read_namespaced_pod_log.assert_called_once_with(
            name="test-pod",
            namespace=OPERATOR_NAMESPACE,
            timestamps=True,
            since_seconds=7200,
        )

    @patch("kubernetes.client.CoreV1Api")
    @patch(
        "sagemaker.hyperpod.common.utils.validate_cluster_connection", return_value=True
    )
    def test_get_logs(self, mock_validate_connection, mock_core_api):
        mock_container = MagicMock()
        mock_container.name = "test-container"
        mock_pod = MagicMock()
        mock_pod.spec.containers = [mock_container]
        mock_core_api.return_value.read_namespaced_pod.return_value = mock_pod
        mock_core_api.return_value.read_namespaced_pod_log.return_value = "pod logs"

        result = self.base.get_logs("test-pod", namespace="test-ns")

        self.assertEqual(result, "pod logs")
        mock_core_api.return_value.read_namespaced_pod_log.assert_called_once_with(
            name="test-pod",
            namespace="test-ns",
            container="test-container",
            timestamps=True,
        )

    @patch("kubernetes.client.CoreV1Api")
    @patch(
        "sagemaker.hyperpod.common.utils.validate_cluster_connection", return_value=True
    )
    def test_list_pods(self, mock_validate_connection, mock_core_api):
        mock_pod1 = MagicMock()
        mock_pod1.metadata.name = "pod1"
        mock_pod2 = MagicMock()
        mock_pod2.metadata.name = "pod2"
        mock_core_api.return_value.list_namespaced_pod.return_value.items = [
            mock_pod1,
            mock_pod2,
        ]

        result = self.base.list_pods(namespace="test-ns")

        self.assertEqual(result, ["pod1", "pod2"])
        mock_core_api.return_value.list_namespaced_pod.assert_called_once_with(
            namespace="test-ns"
        )

    @patch("kubernetes.client.CoreV1Api")
    @patch(
        "sagemaker.hyperpod.common.utils.validate_cluster_connection", return_value=True
    )
    def test_list_namespaces(self, mock_validate_connection, mock_core_api):
        mock_ns1 = MagicMock()
        mock_ns1.metadata.name = "namespace1"
        mock_ns2 = MagicMock()
        mock_ns2.metadata.name = "namespace2"
        mock_core_api.return_value.list_namespace.return_value.items = [
            mock_ns1,
            mock_ns2,
        ]

        result = self.base.list_namespaces()

        self.assertEqual(result, ["namespace1", "namespace2"])
        mock_core_api.return_value.list_namespace.assert_called_once()
