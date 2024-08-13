import unittest
from unittest import mock
from unittest.mock import MagicMock

from hyperpod_cli.clients.kubernetes_client import KubernetesClient
from hyperpod_cli.service.get_logs import GetLogs
from hyperpod_cli.service.list_pods import ListPods


class TestGetLogs(unittest.TestCase):

    def setUp(self):
        self.mock_get_logs = GetLogs()
        self.mock_list_pods_service = MagicMock(spec=ListPods)
        self.mock_k8s_client = MagicMock(spec=KubernetesClient)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_get_logs_with_namespace(
        self,
        mock_list_training_job_pods_service_with_list_pods: mock.Mock,
        mock_list_training_job_pods_service: mock.Mock,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_list_training_job_pods_service.return_value = self.mock_list_pods_service
        mock_list_training_job_pods_service_with_list_pods.return_value = ["test-pod"]
        self.mock_k8s_client.get_logs_for_pod.return_value = "test logs"
        result = self.mock_get_logs.get_training_job_logs("sample-job", "test-pod", "kubeflow")
        self.assertIn("test logs", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_get_logs_without_namespace(
        self,
        mock_list_training_job_pods_service_with_list_pods: mock.Mock,
        mock_list_training_job_pods_service: mock.Mock,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_list_training_job_pods_service.return_value = self.mock_list_pods_service
        self.mock_k8s_client.get_current_context_namespace.return_value = "kubeflow"
        mock_list_training_job_pods_service_with_list_pods.return_value = ["test-pod"]
        self.mock_k8s_client.get_logs_for_pod.return_value = "test logs"
        result = self.mock_get_logs.get_training_job_logs("sample-job", "test-pod", None)
        self.assertIn("test logs", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_get_logs_pod_not_found_for_job(
        self,
        mock_list_training_job_pods_service_with_list_pods: mock.Mock,
        mock_list_training_job_pods_service: mock.Mock,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_list_training_job_pods_service.return_value = self.mock_list_pods_service
        self.mock_k8s_client.get_current_context_namespace.return_value = "kubeflow"
        mock_list_training_job_pods_service_with_list_pods.return_value = ["test-pod"]
        self.mock_k8s_client.get_logs_for_pod.return_value = "test logs"
        with self.assertRaises(RuntimeError):
            self.mock_get_logs.get_training_job_logs("sample-job", "test-pod1", None)
