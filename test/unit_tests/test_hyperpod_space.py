import unittest
from unittest.mock import Mock, patch, MagicMock
from kubernetes.client.rest import ApiException

from sagemaker.hyperpod.space.hyperpod_space import HPSpace
from hyperpod_space_template.v1_0.model import SpaceConfig


class TestHPSpace(unittest.TestCase):
    """Test cases for HPSpace PySDK"""

    def setUp(self):
        """Setup test fixtures"""
        self.mock_config = SpaceConfig(
            name="test-space",
            display_name="Test Space",
            namespace="test-namespace",
            image="test-image:latest",
            desired_status="Running"
        )
        self.hp_space = HPSpace(config=self.mock_config)

    @patch('sagemaker.hyperpod.space.hyperpod_space.config.load_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space.verify_kubernetes_version_compatibility')
    def test_verify_kube_config_success(self, mock_verify_k8s, mock_load_config):
        """Test successful kubeconfig verification"""
        HPSpace.is_kubeconfig_loaded = False
        HPSpace.verify_kube_config()
        
        mock_load_config.assert_called_once()
        mock_verify_k8s.assert_called_once()
        self.assertTrue(HPSpace.is_kubeconfig_loaded)

    @patch('sagemaker.hyperpod.space.hyperpod_space.config.load_kube_config')
    def test_verify_kube_config_failure(self, mock_load_config):
        """Test kubeconfig verification failure"""
        HPSpace.is_kubeconfig_loaded = False
        mock_load_config.side_effect = Exception("Config load failed")
        
        with self.assertRaises(RuntimeError) as context:
            HPSpace.verify_kube_config()
        self.assertIn("Failed to load kubeconfig: Config load failed", str(context.exception))

    def test_verify_kube_config_already_loaded(self):
        """Test kubeconfig verification when already loaded"""
        HPSpace.is_kubeconfig_loaded = True
        
        with patch('sagemaker.hyperpod.space.hyperpod_space.config.load_kube_config') as mock_load_config:
            HPSpace.verify_kube_config()
            mock_load_config.assert_not_called()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch.object(HPSpace, 'space_exists')
    def test_create_success(self, mock_space_exists, mock_verify_config, mock_custom_api_class):
        """Test successful dev space creation"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_space_exists.return_value = False
        
        # Mock the config.to_domain() method
        mock_domain_config = {
            "space_spec": {
                "apiVersion": "workspace.jupyter.org/v1alpha1",
                "kind": "Workspace",
                "metadata": {"name": "test-space", "namespace": "test-namespace"},
                "spec": {"image": "test-image:latest"}
            }
        }
        
        with patch('hyperpod_space_template.v1_0.model.SpaceConfig.to_domain', return_value=mock_domain_config):
            self.hp_space.create()
        
        mock_verify_config.assert_called_once()
        mock_space_exists.assert_called_once()
        mock_custom_api.create_namespaced_custom_object.assert_called_once()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch.object(HPSpace, 'space_exists')
    def test_create_already_exists(self, mock_space_exists, mock_verify_config, mock_custom_api_class):
        """Test dev space creation when resource already exists"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_space_exists.return_value = True
        
        self.hp_space.create()
        
        mock_verify_config.assert_called_once()
        mock_space_exists.assert_called_once()
        # Should not call create since resource exists
        mock_custom_api.create_namespaced_custom_object.assert_not_called()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space.handle_exception')
    @patch.object(HPSpace, 'space_exists')
    def test_create_failure(self, mock_space_exists, mock_handle_exception, mock_verify_config, mock_custom_api_class):
        """Test dev space creation failure"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_space_exists.return_value = False
        
        # Mock creation failure
        mock_custom_api.create_namespaced_custom_object.side_effect = Exception("Creation failed")
        
        mock_domain_config = {
            "space_spec": {
                "apiVersion": "workspace.jupyter.org/v1alpha1",
                "kind": "Workspace",
                "metadata": {"name": "test-space", "namespace": "test-namespace"},
                "spec": {"image": "test-image:latest"}
            }
        }
        
        with patch('hyperpod_space_template.v1_0.model.SpaceConfig.to_domain', return_value=mock_domain_config):
            self.hp_space.create()
        
        mock_handle_exception.assert_called_once()

    def test_space_exists_success(self):
        """Test space_exists method when space exists"""
        with patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi') as mock_custom_api_class:
            mock_custom_api = Mock()
            mock_custom_api_class.return_value = mock_custom_api
            mock_custom_api.get_namespaced_custom_object.return_value = {
                "metadata": {"name": "test-space", "namespace": "test-namespace"}
            }
            
            result = self.hp_space.space_exists()
            self.assertTrue(result)

    def test_space_exists_not_found(self):
        """Test space_exists method when space doesn't exist"""
        with patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi') as mock_custom_api_class:
            mock_custom_api = Mock()
            mock_custom_api_class.return_value = mock_custom_api
            mock_custom_api.get_namespaced_custom_object.side_effect = ApiException(status=404)
            
            result = self.hp_space.space_exists()
            self.assertFalse(result)

    def test_space_exists_api_error(self):
        """Test space_exists method with non-404 API error"""
        with patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi') as mock_custom_api_class:
            mock_custom_api = Mock()
            mock_custom_api_class.return_value = mock_custom_api
            mock_custom_api.get_namespaced_custom_object.side_effect = ApiException(status=500)
            
            with self.assertRaises(ApiException):
                self.hp_space.space_exists()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space.get_default_namespace')
    def test_list_success(self, mock_get_namespace, mock_verify_config, mock_custom_api_class):
        """Test successful dev space listing"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_get_namespace.return_value = "default"
        
        mock_response = {
            "items": [
                {
                    "metadata": {"name": "space1", "namespace": "default"},
                    "spec": {"image": "image1:latest", "displayName": "Space 1"},
                },
                {
                    "metadata": {"name": "space2", "namespace": "default"},
                    "spec": {"image": "image2:latest", "displayName": "Space 2"},
                }
            ]
        }
        mock_custom_api.list_namespaced_custom_object.return_value = mock_response
        
        result = HPSpace.list()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].config.name, "space1")
        self.assertEqual(result[1].config.name, "space2")
        mock_custom_api.list_namespaced_custom_object.assert_called_once()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    def test_list_with_namespace(self, mock_verify_config, mock_custom_api_class):
        """Test dev space listing with specific namespace"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        
        mock_response = {"items": []}
        mock_custom_api.list_namespaced_custom_object.return_value = mock_response
        
        HPSpace.list(namespace="custom-namespace")
        
        mock_custom_api.list_namespaced_custom_object.assert_called_once_with(
            group="workspace.jupyter.org",
            version="v1alpha1",
            namespace="custom-namespace",
            plural="workspaces"
        )

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space.handle_exception')
    def test_list_failure(self, mock_handle_exception, mock_verify_config, mock_custom_api_class):
        """Test dev space listing failure"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_custom_api.list_namespaced_custom_object.side_effect = Exception("List failed")
        
        HPSpace.list(namespace="test-namespace")

        mock_handle_exception.assert_called_once()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    def test_get_success(self, mock_verify_config, mock_custom_api_class):
        """Test successful dev space retrieval"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        
        mock_response = {
            "metadata": {"name": "test-space", "namespace": "test-namespace"},
            "spec": {"image": "test-image:latest", "displayName": "Test Space"},
        }
        mock_custom_api.get_namespaced_custom_object.return_value = mock_response
        
        result = HPSpace.get(name="test-space", namespace="test-namespace")
        
        self.assertEqual(result.config.name, "test-space")
        mock_custom_api.get_namespaced_custom_object.assert_called_once()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space.handle_exception')
    def test_get_failure(self, mock_handle_exception, mock_verify_config, mock_custom_api_class):
        """Test dev space retrieval failure"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_custom_api.get_namespaced_custom_object.side_effect = Exception("Get failed")
        
        HPSpace.get(name="test-space", namespace="test-namespace")

        mock_custom_api.get_namespaced_custom_object.assert_called_once_with(
            group="workspace.jupyter.org",
            version="v1alpha1",
            namespace="test-namespace",
            plural="workspaces",
            name='test-space'
        )
        mock_handle_exception.assert_called_once()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch.object(HPSpace, 'space_exists')
    def test_delete_success(self, mock_space_exists, mock_verify_config, mock_custom_api_class):
        """Test successful dev space deletion"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_space_exists.return_value = True
        
        self.hp_space.delete()
        
        mock_verify_config.assert_called_once()
        mock_space_exists.assert_called_once()
        mock_custom_api.delete_namespaced_custom_object.assert_called_once_with(
            group="workspace.jupyter.org",
            version="v1alpha1",
            namespace="test-namespace",
            plural="workspaces",
            name="test-space"
        )

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch.object(HPSpace, 'space_exists')
    def test_delete_not_exists(self, mock_space_exists, mock_verify_config, mock_custom_api_class):
        """Test dev space deletion when space doesn't exist"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_space_exists.return_value = False
        
        self.hp_space.delete()
        
        mock_verify_config.assert_called_once()
        mock_space_exists.assert_called_once()
        # Should not call delete since resource doesn't exist
        mock_custom_api.delete_namespaced_custom_object.assert_not_called()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space.handle_exception')
    @patch.object(HPSpace, 'space_exists')
    def test_delete_failure(self, mock_space_exists, mock_handle_exception, mock_verify_config, mock_custom_api_class):
        """Test dev space deletion failure"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_space_exists.return_value = True
        mock_custom_api.delete_namespaced_custom_object.side_effect = Exception("Delete failed")
        
        self.hp_space.delete()
        
        mock_handle_exception.assert_called_once()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch.object(HPSpace, 'space_exists')
    def test_update_success(self, mock_space_exists, mock_verify_config, mock_custom_api_class):
        """Test successful dev space update"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_space_exists.return_value = True
        
        mock_domain_config = {
            "space_spec": {
                "spec": {"desiredStatus": "Stopped"}
            }
        }
        
        with patch('hyperpod_space_template.v1_0.model.SpaceConfig.to_domain', return_value=mock_domain_config):
            self.hp_space.update(desired_status="Stopped")
        
        mock_custom_api.patch_namespaced_custom_object.assert_called_once_with(
            group="workspace.jupyter.org",
            version="v1alpha1",
            namespace="test-namespace",
            plural="workspaces",
            name="test-space",
            body={"spec": {"desiredStatus": "Stopped"}}
        )

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch.object(HPSpace, 'space_exists')
    def test_update_not_exists(self, mock_space_exists, mock_verify_config, mock_custom_api_class):
        """Test dev space update when space doesn't exist"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_space_exists.return_value = False
        
        self.hp_space.update(desired_status="Stopped")
        
        mock_verify_config.assert_called_once()
        mock_space_exists.assert_called_once()
        # Should not call update since resource doesn't exist
        mock_custom_api.patch_namespaced_custom_object.assert_not_called()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space.handle_exception')
    @patch.object(HPSpace, 'space_exists')
    def test_update_failure(self, mock_space_exists, mock_handle_exception, mock_verify_config, mock_custom_api_class):
        """Test dev space update failure"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_space_exists.return_value = True
        mock_custom_api.patch_namespaced_custom_object.side_effect = Exception("Update failed")
        
        mock_domain_config = {"space_spec": {"spec": {}}}
        
        with patch('hyperpod_space_template.v1_0.model.SpaceConfig.to_domain', return_value=mock_domain_config):
            self.hp_space.update(desired_status="Stopped")
        
        mock_handle_exception.assert_called_once()

    @patch.object(HPSpace, 'update')
    def test_start(self, mock_update):
        """Test dev space start"""
        self.hp_space.start()
        mock_update.assert_called_once_with(desired_status="Running")

    @patch.object(HPSpace, 'update')
    def test_stop(self, mock_update):
        """Test dev space stop"""
        self.hp_space.stop()
        mock_update.assert_called_once_with(desired_status="Stopped")

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CoreV1Api')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch.object(HPSpace, 'space_exists')
    def test_list_pods_success(self, mock_space_exists, mock_verify_config, mock_core_api_class):
        """Test successful pod listing"""
        mock_core_api = Mock()
        mock_core_api_class.return_value = mock_core_api
        mock_space_exists.return_value = True
        
        mock_pod1 = Mock()
        mock_pod1.metadata.name = "pod1"
        mock_pod2 = Mock()
        mock_pod2.metadata.name = "pod2"
        
        mock_pods = Mock()
        mock_pods.items = [mock_pod1, mock_pod2]
        mock_core_api.list_namespaced_pod.return_value = mock_pods
        
        result = self.hp_space.list_pods()
        
        self.assertEqual(result, ["pod1", "pod2"])
        mock_core_api.list_namespaced_pod.assert_called_once_with(
            namespace="test-namespace",
            label_selector="sagemaker.aws.com/space-name=test-space"
        )

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CoreV1Api')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch.object(HPSpace, 'space_exists')
    def test_list_pods_not_exists(self, mock_space_exists, mock_verify_config, mock_core_api_class):
        """Test pod listing when space doesn't exist"""
        mock_core_api = Mock()
        mock_core_api_class.return_value = mock_core_api
        mock_space_exists.return_value = False
        
        result = self.hp_space.list_pods()
        
        self.assertEqual(result, [])
        mock_core_api.list_namespaced_pod.assert_not_called()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CoreV1Api')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space.handle_exception')
    @patch.object(HPSpace, 'space_exists')
    def test_list_pods_failure(self, mock_space_exists, mock_handle_exception, mock_verify_config, mock_core_api_class):
        """Test pod listing failure"""
        mock_core_api = Mock()
        mock_core_api_class.return_value = mock_core_api
        mock_space_exists.return_value = True
        mock_core_api.list_namespaced_pod.side_effect = Exception("List pods failed")
        
        self.hp_space.list_pods()
        
        mock_handle_exception.assert_called_once()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CoreV1Api')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch.object(HPSpace, 'list_pods')
    @patch.object(HPSpace, 'space_exists')
    def test_get_logs_with_pod_name(self, mock_space_exists, mock_list_pods, mock_verify_config, mock_core_api_class):
        """Test getting logs with specific pod name"""
        mock_core_api = Mock()
        mock_core_api_class.return_value = mock_core_api
        mock_space_exists.return_value = True
        mock_core_api.read_namespaced_pod_log.return_value = "test logs"
        
        result = self.hp_space.get_logs(pod_name="test-pod")
        
        self.assertEqual(result, "test logs")
        mock_core_api.read_namespaced_pod_log.assert_called_once_with(
            name="test-pod",
            namespace="test-namespace"
        )
        mock_list_pods.assert_not_called()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CoreV1Api')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch.object(HPSpace, 'list_pods')
    @patch.object(HPSpace, 'space_exists')
    def test_get_logs_without_pod_name(self, mock_space_exists, mock_list_pods, mock_verify_config, mock_core_api_class):
        """Test getting logs without pod name (uses first available pod)"""
        mock_core_api = Mock()
        mock_core_api_class.return_value = mock_core_api
        mock_space_exists.return_value = True
        mock_core_api.read_namespaced_pod_log.return_value = "test logs"
        mock_list_pods.return_value = ["pod1", "pod2"]
        
        result = self.hp_space.get_logs()
        
        self.assertEqual(result, "test logs")
        mock_core_api.read_namespaced_pod_log.assert_called_once_with(
            name="pod1",
            namespace="test-namespace"
        )

    @patch.object(HPSpace, 'verify_kube_config')
    @patch.object(HPSpace, 'list_pods')
    @patch.object(HPSpace, 'space_exists')
    def test_get_logs_no_pods(self, mock_space_exists, mock_list_pods, mock_verify_config):
        """Test getting logs when no pods are available"""
        mock_space_exists.return_value = True
        mock_list_pods.return_value = []
        
        with self.assertRaises(RuntimeError) as context:
            self.hp_space.get_logs()
        self.assertIn("No pods found for space 'test-space'", str(context.exception))

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CoreV1Api')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch.object(HPSpace, 'space_exists')
    def test_get_logs_with_container(self, mock_space_exists, mock_verify_config, mock_core_api_class):
        """Test getting logs with specific container"""
        mock_core_api = Mock()
        mock_core_api_class.return_value = mock_core_api
        mock_space_exists.return_value = True
        mock_core_api.read_namespaced_pod_log.return_value = "container logs"
        
        result = self.hp_space.get_logs(pod_name="test-pod", container="test-container")
        
        self.assertEqual(result, "container logs")
        mock_core_api.read_namespaced_pod_log.assert_called_once_with(
            name="test-pod",
            namespace="test-namespace",
            container="test-container"
        )

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CoreV1Api')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch.object(HPSpace, 'space_exists')
    def test_get_logs_not_exists(self, mock_space_exists, mock_verify_config, mock_core_api_class):
        """Test getting logs when space doesn't exist"""
        mock_core_api = Mock()
        mock_core_api_class.return_value = mock_core_api
        mock_space_exists.return_value = False
        
        result = self.hp_space.get_logs(pod_name="test-pod")
        
        self.assertEqual(result, "")
        mock_core_api.read_namespaced_pod_log.assert_not_called()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CoreV1Api')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space.handle_exception')
    @patch.object(HPSpace, 'space_exists')
    def test_get_logs_failure(self, mock_space_exists, mock_handle_exception, mock_verify_config, mock_core_api_class):
        """Test getting logs failure"""
        mock_core_api = Mock()
        mock_core_api_class.return_value = mock_core_api
        mock_space_exists.return_value = True
        mock_core_api.read_namespaced_pod_log.side_effect = Exception("Get logs failed")
        
        self.hp_space.get_logs(pod_name="test-pod")
        
        mock_handle_exception.assert_called_once()

    def test_model_validation(self):
        """Test model validation with invalid config"""
        with self.assertRaises(ValueError):
            HPSpace(config="invalid_config")

    def test_model_extra_forbid(self):
        """Test that extra fields are forbidden"""
        with self.assertRaises(ValueError):
            HPSpace(config=self.mock_config, extra_field="not_allowed")

    @patch('sagemaker.hyperpod.space.hyperpod_space.setup_logging')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch.object(HPSpace, 'space_exists')
    def test_create_debug_logging(self, mock_space_exists, mock_verify_config, mock_setup_logging):
        """Test create method with debug logging enabled"""
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        mock_space_exists.return_value = False
        
        # Mock domain config for YAML serialization
        mock_domain_config = {
            "space_spec": {
                "apiVersion": "workspace.jupyter.org/v1alpha1",
                "kind": "Workspace",
                "metadata": {"name": "test-space", "namespace": "test-namespace"},
                "spec": {"image": "test-image:latest"}
            }
        }
        
        with patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi'):
            with patch('hyperpod_space_template.v1_0.model.SpaceConfig.to_domain', return_value=mock_domain_config):
                self.hp_space.create(debug=True)
        
        mock_setup_logging.assert_called_once()

    def test_get_logger(self):
        """Test get_logger class method"""
        logger = HPSpace.get_logger()
        self.assertEqual(logger.name, "sagemaker.hyperpod.space.hyperpod_space")
