import unittest
from unittest.mock import patch, MagicMock
from kubernetes.client.exceptions import ApiException
from pydantic import ValidationError

from sagemaker.hyperpod.training.hyperpod_pytorch_job import (
    HyperPodPytorchJob,
    _handle_exception,
    _load_hp_job,
    _load_hp_job_list,
)
from sagemaker.hyperpod.inference.config.common import Metadata
from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_status import (
    HyperPodPytorchJobStatus,
)


class TestHyperPodPytorchJob(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.metadata = Metadata(name="test-job", namespace="default")
        self.job = HyperPodPytorchJob(metadata=self.metadata)

    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.validate_cluster_connection")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CustomObjectsApi")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.yaml.dump")
    def test_create_success(self, mock_yaml_dump, mock_custom_api, mock_validate):
        """Test successful job creation"""
        mock_validate.return_value = True
        mock_api_instance = MagicMock()
        mock_custom_api.return_value = mock_api_instance
        mock_yaml_dump.return_value = "test-config"

        with patch("builtins.print") as mock_print:
            self.job.create()

        mock_validate.assert_called_once()
        mock_custom_api.assert_called_once()
        mock_api_instance.create_namespaced_custom_object.assert_called_once()
        mock_print.assert_any_call("Deploying HyperPodPytorchJob with config:\n", "test-config", sep="")
        mock_print.assert_any_call("Successful submitted HyperPodPytorchJob!")

    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.validate_cluster_connection")
    def test_create_cluster_connection_failure(self, mock_validate):
        """Test job creation with cluster connection failure"""
        mock_validate.return_value = False

        with self.assertRaises(Exception) as context:
            self.job.create()

        self.assertIn("Failed to connect to the Kubernetes cluster", str(context.exception))

    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.validate_cluster_connection")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CustomObjectsApi")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job._handle_exception")
    def test_create_api_exception(self, mock_handle_exception, mock_custom_api, mock_validate):
        """Test job creation with API exception"""
        mock_validate.return_value = True
        mock_api_instance = MagicMock()
        mock_custom_api.return_value = mock_api_instance
        mock_api_instance.create_namespaced_custom_object.side_effect = ApiException(status=409)

        with patch("builtins.print") as mock_print:
            self.job.create()

        mock_handle_exception.assert_called_once()
        mock_print.assert_any_call("Failed to create HyperPodPytorchJob test-job!")

    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.validate_cluster_connection")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CustomObjectsApi")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job._load_hp_job_list")
    def test_list_success(self, mock_load_list, mock_custom_api, mock_validate):
        """Test successful job listing"""
        mock_validate.return_value = True
        mock_api_instance = MagicMock()
        mock_custom_api.return_value = mock_api_instance
        mock_response = {"items": []}
        mock_api_instance.list_namespaced_custom_object.return_value = mock_response
        mock_load_list.return_value = []

        result = HyperPodPytorchJob.list("test-namespace")

        mock_validate.assert_called_once()
        mock_api_instance.list_namespaced_custom_object.assert_called_once_with(
            group="sagemaker.amazonaws.com",
            version="v1",
            namespace="test-namespace",
            plural="hyperpodpytorchjobs",
        )
        mock_load_list.assert_called_once_with(mock_response)
        self.assertEqual(result, [])

    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.validate_cluster_connection")
    def test_list_cluster_connection_failure(self, mock_validate):
        """Test job listing with cluster connection failure"""
        mock_validate.return_value = False

        with self.assertRaises(Exception) as context:
            HyperPodPytorchJob.list()

        self.assertIn("Failed to connect to the Kubernetes cluster", str(context.exception))

    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.validate_cluster_connection")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CustomObjectsApi")
    def test_delete_success(self, mock_custom_api, mock_validate):
        """Test successful job deletion"""
        mock_validate.return_value = True
        mock_api_instance = MagicMock()
        mock_custom_api.return_value = mock_api_instance

        with patch("builtins.print") as mock_print:
            self.job.delete()

        mock_api_instance.delete_namespaced_custom_object.assert_called_once_with(
            group="sagemaker.amazonaws.com",
            version="v1",
            namespace="default",
            plural="hyperpodpytorchjobs",
            name="test-job",
        )
        mock_print.assert_any_call("Successful deleted HyperPodPytorchJob!")

    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.validate_cluster_connection")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CustomObjectsApi")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job._load_hp_job")
    def test_get_success(self, mock_load_job, mock_custom_api, mock_validate):
        """Test successful job retrieval"""
        mock_validate.return_value = True
        mock_api_instance = MagicMock()
        mock_custom_api.return_value = mock_api_instance
        mock_response = {"metadata": {"name": "test-job"}}
        mock_api_instance.get_namespaced_custom_object.return_value = mock_response
        expected_job = HyperPodPytorchJob(metadata=self.metadata)
        mock_load_job.return_value = expected_job

        result = HyperPodPytorchJob.get("test-job", "test-namespace")

        mock_api_instance.get_namespaced_custom_object.assert_called_once_with(
            group="sagemaker.amazonaws.com",
            version="v1",
            namespace="test-namespace",
            plural="hyperpodpytorchjobs",
            name="test-job",
        )
        mock_load_job.assert_called_once_with(mock_response)
        self.assertEqual(result, expected_job)

    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.validate_cluster_connection")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CustomObjectsApi")
    def test_refresh_success(self, mock_custom_api, mock_validate):
        """Test successful job refresh"""
        mock_validate.return_value = True
        mock_api_instance = MagicMock()
        mock_custom_api.return_value = mock_api_instance
        mock_response = {
            "status": {
                "completionTime": "2023-01-01T00:00:00Z",
                "conditions": []
            }
        }
        mock_api_instance.get_namespaced_custom_object.return_value = mock_response

        self.job.refresh()

        mock_api_instance.get_namespaced_custom_object.assert_called_once_with(
            group="sagemaker.amazonaws.com",
            version="v1",
            namespace="default",
            plural="hyperpodpytorchjobs",
            name="test-job",
        )
        self.assertIsInstance(self.job.status, HyperPodPytorchJobStatus)

    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.validate_cluster_connection")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.config.load_kube_config")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CoreV1Api")
    def test_list_pods_success(self, mock_core_api, mock_load_config, mock_validate):
        """Test successful pod listing"""
        mock_validate.return_value = True
        mock_api_instance = MagicMock()
        mock_core_api.return_value = mock_api_instance
        
        # Mock pod response
        mock_pod1 = MagicMock()
        mock_pod1.metadata.name = "test-job-pod-0"
        mock_pod2 = MagicMock()
        mock_pod2.metadata.name = "other-job-pod-0"
        mock_pod3 = MagicMock()
        mock_pod3.metadata.name = "test-job-pod-1"
        
        mock_response = MagicMock()
        mock_response.items = [mock_pod1, mock_pod2, mock_pod3]
        mock_api_instance.list_namespaced_pod.return_value = mock_response

        result = self.job.list_pods()

        mock_load_config.assert_called_once()
        mock_api_instance.list_namespaced_pod.assert_called_once_with("default")
        self.assertEqual(result, ["test-job-pod-0", "test-job-pod-1"])

    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.validate_cluster_connection")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.config.load_kube_config")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CoreV1Api")
    def test_get_logs_from_pod_success(self, mock_core_api, mock_load_config, mock_validate):
        """Test successful log retrieval from pod"""
        mock_validate.return_value = True
        mock_api_instance = MagicMock()
        mock_core_api.return_value = mock_api_instance
        mock_api_instance.read_namespaced_pod_log.return_value = "test logs"
        
        # Set up replica specs for container name
        self.job.replicaSpecs = [MagicMock()]
        self.job.replicaSpecs[0].template.spec.containers = [MagicMock()]
        self.job.replicaSpecs[0].template.spec.containers[0].name = "test-container"

        result = self.job.get_logs_from_pod("test-pod")

        mock_api_instance.read_namespaced_pod_log.assert_called_once_with(
            name="test-pod",
            namespace="default",
            timestamps=True,
            container="test-container",
        )
        self.assertEqual(result, "test logs")

    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.validate_cluster_connection")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.config.load_kube_config")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CoreV1Api")
    def test_get_logs_from_pod_with_container_name(self, mock_core_api, mock_load_config, mock_validate):
        """Test log retrieval with specific container name"""
        mock_validate.return_value = True
        mock_api_instance = MagicMock()
        mock_core_api.return_value = mock_api_instance
        mock_api_instance.read_namespaced_pod_log.return_value = "test logs"

        result = self.job.get_logs_from_pod("test-pod", "specific-container")

        mock_api_instance.read_namespaced_pod_log.assert_called_once_with(
            name="test-pod",
            namespace="default",
            timestamps=True,
            container="specific-container",
        )
        self.assertEqual(result, "test logs")


