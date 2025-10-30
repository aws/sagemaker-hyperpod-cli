# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import json
import unittest
import yaml
from unittest.mock import Mock, patch, mock_open
from click.testing import CliRunner

from sagemaker.hyperpod.cli.commands.space_template import (
    space_template_create,
    space_template_list,
    space_template_describe,
    space_template_delete,
    space_template_update,
)


class TestSpaceTemplateCommands(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.mock_config_data = {
            "apiVersion": "workspace.jupyter.org/v1alpha1",
            "kind": "WorkspaceTemplate",
            "metadata": {"name": "test-template"},
            "spec": {"displayName": "Test Template"}
        }

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    @patch("builtins.open", new_callable=mock_open, read_data="test: data")
    @patch("yaml.safe_load")
    def test_space_template_create_success(self, mock_yaml_load, mock_file, mock_k8s_client):
        """Test successful space template creation"""
        mock_yaml_load.return_value = self.mock_config_data
        mock_client_instance = Mock()
        mock_k8s_client.return_value = mock_client_instance
        
        result = self.runner.invoke(space_template_create, ["--file", "test.yaml"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Space template 'test-template' created successfully", result.output)
        mock_client_instance.create_space_template.assert_called_once_with(self.mock_config_data)

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    def test_space_template_create_file_not_found(self, mock_k8s_client):
        """Test space template creation with missing file"""
        result = self.runner.invoke(space_template_create, ["--file", "nonexistent.yaml"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Error: File 'nonexistent.yaml' not found", result.output)

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    @patch("builtins.open", new_callable=mock_open, read_data="invalid: yaml: content:")
    @patch("yaml.safe_load")
    def test_space_template_create_yaml_error(self, mock_yaml_load, mock_file, mock_k8s_client):
        """Test space template creation with YAML parsing error"""
        mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")
        
        result = self.runner.invoke(space_template_create, ["--file", "test.yaml"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Error parsing YAML file: Invalid YAML", result.output)

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    @patch("builtins.open", new_callable=mock_open, read_data="test: data")
    @patch("yaml.safe_load")
    def test_space_template_create_k8s_error(self, mock_yaml_load, mock_file, mock_k8s_client):
        """Test space template creation with Kubernetes error"""
        mock_yaml_load.return_value = self.mock_config_data
        mock_client_instance = Mock()
        mock_k8s_client.return_value = mock_client_instance
        mock_client_instance.create_space_template.side_effect = Exception("K8s error")
        
        result = self.runner.invoke(space_template_create, ["--file", "test.yaml"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Error creating space template: K8s error", result.output)

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    def test_space_template_list_table_output(self, mock_k8s_client):
        """Test space template list with table output"""
        mock_client_instance = Mock()
        mock_k8s_client.return_value = mock_client_instance
        mock_client_instance.list_space_templates.return_value = {
            "items": [
                {"metadata": {"name": "template1"}},
                {"metadata": {"name": "template2"}}
            ]
        }
        
        result = self.runner.invoke(space_template_list, ["--output", "table"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("template1", result.output)
        self.assertIn("template2", result.output)
        self.assertIn("NAME", result.output)

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    def test_space_template_list_json_output(self, mock_k8s_client):
        """Test space template list with JSON output"""
        mock_client_instance = Mock()
        mock_k8s_client.return_value = mock_client_instance
        mock_resources = {
            "items": [
                {"metadata": {"name": "template1"}},
                {"metadata": {"name": "template2"}}
            ]
        }
        mock_client_instance.list_space_templates.return_value = mock_resources
        
        result = self.runner.invoke(space_template_list, ["--output", "json"])
        
        self.assertEqual(result.exit_code, 0)
        output_json = json.loads(result.output)
        self.assertEqual(output_json, mock_resources)

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    def test_space_template_list_empty(self, mock_k8s_client):
        """Test space template list with no templates"""
        mock_client_instance = Mock()
        mock_k8s_client.return_value = mock_client_instance
        mock_client_instance.list_space_templates.return_value = {"items": []}
        
        result = self.runner.invoke(space_template_list, ["--output", "table"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("No space templates found", result.output)

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    def test_space_template_list_error(self, mock_k8s_client):
        """Test space template list with error"""
        mock_client_instance = Mock()
        mock_k8s_client.return_value = mock_client_instance
        mock_client_instance.list_space_templates.side_effect = Exception("List error")
        
        result = self.runner.invoke(space_template_list)
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Error listing space templates: List error", result.output)

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    def test_space_template_describe_yaml_output(self, mock_k8s_client):
        """Test space template describe with YAML output"""
        mock_client_instance = Mock()
        mock_k8s_client.return_value = mock_client_instance
        mock_resource = {
            "metadata": {
                "name": "test-template",
                "managedFields": [{"manager": "kubectl"}]
            },
            "spec": {"displayName": "Test Template"}
        }
        mock_client_instance.get_space_template.return_value = mock_resource
        
        result = self.runner.invoke(space_template_describe, ["--name", "test-template", "--output", "yaml"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("name: test-template", result.output)
        self.assertIn("displayName: Test Template", result.output)
        # managedFields should be removed
        self.assertNotIn("managedFields", result.output)

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    def test_space_template_describe_json_output(self, mock_k8s_client):
        """Test space template describe with JSON output"""
        mock_client_instance = Mock()
        mock_k8s_client.return_value = mock_client_instance
        mock_resource = {
            "metadata": {
                "name": "test-template",
                "managedFields": [{"manager": "kubectl"}]
            },
            "spec": {"displayName": "Test Template"}
        }
        mock_client_instance.get_space_template.return_value = mock_resource
        
        result = self.runner.invoke(space_template_describe, ["--name", "test-template", "--output", "json"])
        
        self.assertEqual(result.exit_code, 0)
        output_json = json.loads(result.output)
        self.assertEqual(output_json["metadata"]["name"], "test-template")
        self.assertNotIn("managedFields", output_json["metadata"])

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    def test_space_template_describe_error(self, mock_k8s_client):
        """Test space template describe with error"""
        mock_client_instance = Mock()
        mock_k8s_client.return_value = mock_client_instance
        mock_client_instance.get_space_template.side_effect = Exception("Not found")
        
        result = self.runner.invoke(space_template_describe, ["--name", "nonexistent"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Error describing space template 'nonexistent': Not found", result.output)

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    def test_space_template_delete_success(self, mock_k8s_client):
        """Test successful space template deletion"""
        mock_client_instance = Mock()
        mock_k8s_client.return_value = mock_client_instance
        
        result = self.runner.invoke(space_template_delete, ["--name", "test-template"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Space template 'test-template' deleted successfully", result.output)
        mock_client_instance.delete_space_template.assert_called_once_with("test-template")

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    def test_space_template_delete_error(self, mock_k8s_client):
        """Test space template deletion with error"""
        mock_client_instance = Mock()
        mock_k8s_client.return_value = mock_client_instance
        mock_client_instance.delete_space_template.side_effect = Exception("Delete error")
        
        result = self.runner.invoke(space_template_delete, ["--name", "test-template"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Error deleting space template 'test-template': Delete error", result.output)

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    @patch("builtins.open", new_callable=mock_open, read_data="test: data")
    @patch("yaml.safe_load")
    def test_space_template_update_success(self, mock_yaml_load, mock_file, mock_k8s_client):
        """Test successful space template update"""
        mock_yaml_load.return_value = self.mock_config_data
        mock_client_instance = Mock()
        mock_k8s_client.return_value = mock_client_instance
        
        result = self.runner.invoke(space_template_update, ["--name", "test-template", "--file", "test.yaml"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Space template 'test-template' updated successfully", result.output)
        mock_client_instance.patch_space_template.assert_called_once()

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    @patch("builtins.open", new_callable=mock_open, read_data="test: data")
    @patch("yaml.safe_load")
    def test_space_template_update_name_mismatch(self, mock_yaml_load, mock_file, mock_k8s_client):
        """Test space template update with name mismatch"""
        config_with_different_name = self.mock_config_data.copy()
        config_with_different_name["metadata"]["name"] = "different-name"
        mock_yaml_load.return_value = config_with_different_name
        mock_client_instance = Mock()
        mock_k8s_client.return_value = mock_client_instance
        
        result = self.runner.invoke(space_template_update, ["--name", "test-template", "--file", "test.yaml"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Error: Name mismatch. CLI parameter 'test-template' does not match YAML name 'different-name'", result.output)
        mock_client_instance.patch_space_template.assert_not_called()

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    def test_space_template_update_file_not_found(self, mock_k8s_client):
        """Test space template update with missing file"""
        result = self.runner.invoke(space_template_update, ["--name", "test-template", "--file", "nonexistent.yaml"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Error: File 'nonexistent.yaml' not found", result.output)

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    @patch("builtins.open", new_callable=mock_open, read_data="invalid: yaml: content:")
    @patch("yaml.safe_load")
    def test_space_template_update_yaml_error(self, mock_yaml_load, mock_file, mock_k8s_client):
        """Test space template update with YAML parsing error"""
        mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")
        
        result = self.runner.invoke(space_template_update, ["--name", "test-template", "--file", "test.yaml"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Error parsing YAML file: Invalid YAML", result.output)

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    @patch("builtins.open", new_callable=mock_open, read_data="test: data")
    @patch("yaml.safe_load")
    def test_space_template_update_k8s_error(self, mock_yaml_load, mock_file, mock_k8s_client):
        """Test space template update with Kubernetes error"""
        mock_yaml_load.return_value = self.mock_config_data
        mock_client_instance = Mock()
        mock_k8s_client.return_value = mock_client_instance
        mock_client_instance.patch_space_template.side_effect = Exception("K8s error")
        
        result = self.runner.invoke(space_template_update, ["--name", "test-template", "--file", "test.yaml"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Error updating space template 'test-template': K8s error", result.output)

    @patch("sagemaker.hyperpod.cli.commands.space_template.KubernetesClient")
    @patch("builtins.open", new_callable=mock_open, read_data="test: data")
    @patch("yaml.safe_load")
    def test_space_template_update_removes_immutable_fields(self, mock_yaml_load, mock_file, mock_k8s_client):
        """Test space template update removes immutable fields"""
        config_with_immutable_fields = {
            "metadata": {
                "name": "test-template",
                "resourceVersion": "12345",
                "uid": "abc-123",
                "creationTimestamp": "2023-01-01T00:00:00Z",
                "managedFields": [{"manager": "kubectl"}]
            },
            "spec": {"displayName": "Test Template"}
        }
        mock_yaml_load.return_value = config_with_immutable_fields
        mock_client_instance = Mock()
        mock_k8s_client.return_value = mock_client_instance
        
        result = self.runner.invoke(space_template_update, ["--name", "test-template", "--file", "test.yaml"])
        
        self.assertEqual(result.exit_code, 0)
        # Verify patch was called with cleaned config
        call_args = mock_client_instance.patch_space_template.call_args[0][1]
        self.assertNotIn("resourceVersion", call_args["metadata"])
        self.assertNotIn("uid", call_args["metadata"])
        self.assertNotIn("creationTimestamp", call_args["metadata"])
        self.assertNotIn("managedFields", call_args["metadata"])
        self.assertEqual(call_args["metadata"]["name"], "test-template")


if __name__ == "__main__":
    unittest.main()
