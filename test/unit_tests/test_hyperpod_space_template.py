import unittest
from unittest.mock import Mock, patch, mock_open
import yaml
from kubernetes.client.rest import ApiException

from sagemaker.hyperpod.space.hyperpod_space_template import HPSpaceTemplate


class TestHPSpaceTemplate(unittest.TestCase):
    """Test cases for HPSpaceTemplate PySDK"""

    def setUp(self):
        """Setup test fixtures"""
        self.mock_config_data = {
            "apiVersion": "workspace.jupyter.org/v1alpha1",
            "kind": "WorkspaceTemplate",
            "metadata": {
                "name": "test-template",
                "namespace": "test-namespace"
            },
            "spec": {
                "displayName": "Test Template",
                "description": "Test space template"
            }
        }
        self.yaml_content = yaml.dump(self.mock_config_data)

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_init_success(self, mock_yaml_load, mock_file):
        """Test successful initialization"""
        mock_yaml_load.return_value = self.mock_config_data
        mock_file.return_value.read.return_value = self.yaml_content
        
        template = HPSpaceTemplate(file_path="test.yaml")
        
        self.assertEqual(template.config_data, self.mock_config_data)
        self.assertEqual(template.name, "test-template")
        mock_file.assert_called_once_with("test.yaml", 'r')

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_init_file_not_found(self, mock_file):
        """Test initialization with non-existent file"""
        with self.assertRaises(FileNotFoundError) as context:
            HPSpaceTemplate(file_path="nonexistent.yaml")
        self.assertIn("File 'nonexistent.yaml' not found", str(context.exception))

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load', side_effect=yaml.YAMLError("Invalid YAML"))
    def test_init_yaml_error(self, mock_yaml_load, mock_file):
        """Test initialization with invalid YAML"""
        with self.assertRaises(ValueError) as context:
            HPSpaceTemplate(file_path="invalid.yaml")
        self.assertIn("Error parsing YAML file", str(context.exception))

    @patch('sagemaker.hyperpod.space.hyperpod_space_template.config.load_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.verify_kubernetes_version_compatibility')
    def test_verify_kube_config_success(self, mock_verify_k8s, mock_load_config):
        """Test successful kubeconfig verification"""
        HPSpaceTemplate.is_kubeconfig_loaded = False
        HPSpaceTemplate.verify_kube_config()
        
        mock_load_config.assert_called_once()
        mock_verify_k8s.assert_called_once()
        self.assertTrue(HPSpaceTemplate.is_kubeconfig_loaded)

    def test_verify_kube_config_already_loaded(self):
        """Test kubeconfig verification when already loaded"""
        HPSpaceTemplate.is_kubeconfig_loaded = True
        
        with patch('sagemaker.hyperpod.space.hyperpod_space_template.config.load_kube_config') as mock_load_config:
            HPSpaceTemplate.verify_kube_config()
            mock_load_config.assert_not_called()

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.client.CustomObjectsApi')
    @patch.object(HPSpaceTemplate, 'verify_kube_config')
    def test_create_success(self, mock_verify_config, mock_custom_api_class, mock_yaml_load, mock_file):
        """Test successful space template creation"""
        mock_yaml_load.return_value = self.mock_config_data
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_custom_api.create_namespaced_custom_object.return_value = self.mock_config_data
        
        template = HPSpaceTemplate(file_path="test.yaml")
        template.create()
        
        mock_verify_config.assert_called_once()
        mock_custom_api.create_namespaced_custom_object.assert_called_once_with(
            group="workspace.jupyter.org",
            version="v1alpha1",
            namespace="test-namespace",
            plural="workspacetemplates",
            body=self.mock_config_data
        )

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.client.CustomObjectsApi')
    @patch.object(HPSpaceTemplate, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.handle_exception')
    def test_create_api_exception(self, mock_handle_exception, mock_verify_config, mock_custom_api_class, mock_yaml_load, mock_file):
        """Test space template creation with API exception"""
        mock_yaml_load.return_value = self.mock_config_data
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_custom_api.create_namespaced_custom_object.side_effect = ApiException(status=409)
        
        template = HPSpaceTemplate(file_path="test.yaml")
        template.create()
        
        mock_handle_exception.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.client.CustomObjectsApi')
    @patch.object(HPSpaceTemplate, 'verify_kube_config')
    def test_create_general_exception(self, mock_verify_config, mock_custom_api_class, mock_yaml_load, mock_file):
        """Test space template creation with general exception"""
        mock_yaml_load.return_value = self.mock_config_data
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_custom_api.create_namespaced_custom_object.side_effect = Exception("Creation failed")
        
        template = HPSpaceTemplate(file_path="test.yaml")
        
        with self.assertRaises(Exception):
            template.create()

    @patch('sagemaker.hyperpod.space.hyperpod_space_template.client.CustomObjectsApi')
    @patch.object(HPSpaceTemplate, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.get_default_namespace')
    def test_list_success(self, mock_get_namespace, mock_verify_config, mock_custom_api_class):
        """Test successful space template listing"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_get_namespace.return_value = "default"
        
        mock_response = {
            "items": [
                {
                    "metadata": {"name": "template1", "namespace": "default"},
                    "spec": {"displayName": "Template 1"}
                },
                {
                    "metadata": {"name": "template2", "namespace": "default"},
                    "spec": {"displayName": "Template 2"}
                }
            ]
        }
        mock_custom_api.list_namespaced_custom_object.return_value = mock_response
        
        with patch('builtins.open', new_callable=mock_open), \
             patch('yaml.safe_load', return_value=mock_response["items"][0]):
            result = HPSpaceTemplate.list()
        
        self.assertEqual(len(result), 2)
        mock_custom_api.list_namespaced_custom_object.assert_called_once_with(
            group="workspace.jupyter.org",
            version="v1alpha1",
            namespace="default",
            plural="workspacetemplates"
        )

    @patch('sagemaker.hyperpod.space.hyperpod_space_template.client.CustomObjectsApi')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.HPSpaceTemplate.verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.handle_exception')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.get_default_namespace')
    def test_list_api_exception(self, mock_get_namespace, mock_handle_exception, mock_verify_config, mock_custom_api_class):
        """Test space template listing with API exception"""
        mock_get_namespace.return_value = "default"
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_custom_api.list_namespaced_custom_object.side_effect = ApiException(status=500)
        
        HPSpaceTemplate.list()
        
        mock_handle_exception.assert_called_once()

    @patch('sagemaker.hyperpod.space.hyperpod_space_template.client.CustomObjectsApi')
    @patch.object(HPSpaceTemplate, 'verify_kube_config')
    def test_list_general_exception(self, mock_verify_config, mock_custom_api_class):
        """Test space template listing with general exception"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_custom_api.list_namespaced_custom_object.side_effect = Exception("List failed")
        
        with self.assertRaises(Exception):
            HPSpaceTemplate.list()

    @patch('sagemaker.hyperpod.space.hyperpod_space_template.client.CustomObjectsApi')
    @patch.object(HPSpaceTemplate, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.get_default_namespace')
    def test_get_success(self, mock_get_namespace, mock_verify_config, mock_custom_api_class):
        """Test successful space template retrieval"""
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_get_namespace.return_value = "default"
        
        mock_response = {
            "metadata": {
                "name": "test-template",
                "namespace": "test-namespace",
                "managedFields": [{"manager": "test"}]
            },
            "spec": {"displayName": "Test Template"}
        }
        expected_response = {
            "metadata": {"name": "test-template"},
            "spec": {"displayName": "Test Template"}
        }
        mock_custom_api.get_namespaced_custom_object.return_value = mock_response
        
        with patch('builtins.open', new_callable=mock_open), \
             patch('yaml.safe_load', return_value=expected_response):
            result = HPSpaceTemplate.get("test-template")
        
        mock_custom_api.get_namespaced_custom_object.assert_called_once_with(
            group="workspace.jupyter.org",
            version="v1alpha1",
            namespace="default",
            plural="workspacetemplates",
            name="test-template"
        )

    @patch('sagemaker.hyperpod.space.hyperpod_space_template.client.CustomObjectsApi')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.HPSpaceTemplate.verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.handle_exception')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.get_default_namespace')
    def test_get_api_exception(self, mock_get_namespace, mock_handle_exception, mock_verify_config, mock_custom_api_class):
        """Test space template retrieval with API exception"""
        mock_get_namespace.return_value = "default"
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_custom_api.get_namespaced_custom_object.side_effect = ApiException(status=404)
        
        HPSpaceTemplate.get("nonexistent-template")
        
        mock_handle_exception.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.client.CustomObjectsApi')
    @patch.object(HPSpaceTemplate, 'verify_kube_config')
    def test_delete_success(self, mock_verify_config, mock_custom_api_class, mock_yaml_load, mock_file):
        """Test successful space template deletion"""
        mock_yaml_load.return_value = self.mock_config_data
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        
        template = HPSpaceTemplate(file_path="test.yaml")
        template.delete()
        
        mock_verify_config.assert_called_once()
        mock_custom_api.delete_namespaced_custom_object.assert_called_once_with(
            group="workspace.jupyter.org",
            version="v1alpha1",
            namespace="test-namespace",
            plural="workspacetemplates",
            name="test-template"
        )

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.client.CustomObjectsApi')
    @patch.object(HPSpaceTemplate, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.handle_exception')
    def test_delete_api_exception(self, mock_handle_exception, mock_verify_config, mock_custom_api_class, mock_yaml_load, mock_file):
        """Test space template deletion with API exception"""
        mock_yaml_load.return_value = self.mock_config_data
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_custom_api.delete_namespaced_custom_object.side_effect = ApiException(status=404)
        
        template = HPSpaceTemplate(file_path="test.yaml")
        template.delete()
        
        mock_handle_exception.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.client.CustomObjectsApi')
    @patch.object(HPSpaceTemplate, 'verify_kube_config')
    def test_update_success(self, mock_verify_config, mock_custom_api_class, mock_yaml_load, mock_file):
        """Test successful space template update"""
        mock_yaml_load.side_effect = [self.mock_config_data, self.mock_config_data]
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_custom_api.patch_namespaced_custom_object.return_value = self.mock_config_data
        
        template = HPSpaceTemplate(file_path="test.yaml")
        template.update("updated.yaml")
        
        mock_verify_config.assert_called_once()
        mock_custom_api.patch_namespaced_custom_object.assert_called_once_with(
            group="workspace.jupyter.org",
            version="v1alpha1",
            namespace="test-namespace",
            plural="workspacetemplates",
            name="test-template",
            body=self.mock_config_data
        )

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch.object(HPSpaceTemplate, 'verify_kube_config')
    def test_update_name_mismatch(self, mock_verify_config, mock_yaml_load, mock_file):
        """Test space template update with name mismatch"""
        mock_yaml_load.side_effect = [
            self.mock_config_data,
            {"metadata": {"name": "different-name"}}
        ]
        
        template = HPSpaceTemplate(file_path="test.yaml")
        
        with self.assertRaises(ValueError) as context:
            template.update("different.yaml")
        self.assertIn("Name mismatch", str(context.exception))

    @patch('builtins.open')
    @patch('yaml.safe_load')
    @patch.object(HPSpaceTemplate, 'verify_kube_config')
    def test_update_file_not_found(self, mock_verify_config, mock_yaml_load, mock_file):
        """Test space template update with non-existent file"""
        mock_yaml_load.return_value = self.mock_config_data
        mock_file.side_effect = [mock_open().return_value, FileNotFoundError("File 'nonexistent.yaml' not found")]
        
        template = HPSpaceTemplate(file_path="test.yaml")
        
        with self.assertRaises(FileNotFoundError) as context:
            template.update("nonexistent.yaml")
        self.assertIn("File 'nonexistent.yaml' not found", str(context.exception))

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch.object(HPSpaceTemplate, 'verify_kube_config')
    def test_update_yaml_error(self, mock_verify_config, mock_yaml_load, mock_file):
        """Test space template update with YAML error"""
        mock_yaml_load.side_effect = [self.mock_config_data, yaml.YAMLError("Invalid YAML")]
        
        template = HPSpaceTemplate(file_path="test.yaml")
        
        with self.assertRaises(ValueError) as context:
            template.update("invalid.yaml")
        self.assertIn("Error parsing YAML file", str(context.exception))

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.client.CustomObjectsApi')
    @patch.object(HPSpaceTemplate, 'verify_kube_config')
    @patch('sagemaker.hyperpod.space.hyperpod_space_template.handle_exception')
    def test_update_api_exception(self, mock_handle_exception, mock_verify_config, mock_custom_api_class, mock_yaml_load, mock_file):
        """Test space template update with API exception"""
        mock_yaml_load.side_effect = [self.mock_config_data, self.mock_config_data]
        mock_custom_api = Mock()
        mock_custom_api_class.return_value = mock_custom_api
        mock_custom_api.patch_namespaced_custom_object.side_effect = ApiException(status=404)
        
        template = HPSpaceTemplate(file_path="test.yaml")
        template.update("updated.yaml")
        
        mock_handle_exception.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_to_yaml(self, mock_yaml_load, mock_file):
        """Test converting space template to YAML"""
        mock_yaml_load.return_value = self.mock_config_data
        
        template = HPSpaceTemplate(file_path="test.yaml")
        result = template.to_yaml()
        
        self.assertIsInstance(result, str)
        self.assertIn("test-template", result)

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_to_dict(self, mock_yaml_load, mock_file):
        """Test converting space template to dictionary"""
        mock_yaml_load.return_value = self.mock_config_data
        
        template = HPSpaceTemplate(file_path="test.yaml")
        result = template.to_dict()
        
        self.assertEqual(result, self.mock_config_data)
