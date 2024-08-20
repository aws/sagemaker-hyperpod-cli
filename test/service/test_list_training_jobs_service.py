import unittest
from unittest import mock
from unittest.mock import MagicMock

from hyperpod_cli.clients.kubernetes_client import KubernetesClient
from hyperpod_cli.service.list_training_jobs import ListTrainingJobs

SAMPLE_OUTPUT = {
    "items": [
        {
            "metadata": {"name": "test-name", "namespace": "test-namespace"},
            "status": {"startTime": "test-time", "conditions": [{"type": "Succeeded"}]},
        },
        {
            "metadata": {"name": "test-name1", "namespace": "test-namespace1"},
            "status": {
                "startTime": "test-time1",
                "conditions": [
                    {"type": "Running"},
                    {
                        "type": "Created",
                    },
                ],
            },
        },
        {
            "metadata": {"name": "test-name2", "namespace": "test-namespace1"},
            "status": {"startTime": "test-time1", "conditions": [{"type": "Created"}]},
        },
    ]
}
INVALID_OUTPUT = {
    "items": [
        {
            "status": {"startTime": "test-time", "conditions": [{"type": "Succeeded"}]},
        }
    ]
}
OUTPUT_WITHOUT_STATUS = {
    "items": [
        {
            "metadata": {"name": "test-name", "namespace": "test-namespace"},
        }
    ]
}


class ListTrainingJobsTest(unittest.TestCase):
    def setUp(self):
        self.mock_list_training_jobs = ListTrainingJobs()
        self.mock_k8s_client = MagicMock(spec=KubernetesClient)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_with_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_training_jobs.return_value = SAMPLE_OUTPUT
        result = self.mock_list_training_jobs.list_training_jobs("namespace", None, None)
        self.assertIn("test-name", result)
        self.assertIn("test-name1", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_without_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.list_training_jobs.return_value = SAMPLE_OUTPUT
        result = self.mock_list_training_jobs.list_training_jobs(None, None, None)
        self.assertIn("test-name", result)
        self.assertIn("test-name1", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_without_namespace_no_jobs(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.list_training_jobs.return_value = {"items": []}
        result = self.mock_list_training_jobs.list_training_jobs(None, None, None)
        self.assertNotIn("test-name", result)
        self.assertNotIn("test-name1", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_all_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_namespaces.return_value = ["namespace"]
        self.mock_k8s_client.list_training_jobs.return_value = SAMPLE_OUTPUT
        result = self.mock_list_training_jobs.list_training_jobs(None, True, None)
        self.assertIn("test-name", result)
        self.assertIn("test-name1", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_all_namespace_no_jobs(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_namespaces.return_value = ["namespace"]
        self.mock_k8s_client.list_training_jobs.return_value = {"items": []}
        result = self.mock_list_training_jobs.list_training_jobs(None, True, None)
        self.assertNotIn("test-name", result)
        self.assertNotIn("test-name1", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_all_namespace_missing_metadata(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_namespaces.return_value = ["namespace"]
        self.mock_k8s_client.list_training_jobs.return_value = INVALID_OUTPUT
        result = self.mock_list_training_jobs.list_training_jobs(None, True, None)
        self.assertNotIn("name", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_all_namespace_missing_status(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_namespaces.return_value = ["namespace"]
        self.mock_k8s_client.list_training_jobs.return_value = OUTPUT_WITHOUT_STATUS
        result = self.mock_list_training_jobs.list_training_jobs(None, True, None)
        self.assertNotIn("State: null", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_unknown_status(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        unknown_status_sample_output = {
            "items": [
                {
                    "metadata": {"name": "test-name", "namespace": "test-namespace"},
                    "status": {"startTime": "test-time", "conditions": [{"type": "unknown"}]},
                }
            ]
        }
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_namespaces.return_value = ["namespace"]
        self.mock_k8s_client.list_training_jobs.return_value = unknown_status_sample_output
        with self.assertRaises(RuntimeError):
            self.mock_list_training_jobs.list_training_jobs(None, True, None)
