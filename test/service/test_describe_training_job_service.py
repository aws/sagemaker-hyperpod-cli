import unittest
from unittest import mock
from unittest.mock import MagicMock

from hyperpod_cli.clients.kubernetes_client import KubernetesClient
from hyperpod_cli.service.describe_training_job import DescribeTrainingJob


class DescribeTrainingJobTest(unittest.TestCase):
    def setUp(self):
        self.mock_describe_training_job = DescribeTrainingJob()
        self.mock_k8s_client = MagicMock(spec=KubernetesClient)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_describe_training_job_with_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.describe_training_job.return_value = {
            "metadata": {"name": "pytorch-simple"}
        }
        result = self.mock_describe_training_job.describe_training_job(
            "sample-job", "namespace", None
        )
        self.assertIn("pytorch-simple", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_describe_training_job_without_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.describe_training_job.return_value = {
            "metadata": {"name": "pytorch-simple"}
        }
        result = self.mock_describe_training_job.describe_training_job("sample-job", None, None)
        self.assertIn("pytorch-simple", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_describe_training_job_with_verbose(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.describe_training_job.return_value = {
            "metadata": {"name": "pytorch-simple"}
        }
        result = self.mock_describe_training_job.describe_training_job("sample-job", None, True)
        self.assertIn("pytorch-simple", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_describe_training_job_with_verbose_with_no_output(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.describe_training_job.return_value = None
        result = self.mock_describe_training_job.describe_training_job("sample-job", None, True)
        self.assertIn("", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_describe_training_job_without_verbose_with_no_output(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.describe_training_job.return_value = None
        result = self.mock_describe_training_job.describe_training_job("sample-job", None, False)
        self.assertIn("", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_describe_training_job_without_verbose_without_metadata(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.describe_training_job.return_value = {"status": "test_status"}
        result = self.mock_describe_training_job.describe_training_job("sample-job", None, False)
        self.assertIn("test_status", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_describe_training_job_with_verbose_with_values(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.describe_training_job.return_value = {
            "metadata": {"name": "pytorch-simple"},
            "kind": "test_kind",
            "apiVersion": "test_apiVersion",
            "spec": "test_spec",
            "status": "test_status",
        }
        result = self.mock_describe_training_job.describe_training_job("sample-job", None, True)
        print(result)
        self.assertIn("pytorch-simple", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_describe_training_job_with_verbose_without_metadata(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.describe_training_job.return_value = {
            "kind": "test_kind",
            "apiVersion": "test_apiVersion",
            "spec": "test_spec",
            "status": "test_status",
        }
        result = self.mock_describe_training_job.describe_training_job("sample-job", None, True)
        print(result)
        self.assertIn("test_status", result)
