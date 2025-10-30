import pytest
import json
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock

from sagemaker.hyperpod.cli.commands.space import (
    space_create,
    space_list,
    space_describe,
    space_delete,
    space_update,
    space_start,
    space_stop,
    space_get_logs,
)


class TestSpaceCommands:
    """Test cases for space commands"""

    def setup_method(self):
        self.runner = CliRunner()
        self.mock_k8s_client = Mock()

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_create_success(self, mock_k8s_client_class, mock_load_schema):
        """Test successful space creation"""
        # Mock schema loading
        mock_load_schema.return_value = {
            "properties": {
                "name": {"type": "string"},
                "display_name": {"type": "string"},
                "namespace": {"type": "string"}
            },
            "required": ["name", "display_name"]
        }

        # Mock model registry
        mock_model = Mock()
        mock_model.return_value = Mock()
        mock_model.return_value.to_domain.return_value = {
            "name": "test-space",
            "display_name": "Test Space",
            "namespace": "test-ns",
            "space_spec": {"spec": {"image": "test-image"}}
        }

        # Mock KubernetesClient
        mock_k8s_instance = Mock()
        mock_k8s_client_class.return_value = mock_k8s_instance

        with patch('hyperpod_space_template.registry.SCHEMA_REGISTRY', {'1.0': mock_model}):
            result = self.runner.invoke(space_create, [
                '--version', '1.0',
                '--name', 'test-space',
                '--display-name', 'Test Space',
                '--namespace', 'test-ns'
            ])

        assert result.exit_code == 0
        assert "Space 'test-space' created successfully" in result.output
        mock_k8s_instance.create_space.assert_called_once()

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
    def test_space_create_missing_required_args(self, mock_load_schema):
        """Test space creation with missing required arguments"""
        mock_load_schema.return_value = {
            "properties": {"name": {"type": "string"}},
            "required": ["name"]
        }

        result = self.runner.invoke(space_create, ['--version', '1.0'])
        assert result.exit_code != 0
        assert 'Missing option' in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_create_k8s_error(self, mock_k8s_client_class):
        """Test space creation error handling"""
        mock_k8s_instance = Mock()
        mock_k8s_instance.create_space.side_effect = Exception("Creation failed")
        mock_k8s_client_class.return_value = mock_k8s_instance

        mock_model = Mock()
        mock_model.return_value = Mock()
        mock_model.return_value.to_domain.return_value = {
            "name": "test-space",
            "display_name": "Test Space",
            "namespace": "test-ns",
            "space_spec": {}
        }

        with patch('hyperpod_space_template.registry.SCHEMA_REGISTRY', {'1.0': mock_model}):
            with patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version') as mock_load_schema:
                mock_load_schema.return_value = {
                    "properties": {
                        "name": {"type": "string"},
                        "display_name": {"type": "string"},
                        "namespace": {"type": "string"}
                    },
                    "required": ["name", "display_name"]
                }
                result = self.runner.invoke(space_create, [
                    '--version', '1.0',
                    '--name', 'test-space',
                    '--display-name', 'Test Space',
                    '--namespace', 'test-ns'
                ])

        assert result.exit_code == 0
        assert "Error creating space: Creation failed" in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_list_table_output(self, mock_k8s_client_class):
        """Test space list with table output"""
        mock_k8s_instance = Mock()
        mock_k8s_instance.list_spaces.return_value = {
            "items": [
                {
                    "metadata": {"name": "space1", "namespace": "ns1"},
                    "status": {"phase": "Running"}
                },
                {
                    "metadata": {"name": "space2", "namespace": "ns2"},
                    "status": {"phase": "Stopped"}
                }
            ]
        }
        mock_k8s_client_class.return_value = mock_k8s_instance

        result = self.runner.invoke(space_list, [
            '--namespace', 'test-ns',
            '--output', 'table'
        ])

        assert result.exit_code == 0
        assert "space1" in result.output
        assert "space2" in result.output
        mock_k8s_instance.list_spaces.assert_called_once_with('test-ns')

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_list_json_output(self, mock_k8s_client_class):
        """Test space list with JSON output"""
        mock_resources = {
            "items": [
                {"metadata": {"name": "space1", "namespace": "ns1"}}
            ]
        }
        mock_k8s_instance = Mock()
        mock_k8s_instance.list_spaces.return_value = mock_resources
        mock_k8s_client_class.return_value = mock_k8s_instance

        result = self.runner.invoke(space_list, [
            '--namespace', 'test-ns',
            '--output', 'json'
        ])

        assert result.exit_code == 0
        output_json = json.loads(result.output)
        assert output_json == mock_resources

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_list_empty(self, mock_k8s_client_class):
        """Test space list with no items"""
        mock_k8s_instance = Mock()
        mock_k8s_instance.list_spaces.return_value = {"items": []}
        mock_k8s_client_class.return_value = mock_k8s_instance

        result = self.runner.invoke(space_list, [
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "No spaces found" in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_list_error(self, mock_k8s_client_class):
        """Test space list error handling"""
        mock_k8s_instance = Mock()
        mock_k8s_instance.list_spaces.side_effect = Exception("List failed")
        mock_k8s_client_class.return_value = mock_k8s_instance

        result = self.runner.invoke(space_list, [
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Error listing spaces: List failed" in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_describe_yaml_output(self, mock_k8s_client_class):
        """Test space describe with YAML output"""
        mock_resource = {"metadata": {"name": "test-space"}}
        mock_k8s_instance = Mock()
        mock_k8s_instance.get_space.return_value = mock_resource
        mock_k8s_client_class.return_value = mock_k8s_instance

        with patch('yaml.dump') as mock_yaml_dump:
            mock_yaml_dump.return_value = "yaml_output"
            result = self.runner.invoke(space_describe, [
                '--name', 'test-space',
                '--namespace', 'test-ns',
            ])

        assert result.exit_code == 0
        assert "yaml_output" in result.output
        mock_k8s_instance.get_space.assert_called_once_with('test-ns', 'test-space')

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_describe_json_output(self, mock_k8s_client_class):
        """Test space describe with JSON output"""
        mock_resource = {"metadata": {"name": "test-space"}}
        mock_k8s_instance = Mock()
        mock_k8s_instance.get_space.return_value = mock_resource
        mock_k8s_client_class.return_value = mock_k8s_instance

        result = self.runner.invoke(space_describe, [
            '--name', 'test-space',
            '--namespace', 'test-ns',
            '--output', 'json'
        ])

        assert result.exit_code == 0
        output_json = json.loads(result.output)
        assert output_json == mock_resource

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_describe_k8s_error(self, mock_k8s_client_class):
        """Test space describe error handling"""
        mock_k8s_instance = Mock()
        mock_k8s_instance.get_space.side_effect = Exception("Describe failed")
        mock_k8s_client_class.return_value = mock_k8s_instance

        result = self.runner.invoke(space_describe, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Error describing space 'test-space': Describe failed" in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_delete_success(self, mock_k8s_client_class):
        """Test successful space deletion"""
        mock_k8s_instance = Mock()
        mock_k8s_client_class.return_value = mock_k8s_instance

        result = self.runner.invoke(space_delete, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Space 'test-space' deleted successfully" in result.output
        mock_k8s_instance.delete_space.assert_called_once_with('test-ns', 'test-space')

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_delete_k8s_error(self, mock_k8s_client_class):
        """Test space delete error handling"""
        mock_k8s_instance = Mock()
        mock_k8s_instance.delete_space.side_effect = Exception("Delete failed")
        mock_k8s_client_class.return_value = mock_k8s_instance

        result = self.runner.invoke(space_delete, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Error deleting space 'test-space': Delete failed" in result.output

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_update_success(self, mock_k8s_client_class, mock_load_schema):
        """Test successful space update"""
        # Mock schema loading
        mock_load_schema.return_value = {
            "properties": {
                "name": {"type": "string"},
                "display_name": {"type": "string"},
                "namespace": {"type": "string"}
            },
            "required": ["name"]
        }

        # Mock model registry
        mock_model = Mock()
        mock_model.return_value = Mock()
        mock_model.return_value.to_domain.return_value = {
            "name": "test-space",
            "namespace": "test-ns",
            "space_spec": {"spec": {"image": "updated-image"}}
        }

        # Mock KubernetesClient
        mock_k8s_instance = Mock()
        mock_k8s_client_class.return_value = mock_k8s_instance

        with patch('hyperpod_space_template.registry.SCHEMA_REGISTRY', {'1.0': mock_model}):
            result = self.runner.invoke(space_update, [
                '--version', '1.0',
                '--name', 'test-space',
                '--display-name', 'Test Space',
                '--namespace', 'test-ns'
            ])

        assert result.exit_code == 0
        assert "Space 'test-space' updated successfully" in result.output
        mock_k8s_instance.patch_space.assert_called_once()

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_update_k8_error(self, mock_k8s_client_class):
        """Test space update error handling"""
        mock_k8s_instance = Mock()
        mock_k8s_instance.patch_space.side_effect = Exception("Update failed")
        mock_k8s_client_class.return_value = mock_k8s_instance

        mock_model = Mock()
        mock_model.return_value = Mock()
        mock_model.return_value.to_domain.return_value = {
            "name": "test-space",
            "namespace": "test-ns",
            "space_spec": {}
        }

        with patch('hyperpod_space_template.registry.SCHEMA_REGISTRY', {'1.0': mock_model}):
            with patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version') as mock_load_schema:
                mock_load_schema.return_value = {
                    "properties": {
                        "name": {"type": "string"},
                        "display_name": {"type": "string"},
                        "namespace": {"type": "string"}
                    },
                    "required": ["name"]
                }
                result = self.runner.invoke(space_update, [
                    '--version', '1.0',
                    '--name', 'test-space',
                    '--display-name', 'Test Space',
                    '--namespace', 'test-ns'
                ])

        assert result.exit_code == 0
        assert "Error updating space 'test-space': Update failed" in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_start_success(self, mock_k8s_client_class):
        """Test successful space start"""
        mock_k8s_instance = Mock()
        mock_k8s_client_class.return_value = mock_k8s_instance

        result = self.runner.invoke(space_start, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Space 'test-space' start requested" in result.output
        mock_k8s_instance.patch_space.assert_called_once_with(
            namespace='test-ns',
            name='test-space',
            body={"spec": {"desiredStatus": "Running"}}
        )

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_start_k8s_error(self, mock_k8s_client_class):
        """Test space start error handling"""
        mock_k8s_instance = Mock()
        mock_k8s_instance.patch_space.side_effect = Exception("Start failed")
        mock_k8s_client_class.return_value = mock_k8s_instance

        result = self.runner.invoke(space_start, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Error starting space 'test-space': Start failed" in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_stop_success(self, mock_k8s_client_class):
        """Test successful space stop"""
        mock_k8s_instance = Mock()
        mock_k8s_client_class.return_value = mock_k8s_instance

        result = self.runner.invoke(space_stop, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Space 'test-space' stop requested" in result.output
        mock_k8s_instance.patch_space.assert_called_once_with(
            namespace='test-ns',
            name='test-space',
            body={"spec": {"desiredStatus": "Stopped"}}
        )

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_stop_k8s_error(self, mock_k8s_client_class):
        """Test space stop error handling"""
        mock_k8s_instance = Mock()
        mock_k8s_instance.patch_space.side_effect = Exception("Stop failed")
        mock_k8s_client_class.return_value = mock_k8s_instance

        result = self.runner.invoke(space_stop, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Error stopping space 'test-space': Stop failed" in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_get_logs_success(self, mock_k8s_client_class):
        """Test successful space get logs"""
        mock_pod = Mock()
        mock_pod.metadata.name = "test-pod"
        mock_pods = Mock()
        mock_pods.items = [mock_pod]

        mock_k8s_instance = Mock()
        mock_k8s_instance.list_pods_with_labels.return_value = mock_pods
        mock_k8s_instance.get_logs_for_pod.return_value = "test logs"
        mock_k8s_client_class.return_value = mock_k8s_instance

        result = self.runner.invoke(space_get_logs, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "test logs" in result.output
        mock_k8s_instance.list_pods_with_labels.assert_called_once_with(
            namespace='test-ns',
            label_selector='sagemaker.aws.com/space-name=test-space'
        )
        mock_k8s_instance.get_logs_for_pod.assert_called_once_with(
            pod_name='test-pod',
            namespace='test-ns'
        )

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_get_logs_no_pods(self, mock_k8s_client_class):
        """Test space get logs with no pods"""
        mock_pods = Mock()
        mock_pods.items = []

        mock_k8s_instance = Mock()
        mock_k8s_instance.list_pods_with_labels.return_value = mock_pods
        mock_k8s_client_class.return_value = mock_k8s_instance

        result = self.runner.invoke(space_get_logs, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "No pods found for space 'test-space'" in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.KubernetesClient')
    def test_space_get_logs_k8s_error(self, mock_k8s_client_class):
        """Test space get logs error handling"""
        mock_k8s_instance = Mock()
        mock_k8s_instance.list_pods_with_labels.side_effect = Exception("List pod failed")
        mock_k8s_client_class.return_value = mock_k8s_instance

        result = self.runner.invoke(space_get_logs, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Error getting logs for space 'test-space': List pod failed" in result.output

    def test_missing_required_arguments(self):
        """Test commands with missing required arguments"""
        # Test create without name
        result = self.runner.invoke(space_create, ['--namespace', 'test-ns'])
        assert result.exit_code == 2
        assert "Missing option '--name'" in result.output

        # Test describe without name
        result = self.runner.invoke(space_describe, ['--namespace', 'test-ns'])
        assert result.exit_code == 2
        assert "Missing option '--name'" in result.output

        # Test delete without name
        result = self.runner.invoke(space_delete, ['--namespace', 'test-ns'])
        assert result.exit_code == 2
        assert "Missing option '--name'" in result.output

        # Test update without name
        result = self.runner.invoke(space_update, ['--namespace', 'test-ns'])
        assert result.exit_code == 2
        assert "Missing option '--name'" in result.output

        # Test start without name
        result = self.runner.invoke(space_start, ['--namespace', 'test-ns'])
        assert result.exit_code == 2
        assert "Missing option '--name'" in result.output

        # Test stop without name
        result = self.runner.invoke(space_stop, ['--namespace', 'test-ns'])
        assert result.exit_code == 2
        assert "Missing option '--name'" in result.output

        # Test get logs without name
        result = self.runner.invoke(space_get_logs, ['--namespace', 'test-ns'])
        assert result.exit_code == 2
        assert "Missing option '--name'" in result.output