class TestHandleException(unittest.TestCase):
    """Test the _handle_exception function"""

    def test_handle_api_exception_401(self):
        """Test handling 401 API exception"""
        exception = ApiException(status=401)
        with self.assertRaises(Exception) as context:
            _handle_exception(exception, "test-job", "default")
        self.assertIn("Credentials unauthorized", str(context.exception))

    def test_handle_api_exception_403(self):
        """Test handling 403 API exception"""
        exception = ApiException(status=403)
        with self.assertRaises(Exception) as context:
            _handle_exception(exception, "test-job", "default")
        self.assertIn("Access denied to resource 'test-job' in 'default'", str(context.exception))

    def test_handle_api_exception_404(self):
        """Test handling 404 API exception"""
        exception = ApiException(status=404)
        with self.assertRaises(Exception) as context:
            _handle_exception(exception, "test-job", "default")
        self.assertIn("Resource 'test-job' not found in 'default'", str(context.exception))

    def test_handle_api_exception_409(self):
        """Test handling 409 API exception"""
        exception = ApiException(status=409)
        with self.assertRaises(Exception) as context:
            _handle_exception(exception, "test-job", "default")
        self.assertIn("Resource 'test-job' already exists in 'default'", str(context.exception))

    def test_handle_api_exception_500(self):
        """Test handling 500 API exception"""
        exception = ApiException(status=500)
        with self.assertRaises(Exception) as context:
            _handle_exception(exception, "test-job", "default")
        self.assertIn("Kubernetes API internal server error", str(context.exception))

    def test_handle_api_exception_unhandled(self):
        """Test handling unhandled API exception"""
        exception = ApiException(status=418, reason="I'm a teapot")
        with self.assertRaises(Exception) as context:
            _handle_exception(exception, "test-job", "default")
        self.assertIn("Unhandled Kubernetes error: 418 I'm a teapot", str(context.exception))

    def test_handle_validation_error(self):
        """Test handling validation error"""
        exception = ValidationError.from_exception_data("test", [])
        with self.assertRaises(Exception) as context:
            _handle_exception(exception, "test-job", "default")
        self.assertIn("Response did not match expected schema", str(context.exception))

    def test_handle_generic_exception(self):
        """Test handling generic exception"""
        exception = ValueError("test error")
        with self.assertRaises(ValueError):
            _handle_exception(exception, "test-job", "default")


