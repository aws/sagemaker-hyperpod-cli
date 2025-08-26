import unittest
from unittest.mock import patch, MagicMock, Mock
from kubernetes.client.exceptions import ApiException

from sagemaker.hyperpod.training import (
    HyperPodPytorchJob,
    HyperPodPytorchJobStatus,
    Containers,
    ReplicaSpec,
    Resources,
    RunPolicy,
    Spec,
    Template,
    _load_hp_job,
    _load_hp_job_list,
)
from sagemaker.hyperpod.common.config import Metadata


class TestHyperPodPytorchJob(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.metadata = Metadata(name="test-job", namespace="default")
        replica_specs = [
            ReplicaSpec(
                name="pod",
                template=Template(
                    spec=Spec(
                        containers=[
                            Containers(
                                name="test-container",
                                image="test-image",
                                resources=Resources(
                                    requests={"nvidia.com/gpu": "0"},
                                    limits={"nvidia.com/gpu": "0"},
                                ),
                            )
                        ]
                    )
                ),
            )
        ]
        run_policy = RunPolicy(clean_pod_policy="None")
        self.job = HyperPodPytorchJob(
            metadata=self.metadata,
            nproc_per_node="auto",
            replica_specs=replica_specs,
            run_policy=run_policy,
        )
        
    @patch("kubernetes.config.load_kube_config")
    def test_verify_kube_config(self, mock_load_config):
        """Test verify_kube_config method"""        
        HyperPodPytorchJob.is_kubeconfig_loaded = False
        
        # Mock the verify_kubernetes_version_compatibility function directly in the module
        with patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.verify_kubernetes_version_compatibility") as mock_verify:
            HyperPodPytorchJob.verify_kube_config()
            
            mock_load_config.assert_called_once()
            mock_verify.assert_called_once()
            self.assertTrue(HyperPodPytorchJob.is_kubeconfig_loaded)
            
            mock_load_config.reset_mock()
            mock_verify.reset_mock()
            
            # Second call should do nothing since config is already loaded
            HyperPodPytorchJob.verify_kube_config()
            
            mock_load_config.assert_not_called()
            mock_verify.assert_not_called()

    @patch.object(HyperPodPytorchJob, "verify_kube_config")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CustomObjectsApi")
    def test_create_success(self, mock_custom_api, mock_verify_config):
        """Test successful job creation"""
        mock_api_instance = MagicMock()
        mock_custom_api.return_value = mock_api_instance

        self.job.create(debug=True)

        mock_verify_config.assert_called_once()
        mock_custom_api.assert_called_once()
        mock_api_instance.create_namespaced_custom_object.assert_called_once()

    @patch.object(HyperPodPytorchJob, "verify_kube_config")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CustomObjectsApi")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.handle_exception")
    def test_create_api_exception(
        self, mock_handle_exception, mock_custom_api, mock_verify_config
    ):
        """Test job creation with API exception"""
        mock_api_instance = MagicMock()
        mock_custom_api.return_value = mock_api_instance
        mock_api_instance.create_namespaced_custom_object.side_effect = ApiException(
            status=409
        )

        self.job.create()

        mock_handle_exception.assert_called_once()

    @patch.object(HyperPodPytorchJob, "verify_kube_config")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CustomObjectsApi")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job._load_hp_job_list")
    def test_list_success(self, mock_load_list, mock_custom_api, mock_verify_config):
        """Test successful job listing"""
        mock_api_instance = MagicMock()
        mock_custom_api.return_value = mock_api_instance
        mock_response = {"items": [{"metadata": {"name": "test-job"}}]}
        mock_api_instance.list_namespaced_custom_object.return_value = mock_response
        mock_load_list.return_value = [
            HyperPodPytorchJob(metadata=Metadata(name="test-job"))
        ]

        result = HyperPodPytorchJob.list("test-namespace")

        mock_verify_config.assert_called_once()
        mock_api_instance.list_namespaced_custom_object.assert_called_once_with(
            group="sagemaker.amazonaws.com",
            version="v1",
            namespace="test-namespace",
            plural="hyperpodpytorchjobs",
        )
        mock_load_list.assert_called_once_with(mock_response)
        self.assertEqual(
            result, [HyperPodPytorchJob(metadata=Metadata(name="test-job"))]
        )

    @patch.object(HyperPodPytorchJob, "verify_kube_config")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CustomObjectsApi")
    def test_delete_success(self, mock_custom_api, mock_verify_config):
        """Test successful job deletion"""
        mock_api_instance = MagicMock()
        mock_custom_api.return_value = mock_api_instance

        self.job.delete()

        mock_api_instance.delete_namespaced_custom_object.assert_called_once_with(
            group="sagemaker.amazonaws.com",
            version="v1",
            namespace="default",
            plural="hyperpodpytorchjobs",
            name="test-job",
        )

    @patch.object(HyperPodPytorchJob, "verify_kube_config")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CustomObjectsApi")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job._load_hp_job")
    def test_get_success(self, mock_load_job, mock_custom_api, mock_verify_config):
        """Test successful job retrieval"""
        mock_api_instance = MagicMock()
        mock_custom_api.return_value = mock_api_instance
        mock_response = {"metadata": {"name": "test-job"}}
        mock_api_instance.get_namespaced_custom_object.return_value = mock_response
        replica_specs = [
            ReplicaSpec(
                name="pod",
                template=Template(
                    spec=Spec(
                        containers=[
                            Containers(
                                name="test-container",
                                image="test-image",
                                resources=Resources(
                                    requests={"nvidia.com/gpu": "0"},
                                    limits={"nvidia.com/gpu": "0"},
                                ),
                            )
                        ]
                    )
                ),
            )
        ]
        run_policy = RunPolicy(clean_pod_policy="None")
        expected_job = HyperPodPytorchJob(
            metadata=self.metadata,
            nproc_per_node="auto",
            replica_specs=replica_specs,
            run_policy=run_policy,
        )
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

    @patch.object(HyperPodPytorchJob, "verify_kube_config")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CustomObjectsApi")
    def test_refresh_success(self, mock_custom_api, mock_verify_config):
        """Test successful job refresh"""
        mock_api_instance = MagicMock()
        mock_custom_api.return_value = mock_api_instance
        mock_response = {
            "status": {"completionTime": "2023-01-01T00:00:00Z", "conditions": []}
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

    @patch.object(HyperPodPytorchJob, "verify_kube_config")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.config.load_kube_config")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CoreV1Api")
    def test_list_pods_success(self, mock_core_api, mock_load_config, mock_verify_config):
        """Test successful pod listing"""
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

    @patch.object(HyperPodPytorchJob, "verify_kube_config")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.config.load_kube_config")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CoreV1Api")
    def test_get_logs_from_pod_success(
        self, mock_core_api, mock_load_config, mock_verify_config
    ):
        """Test successful log retrieval from pod"""
        mock_api_instance = MagicMock()
        mock_core_api.return_value = mock_api_instance
        mock_api_instance.read_namespaced_pod_log.return_value = "test logs"

        result = self.job.get_logs_from_pod("test-pod")

        mock_api_instance.read_namespaced_pod_log.assert_called_once_with(
            name="test-pod",
            namespace="default",
            timestamps=True,
            container="test-container",
        )
        self.assertEqual(result, "test logs")
        
    @patch.object(HyperPodPytorchJob, "verify_kube_config")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.config.load_kube_config")
    @patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CoreV1Api")
    def test_get_logs_from_pod_with_container_name(
        self, mock_core_api, mock_load_config, mock_verify_config
    ):
        """Test log retrieval with specific container name"""
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

    @patch("kubernetes.client.CoreV1Api")
    @patch.object(HyperPodPytorchJob, "verify_kube_config")
    def test_get_operator_logs(self, mock_verify_config, mock_core_api):
        # Mock only the training operator pod (since we're using label selector)
        mock_operator_pod = MagicMock()
        mock_operator_pod.metadata.name = "training-operator-pod-abc123"
        
        mock_core_api.return_value.list_namespaced_pod.return_value.items = [mock_operator_pod]
        mock_core_api.return_value.read_namespaced_pod_log.return_value = "training operator logs"

        result = HyperPodPytorchJob.get_operator_logs(2.5)

        self.assertEqual(result, "training operator logs")
        # Verify label selector is used
        mock_core_api.return_value.list_namespaced_pod.assert_called_once_with(
            namespace="aws-hyperpod",
            label_selector="hp-training-control-plane"
        )
        mock_core_api.return_value.read_namespaced_pod_log.assert_called_once_with(
            name="training-operator-pod-abc123",
            namespace="aws-hyperpod",
            timestamps=True,
            since_seconds=9000,
        )


class TestLoadHpJob(unittest.TestCase):
    """Test the _load_hp_job function"""

    def test_load_hp_job_with_status(self):
        """Test loading job with status"""
        response = {
            "metadata": {"name": "test-job", "namespace": "default"},
            "spec": {"nproc_per_node": "auto"},
            "status": {"completionTime": "2023-01-01T00:00:00Z", "conditions": []},
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
            "spec": {"nproc_per_node": "auto"},
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
                    "spec": {"nproc_per_node": "auto"},
                },
                {
                    "metadata": {"name": "job2", "namespace": "test"},
                    "spec": {"nproc_per_node": "2"},
                },
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
