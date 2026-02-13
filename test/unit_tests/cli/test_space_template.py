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

    @patch("sagemaker.hyperpod.cli.commands.space_template.HPSpaceTemplate")
    def test_space_template_create_success(self, mock_hp_space_template):
        """Test successful space template creation"""
        mock_template_instance = Mock()
        mock_template_instance.name = "test-template"
        mock_template_instance.namespace = "default"
        mock_hp_space_template.return_value = mock_template_instance
        
        result = self.runner.invoke(space_template_create, ["--file", "test.yaml"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Space template 'test-template' in namespace 'default' created successfully", result.output)
        mock_hp_space_template.assert_called_once_with(file_path="test.yaml")
        mock_template_instance.create.assert_called_once()

    @patch("sagemaker.hyperpod.cli.commands.space_template.HPSpaceTemplate")
    def test_space_template_list_table_output(self, mock_hp_space_template):
        """Test space template list with table output"""
        mock_template1 = Mock()
        mock_template1.name = "template1"
        mock_template1.namespace = "default"
        mock_template1.config_data = {"spec": {"displayName": "Template 1", "defaultImage": "image1"}}
        mock_template2 = Mock()
        mock_template2.name = "template2"
        mock_template2.namespace = "test"
        mock_template2.config_data = {"spec": {"displayName": "Template 2", "defaultImage": "image2"}}
        mock_hp_space_template.list.return_value = [mock_template1, mock_template2]
        
        result = self.runner.invoke(space_template_list, ["--output", "table"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("template1", result.output)
        self.assertIn("template2", result.output)
        self.assertIn("NAMESPACE", result.output)
        self.assertIn("NAME", result.output)
        mock_hp_space_template.list.assert_called_once_with(None)

    @patch("sagemaker.hyperpod.cli.commands.space_template.HPSpaceTemplate")
    def test_space_template_list_json_output(self, mock_hp_space_template):
        """Test space template list with JSON output"""
        mock_template1 = Mock()
        mock_template1.to_dict.return_value = {"metadata": {"name": "template1"}}
        mock_template2 = Mock()
        mock_template2.to_dict.return_value = {"metadata": {"name": "template2"}}
        mock_hp_space_template.list.return_value = [mock_template1, mock_template2]
        
        result = self.runner.invoke(space_template_list, ["--output", "json"])
        
        self.assertEqual(result.exit_code, 0)
        output_json = json.loads(result.output)
        self.assertEqual(len(output_json), 2)
        self.assertEqual(output_json[0]["metadata"]["name"], "template1")
        self.assertEqual(output_json[1]["metadata"]["name"], "template2")
        mock_hp_space_template.list.assert_called_once_with(None)

    @patch("sagemaker.hyperpod.cli.commands.space_template.HPSpaceTemplate")
    def test_space_template_list_empty(self, mock_hp_space_template):
        """Test space template list with no templates"""
        mock_hp_space_template.list.return_value = []
        
        result = self.runner.invoke(space_template_list, ["--output", "table"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("No space templates found", result.output)
        mock_hp_space_template.list.assert_called_once_with(None)

    @patch("sagemaker.hyperpod.common.cli_decorators._namespace_exists")
    @patch("sagemaker.hyperpod.cli.commands.space_template.HPSpaceTemplate")
    def test_space_template_list_with_namespace(self, mock_hp_space_template, mock_namespace_exists):
        """Test space template list with namespace parameter"""
        mock_namespace_exists.return_value = True
        mock_template1 = Mock()
        mock_template1.name = "template1"
        mock_template1.namespace = "test-namespace"
        mock_template1.config_data = {"spec": {"displayName": "Template 1", "defaultImage": "image1"}}
        mock_hp_space_template.list.return_value = [mock_template1]

        result = self.runner.invoke(space_template_list, ["--namespace", "test-namespace", "--output", "table"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("template1", result.output)
        self.assertIn("test-namespace", result.output)
        mock_hp_space_template.list.assert_called_once_with("test-namespace")

    @patch("sagemaker.hyperpod.cli.commands.space_template.HPSpaceTemplate")
    def test_space_template_describe_yaml_output(self, mock_hp_space_template):
        """Test space template describe with YAML output"""
        mock_template_instance = Mock()
        mock_template_instance.to_yaml.return_value = "name: test-template\nspec:\n  displayName: Test Template"
        mock_hp_space_template.get.return_value = mock_template_instance
        
        result = self.runner.invoke(space_template_describe, ["--name", "test-template", "--output", "yaml"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("name: test-template", result.output)
        self.assertIn("displayName: Test Template", result.output)
        mock_hp_space_template.get.assert_called_once_with("test-template", None)

    @patch("sagemaker.hyperpod.cli.commands.space_template.HPSpaceTemplate")
    def test_space_template_describe_json_output(self, mock_hp_space_template):
        """Test space template describe with JSON output"""
        mock_template_instance = Mock()
        mock_template_instance.to_dict.return_value = {
            "metadata": {"name": "test-template"},
            "spec": {"displayName": "Test Template"}
        }
        mock_hp_space_template.get.return_value = mock_template_instance
        
        result = self.runner.invoke(space_template_describe, ["--name", "test-template", "--output", "json"])
        
        self.assertEqual(result.exit_code, 0)
        output_json = json.loads(result.output)
        self.assertEqual(output_json["metadata"]["name"], "test-template")
        self.assertEqual(output_json["spec"]["displayName"], "Test Template")
        mock_hp_space_template.get.assert_called_once_with("test-template", None)

    @patch("sagemaker.hyperpod.cli.commands.space_template.HPSpaceTemplate")
    def test_space_template_delete_success(self, mock_hp_space_template):
        """Test successful space template deletion"""
        mock_template_instance = Mock()
        mock_hp_space_template.get.return_value = mock_template_instance
        
        result = self.runner.invoke(space_template_delete, ["--name", "test-template"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Requested deletion for Space template 'test-template' in namespace 'None'", result.output)
        mock_hp_space_template.get.assert_called_once_with("test-template", None)
        mock_template_instance.delete.assert_called_once()

    @patch("sagemaker.hyperpod.cli.commands.space_template.HPSpaceTemplate")
    def test_space_template_update_success(self, mock_hp_space_template):
        """Test successful space template update"""
        mock_template_instance = Mock()
        mock_hp_space_template.get.return_value = mock_template_instance
        
        result = self.runner.invoke(space_template_update, ["--name", "test-template", "--file", "test.yaml"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Space template 'test-template' in namespace 'None' updated successfully", result.output)
        mock_hp_space_template.get.assert_called_once_with("test-template", None)
        mock_template_instance.update.assert_called_once_with("test.yaml")