class TestLoadHpJob(unittest.TestCase):
    """Test the _load_hp_job function"""

    def test_load_hp_job_with_status(self):
        """Test loading job with status"""
        response = {
            "metadata": {"name": "test-job", "namespace": "default"},
            "spec": {"nprocPerNode": "auto"},
            "status": {"completionTime": "2023-01-01T00:00:00Z", "conditions": []}
        }

        result = _load_hp_job(response)

        self.assertIsInstance(result, HyperPodPytorchJob)
        self.assertEqual(result.metadata.name, "test-job")
        self.assertEqual(result.metadata.namespace, "default")
        self.assertIsInstance(result.status, HyperPodPytorchJobStatus)

    def test_load_hp_job_without_status(self):
        """Test loading job without status"""
        response = {
            "metadata": {"name": "test-job", "namespace": "default"},
            "spec": {"nprocPerNode": "auto"}
        }

        result = _load_hp_job(response)

        self.assertIsInstance(result, HyperPodPytorchJob)
        self.assertEqual(result.metadata.name, "test-job")
        self.assertEqual(result.metadata.namespace, "default")
        self.assertIsNone(result.status)


class TestLoadHpJobList(unittest.TestCase):
    """Test the _load_hp_job_list function"""

    def test_load_hp_job_list(self):
        """Test loading job list"""
        response = {
            "items": [
                {
                    "metadata": {"name": "job1", "namespace": "default"},
                    "spec": {"nprocPerNode": "auto"}
                },
                {
                    "metadata": {"name": "job2", "namespace": "test"},
                    "spec": {"nprocPerNode": "2"}
                }
            ]
        }

        result = _load_hp_job_list(response)

        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], HyperPodPytorchJob)
        self.assertIsInstance(result[1], HyperPodPytorchJob)
        self.assertEqual(result[0].metadata.name, "job1")
        self.assertEqual(result[1].metadata.name, "job2")

    def test_load_hp_job_list_empty(self):
        """Test loading empty job list"""
        response = {"items": []}

        result = _load_hp_job_list(response)

        self.assertEqual(len(result), 0)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()