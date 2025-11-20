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
    def test_create_success(self, mock_verify_config, mock_custom_api_class):
        """Test successful space creation"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        
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
        mock_custom_api.create_namespaced_custom_object.assert_called_once()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space.handle_exception')
    def test_create_failure(self, mock_handle_exception, mock_verify_config, mock_custom_api_class):
        """Test space creation failure"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        
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

    @patch('sagemaker.hyperpod.space.hyperpod_space.boto3.client')
    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space.get_default_namespace')
    def test_list_success(self, mock_get_namespace, mock_verify_config, mock_custom_api_class, mock_boto3_client):
        """Test successful space listing"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_get_namespace.return_value = "default"
        
        # Mock STS client for caller identity
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Arn': 'arn:aws:iam::123456789012:user/test-user'}
        mock_boto3_client.return_value = mock_sts_client
        
        mock_response = {
            "items": [
                {
                    "metadata": {
                        "name": "space1", 
                        "namespace": "default",
                        "annotations": {
                            "workspace.jupyter.org/created-by": "arn:aws:iam::123456789012:user/test-user"
                        }
                    },
                    "spec": {"image": "image1:latest", "displayName": "Space 1"},
                },
                {
                    "metadata": {
                        "name": "space2", 
                        "namespace": "default",
                        "annotations": {
                            "workspace.jupyter.org/created-by": "arn:aws:iam::123456789012:user/test-user"
                        }
                    },
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

    @patch('sagemaker.hyperpod.space.hyperpod_space.boto3.client')
    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    def test_list_with_namespace(self, mock_verify_config, mock_custom_api_class, mock_boto3_client):
        """Test space listing with specific namespace"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        
        # Mock STS client for caller identity
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Arn': 'arn:aws:iam::123456789012:user/test-user'}
        mock_boto3_client.return_value = mock_sts_client
        
        mock_response = {"items": []}
        mock_custom_api.list_namespaced_custom_object.return_value = mock_response
        
        HPSpace.list(namespace="custom-namespace")
        
        mock_custom_api.list_namespaced_custom_object.assert_called_once_with(
            group="workspace.jupyter.org",
            version="v1alpha1",
            namespace="custom-namespace",
            plural="workspaces",
            _continue=None
        )


    @patch('sagemaker.hyperpod.space.hyperpod_space.boto3.client')
    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space.get_default_namespace')
    def test_list_filters_by_creator(self, mock_get_namespace, mock_verify_config, mock_custom_api_class, mock_boto3_client):
        """Test that list only returns spaces created by the caller"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_get_namespace.return_value = "default"
        
        # Mock STS client for caller identity
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Arn': 'arn:aws:iam::123456789012:user/test-user'}
        mock_boto3_client.return_value = mock_sts_client
        
        # Mock response with spaces from different creators
        mock_response = {
            "items": [
                {
                    "metadata": {
                        "name": "my-space", 
                        "namespace": "default",
                        "annotations": {
                            "workspace.jupyter.org/created-by": "arn:aws:iam::123456789012:user/test-user"
                        }
                    },
                    "spec": {"image": "image1:latest", "displayName": "My Space"},
                },
                {
                    "metadata": {
                        "name": "other-space", 
                        "namespace": "default",
                        "annotations": {
                            "workspace.jupyter.org/created-by": "arn:aws:iam::123456789012:user/other-user"
                        }
                    },
                    "spec": {"image": "image2:latest", "displayName": "Other Space"},
                },
                {
                    "metadata": {
                        "name": "no-annotation-space", 
                        "namespace": "default"
                    },
                    "spec": {"image": "image3:latest", "displayName": "No Annotation Space"},
                }
            ]
        }
        mock_custom_api.list_namespaced_custom_object.return_value = mock_response
        
        result = HPSpace.list()
        
        # Should only return the space created by the current user
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].config.name, "my-space")

    @patch('sagemaker.hyperpod.space.hyperpod_space.boto3.client')
    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space.get_default_namespace')
    def test_list_pagination_multiple_pages(self, mock_get_namespace, mock_verify_config, mock_custom_api_class, mock_boto3_client):
        """Test pagination with multiple pages"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_get_namespace.return_value = "default"
        
        # Mock STS client
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Arn': 'arn:aws:iam::123456789012:user/test-user'}
        mock_boto3_client.return_value = mock_sts_client
        
        # Mock responses for multiple pages
        first_page_response = {
            "items": [
                {
                    "metadata": {
                        "name": "space1", 
                        "namespace": "default",
                        "annotations": {
                            "workspace.jupyter.org/created-by": "arn:aws:iam::123456789012:user/test-user"
                        }
                    },
                    "spec": {"image": "image1:latest", "displayName": "Space 1"},
                }
            ],
            "metadata": {"continue": "page2-token"}
        }
        
        second_page_response = {
            "items": [
                {
                    "metadata": {
                        "name": "space2", 
                        "namespace": "default",
                        "annotations": {
                            "workspace.jupyter.org/created-by": "arn:aws:iam::123456789012:user/test-user"
                        }
                    },
                    "spec": {"image": "image2:latest", "displayName": "Space 2"},
                }
            ],
            "metadata": {}  # No continue token (last page)
        }
        
        mock_custom_api.list_namespaced_custom_object.side_effect = [first_page_response, second_page_response]
        
        result = HPSpace.list()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].config.name, "space1")
        self.assertEqual(result[1].config.name, "space2")
        
        # Should be called twice (two pages)
        self.assertEqual(mock_custom_api.list_namespaced_custom_object.call_count, 2)
        
        # Verify the calls
        calls = mock_custom_api.list_namespaced_custom_object.call_args_list
        self.assertEqual(calls[0][1]['_continue'], None)  # First call
        self.assertEqual(calls[1][1]['_continue'], "page2-token")  # Second call with token

    @patch('sagemaker.hyperpod.space.hyperpod_space.boto3.client')
    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    def test_list_no_matching_spaces_across_pages(self, mock_verify_config, mock_custom_api_class, mock_boto3_client):
        """Test pagination when no spaces match the creator filter"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        
        # Mock STS client
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Arn': 'arn:aws:iam::123456789012:user/test-user'}
        mock_boto3_client.return_value = mock_sts_client
        
        # Mock responses with no matching creators
        first_page_response = {
            "items": [
                {
                    "metadata": {
                        "name": "other-space1", 
                        "namespace": "test-namespace",
                        "annotations": {
                            "workspace.jupyter.org/created-by": "arn:aws:iam::123456789012:user/other-user"
                        }
                    },
                    "spec": {"image": "image1:latest", "displayName": "Other Space 1"},
                }
            ],
            "metadata": {"continue": "page2-token"}
        }
        
        second_page_response = {
            "items": [
                {
                    "metadata": {
                        "name": "another-space", 
                        "namespace": "test-namespace",
                        "annotations": {
                            "workspace.jupyter.org/created-by": "arn:aws:iam::123456789012:user/another-user"
                        }
                    },
                    "spec": {"image": "image2:latest", "displayName": "Another Space"},
                }
            ],
            "metadata": {}  # No continue token (last page)
        }
        
        mock_custom_api.list_namespaced_custom_object.side_effect = [first_page_response, second_page_response]
        
        result = HPSpace.list(namespace="test-namespace")
        
        # Should return empty list (no matching creators)
        self.assertEqual(len(result), 0)
        
        # Should still paginate through all pages
        self.assertEqual(mock_custom_api.list_namespaced_custom_object.call_count, 2)

    @patch('sagemaker.hyperpod.space.hyperpod_space.boto3.client')
    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space.handle_exception')
    def test_list_failure(self, mock_handle_exception, mock_verify_config, mock_custom_api_class, mock_boto3_client):
        """Test space listing failure"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_custom_api.list_namespaced_custom_object.side_effect = Exception("List failed")
        
        HPSpace.list(namespace="test-namespace")

        mock_handle_exception.assert_called_once()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    def test_get_success(self, mock_verify_config, mock_custom_api_class):
        """Test successful space retrieval"""
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
        """Test space retrieval failure"""
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
    def test_delete_success(self, mock_verify_config, mock_custom_api_class):
        """Test successful space deletion"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        
        self.hp_space.delete()
        
        mock_verify_config.assert_called_once()
        mock_custom_api.delete_namespaced_custom_object.assert_called_once_with(
            group="workspace.jupyter.org",
            version="v1alpha1",
            namespace="test-namespace",
            plural="workspaces",
            name="test-space"
        )

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space.handle_exception')
    def test_delete_failure(self, mock_handle_exception, mock_verify_config, mock_custom_api_class):
        """Test space deletion failure"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_custom_api.delete_namespaced_custom_object.side_effect = Exception("Delete failed")
        
        self.hp_space.delete()
        
        mock_handle_exception.assert_called_once()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    def test_update_success(self, mock_verify_config, mock_custom_api_class):
        """Test successful space update"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        
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
    @patch('sagemaker.hyperpod.space.hyperpod_space.handle_exception')
    def test_update_failure(self, mock_handle_exception, mock_verify_config, mock_custom_api_class):
        """Test space update failure"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_custom_api.patch_namespaced_custom_object.side_effect = Exception("Update failed")
        
        mock_domain_config = {"space_spec": {"spec": {}}}
        
        with patch('hyperpod_space_template.v1_0.model.SpaceConfig.to_domain', return_value=mock_domain_config):
            self.hp_space.update(desired_status="Stopped")
        
        mock_handle_exception.assert_called_once()

    @patch.object(HPSpace, 'update')
    def test_start(self, mock_update):
        """Test space start"""
        self.hp_space.start()
        mock_update.assert_called_once_with(desired_status="Running")

    @patch.object(HPSpace, 'update')
    def test_stop(self, mock_update):
        """Test space stop"""
        self.hp_space.stop()
        mock_update.assert_called_once_with(desired_status="Stopped")

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CoreV1Api')
    @patch.object(HPSpace, 'verify_kube_config')
    def test_list_pods_success(self, mock_verify_config, mock_core_api_class):
        """Test successful pod listing"""
        mock_core_api = Mock()
        mock_core_api_class.return_value = mock_core_api
        
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
            label_selector="workspace.jupyter.org/workspace-name=test-space"
        )

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CoreV1Api')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space.handle_exception')
    def test_list_pods_failure(self, mock_handle_exception, mock_verify_config, mock_core_api_class):
        """Test pod listing failure"""
        mock_core_api = Mock()
        mock_core_api_class.return_value = mock_core_api
        mock_core_api.list_namespaced_pod.side_effect = Exception("List pods failed")
        
        self.hp_space.list_pods()
        
        mock_handle_exception.assert_called_once()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CoreV1Api')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch.object(HPSpace, 'list_pods')
    def test_get_logs_with_pod_name(self, mock_list_pods, mock_verify_config, mock_core_api_class):
        """Test getting logs with specific pod name"""
        mock_core_api = Mock()
        mock_core_api_class.return_value = mock_core_api
        mock_core_api.read_namespaced_pod_log.return_value = "test logs"
        
        result = self.hp_space.get_logs(pod_name="test-pod")
        
        self.assertEqual(result, "test logs")
        mock_core_api.read_namespaced_pod_log.assert_called_once_with(
            name="test-pod",
            namespace="test-namespace",
            container="workspace",
        )
        mock_list_pods.assert_not_called()

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CoreV1Api')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch.object(HPSpace, 'list_pods')
    def test_get_logs_without_pod_name(self, mock_list_pods, mock_verify_config, mock_core_api_class):
        """Test getting logs without pod name (uses first available pod)"""
        mock_core_api = Mock()
        mock_core_api_class.return_value = mock_core_api
        mock_core_api.read_namespaced_pod_log.return_value = "test logs"
        mock_list_pods.return_value = ["pod1", "pod2"]
        
        result = self.hp_space.get_logs()
        
        self.assertEqual(result, "test logs")
        mock_core_api.read_namespaced_pod_log.assert_called_once_with(
            name="pod1",
            namespace="test-namespace",
            container="workspace",
        )

    @patch.object(HPSpace, 'verify_kube_config')
    @patch.object(HPSpace, 'list_pods')
    def test_get_logs_no_pods(self, mock_list_pods, mock_verify_config):
        """Test getting logs when no pods are available"""
        mock_list_pods.return_value = []
        
        with self.assertRaises(RuntimeError) as context:
            self.hp_space.get_logs()
        self.assertIn("No pods found for space 'test-space'", str(context.exception))

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CoreV1Api')
    @patch.object(HPSpace, 'verify_kube_config')
    def test_get_logs_with_container(self, mock_verify_config, mock_core_api_class):
        """Test getting logs with specific container"""
        mock_core_api = Mock()
        mock_core_api_class.return_value = mock_core_api
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
    @patch('sagemaker.hyperpod.space.hyperpod_space.handle_exception')
    def test_get_logs_failure(self, mock_handle_exception, mock_verify_config, mock_core_api_class):
        """Test getting logs failure"""
        mock_core_api = Mock()
        mock_core_api_class.return_value = mock_core_api
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
    def test_create_debug_logging(self, mock_verify_config, mock_setup_logging):
        """Test create method with debug logging enabled"""
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
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

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    def test_create_space_access_success(self, mock_verify_config, mock_custom_api_class):
        """Test successful space access creation"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        
        mock_response = {
            "status": {
                "workspaceConnectionUrl": "https://example.com/vscode-access"
            }
        }
        mock_custom_api.create_namespaced_custom_object.return_value = mock_response
        
        result = self.hp_space.create_space_access()
        
        expected_config = {
            "metadata": {
                "namespace": "test-namespace",
            },
            "spec": {
                "workspaceName": "test-space",
                "workspaceConnectionType": "vscode-remote",
            }
        }
        
        mock_verify_config.assert_called_once()
        mock_custom_api.create_namespaced_custom_object.assert_called_once_with(
            group="connection.workspace.jupyter.org",
            version="v1alpha1",
            namespace="test-namespace",
            plural="workspaceconnections",
            body=expected_config
        )
        self.assertEqual(result, {"SpaceConnectionType": "vscode-remote", "SpaceConnectionUrl": "https://example.com/vscode-access"})

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    def test_create_space_access_custom_ide(self, mock_verify_config, mock_custom_api_class):
        """Test space access creation with custom IDE type"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        
        mock_response = {
            "status": {
                "workspaceConnectionUrl": "https://example.com/webui-access"
            }
        }
        mock_custom_api.create_namespaced_custom_object.return_value = mock_response
        
        result = self.hp_space.create_space_access(connection_type="web-ui")
        
        expected_config = {
            "metadata": {
                "namespace": "test-namespace",
            },
            "spec": {
                "workspaceName": "test-space",
                "workspaceConnectionType": "web-ui",
            }
        }
        
        mock_custom_api.create_namespaced_custom_object.assert_called_once_with(
            group="connection.workspace.jupyter.org",
            version="v1alpha1",
            namespace="test-namespace",
            plural="workspaceconnections",
            body=expected_config
        )
        self.assertEqual(result, {"SpaceConnectionType": "web-ui", "SpaceConnectionUrl": "https://example.com/webui-access"})

    @patch('sagemaker.hyperpod.space.hyperpod_space.client.CustomObjectsApi')
    @patch.object(HPSpace, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space.handle_exception')
    def test_create_space_access_failure(self, mock_handle_exception, mock_verify_config, mock_custom_api_class):
        """Test space access creation failure"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_custom_api.create_namespaced_custom_object.side_effect = Exception("Access creation failed")
        
        self.hp_space.create_space_access()
        
        mock_handle_exception.assert_called_once_with(
            mock_custom_api.create_namespaced_custom_object.side_effect,
            "test-space",
            "test-namespace"
        )
