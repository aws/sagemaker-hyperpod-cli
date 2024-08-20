import unittest
from unittest import mock
from unittest.mock import MagicMock

from hyperpod_cli.clients.kubernetes_client import KubernetesClient
from hyperpod_cli.service.cancel_training_job import CancelTrainingJob


class CancelTrainingJobTest(unittest.TestCase):
    def setUp(self):
        self.mock_cancel_training_job = CancelTrainingJob()
        self.mock_k8s_client = MagicMock(spec=KubernetesClient)

    @mock.patch('subprocess.run')
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_cancel_training_job_with_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
        mock_subprocess_run: mock.Mock
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.delete_training_job.return_value = {"status": "Success"}
        result = self.mock_cancel_training_job.cancel_training_job("sample-job", "namespace")
        self.assertIsNone(result)
        mock_subprocess_run.assert_called_once()

    @mock.patch('subprocess.run')
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_cancel_training_job_without_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
        mock_subprocess_run: mock.Mock
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.delete_training_job.return_value = {"status": "Success"}
        result = self.mock_cancel_training_job.cancel_training_job("sample-job", None)
        self.assertIsNone(result)
        mock_subprocess_run.assert_called_once()
