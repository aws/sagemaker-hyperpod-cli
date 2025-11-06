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
        self.mock_hp_space = Mock()

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
    def test_space_create_success(self, mock_load_schema, mock_hp_space_class):
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

        # Mock HPSpace instance
        mock_hp_space_instance = Mock()
        mock_hp_space_class.return_value = mock_hp_space_instance

        # Mock model registry
        mock_model = Mock()
        mock_model.return_value = Mock()
        mock_model.return_value.to_domain.return_value = {
            "name": "test-space",
            "display_name": "Test Space",
            "namespace": "test-ns",
            "space_spec": {"spec": {"image": "test-image"}}
        }

        with patch('hyperpod_space_template.registry.SCHEMA_REGISTRY', {'1.0': mock_model}):
            with patch('sagemaker.hyperpod.cli.commands.space.SpaceConfig') as mock_space_config:
                mock_space_config.return_value.name = "test-space"
                mock_space_config.return_value.namespace = "test-ns"
                
                result = self.runner.invoke(space_create, [
                    '--version', '1.0',
                    '--name', 'test-space',
                    '--display-name', 'Test Space',
                    '--namespace', 'test-ns'
                ])

        assert result.exit_code == 0
        assert "Space 'test-space' created successfully" in result.output
        mock_hp_space_instance.create.assert_called_once()

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

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_create_hp_space_error(self, mock_hp_space_class):
        """Test space creation error handling"""
        mock_hp_space_instance = Mock()
        mock_hp_space_instance.create.side_effect = Exception("Creation failed")
        mock_hp_space_class.return_value = mock_hp_space_instance

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

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_list_table_output(self, mock_hp_space_class):
        """Test space list with table output"""
        # Mock HPSpace instances with config and status
        mock_space1 = Mock()
        mock_space1.config.name = "space1"
        mock_space1.status = {"conditions": [
            {"type": "Available", "status": "True"},
            {"type": "Progressing", "status": "False"},
            {"type": "Degraded", "status": "False"}
        ]}
        
        mock_space2 = Mock()
        mock_space2.config.name = "space2"
        mock_space2.status = {"conditions": [
            {"type": "Available", "status": "False"},
            {"type": "Progressing", "status": "True"},
            {"type": "Degraded", "status": "False"}
        ]}
        
        mock_hp_space_class.list.return_value = [mock_space1, mock_space2]

        result = self.runner.invoke(space_list, [
            '--namespace', 'test-ns',
            '--output', 'table'
        ])

        assert result.exit_code == 0
        assert "space1" in result.output
        assert "space2" in result.output
        mock_hp_space_class.list.assert_called_once_with(namespace='test-ns')

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_list_json_output(self, mock_hp_space_class):
        """Test space list with JSON output"""
        # Mock HPSpace instances
        mock_space1 = Mock()
        mock_space1.config.model_dump.return_value = {"name": "space1", "namespace": "ns1"}
        
        mock_hp_space_class.list.return_value = [mock_space1]

        result = self.runner.invoke(space_list, [
            '--namespace', 'test-ns',
            '--output', 'json'
        ])

        assert result.exit_code == 0
        output_json = json.loads(result.output)
        assert output_json == [{"name": "space1", "namespace": "ns1"}]

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_list_empty(self, mock_hp_space_class):
        """Test space list with no items"""
        mock_hp_space_class.list.return_value = []

        result = self.runner.invoke(space_list, [
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "No spaces found" in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_list_error(self, mock_hp_space_class):
        """Test space list error handling"""
        mock_hp_space_class.list.side_effect = Exception("List failed")

        result = self.runner.invoke(space_list, [
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Error listing spaces: List failed" in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_describe_yaml_output(self, mock_hp_space_class):
        """Test space describe with YAML output"""
        mock_resource = {"metadata": {"name": "test-space"}}
        # mock_hp_space_instance = Mock()
        # mock_hp_space_instance.raw_resource = mock_resource
        # mock_hp_space_class.get.return_value = mock_hp_space_instance

        with patch('yaml.dump') as mock_yaml_dump:
            mock_yaml_dump.return_value = "yaml_output"
            result = self.runner.invoke(space_describe, [
                '--name', 'test-space',
                '--namespace', 'test-ns',
            ])

        assert result.exit_code == 0
        assert "yaml_output" in result.output
        mock_hp_space_class.get.assert_called_once_with(name='test-space', namespace='test-ns')

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_describe_json_output(self, mock_hp_space_class):
        """Test space describe with JSON output"""
        mock_resource = {"metadata": {"name": "test-space"}}
        mock_hp_space_instance = Mock()
        mock_hp_space_instance.raw_resource = mock_resource
        mock_hp_space_class.get.return_value = mock_hp_space_instance

        result = self.runner.invoke(space_describe, [
            '--name', 'test-space',
            '--namespace', 'test-ns',
            '--output', 'json'
        ])

        assert result.exit_code == 0
        output_json = json.loads(result.output)
        assert output_json == mock_resource

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_describe_hp_space_error(self, mock_hp_space_class):
        """Test space describe error handling"""
        mock_hp_space_class.get.side_effect = Exception("Describe failed")

        result = self.runner.invoke(space_describe, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Error describing space 'test-space': Describe failed" in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_delete_success(self, mock_hp_space_class):
        """Test successful space deletion"""
        mock_hp_space_instance = Mock()
        mock_hp_space_class.get.return_value = mock_hp_space_instance

        result = self.runner.invoke(space_delete, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Space 'test-space' deleted successfully" in result.output
        mock_hp_space_class.get.assert_called_once_with(name='test-space', namespace='test-ns')
        mock_hp_space_instance.delete.assert_called_once()

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_delete_hp_space_error(self, mock_hp_space_class):
        """Test space delete error handling"""
        mock_hp_space_class.get.side_effect = Exception("Delete failed")

        result = self.runner.invoke(space_delete, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Error deleting space 'test-space': Delete failed" in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
    def test_space_update_success(self, mock_load_schema, mock_hp_space_class):
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

        # Mock HPSpace instance
        mock_hp_space_instance = Mock()
        mock_hp_space_instance.config.name = "test-space"
        mock_hp_space_instance.config.display_name = "Test Space"
        mock_hp_space_class.get.return_value = mock_hp_space_instance

        # Mock model registry
        mock_model = Mock()
        mock_model.return_value = Mock()
        mock_model.return_value.to_domain.return_value = {
            "name": "test-space",
            "namespace": "test-ns",
            "space_spec": {"spec": {"image": "updated-image"}}
        }

        with patch('hyperpod_space_template.registry.SCHEMA_REGISTRY', {'1.0': mock_model}):
            result = self.runner.invoke(space_update, [
                '--version', '1.0',
                '--name', 'test-space',
                '--display-name', 'Test Space',
                '--namespace', 'test-ns'
            ])

        assert result.exit_code == 0
        assert "Space 'test-space' updated successfully" in result.output
        mock_hp_space_class.get.assert_called_once_with(name='test-space', namespace='test-ns')
        mock_hp_space_instance.update.assert_called_once()

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_update_hp_space_error(self, mock_hp_space_class):
        """Test space update error handling"""
        mock_hp_space_instance = Mock()
        mock_hp_space_instance.update.side_effect = Exception("Update failed")
        mock_hp_space_class.get.return_value = mock_hp_space_instance

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
        assert "Error updating space: Update failed" in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_start_success(self, mock_hp_space_class):
        """Test successful space start"""
        mock_hp_space_instance = Mock()
        mock_hp_space_class.get.return_value = mock_hp_space_instance

        result = self.runner.invoke(space_start, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Space 'test-space' start requested" in result.output
        mock_hp_space_class.get.assert_called_once_with(name='test-space', namespace='test-ns')
        mock_hp_space_instance.start.assert_called_once()

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_start_hp_space_error(self, mock_hp_space_class):
        """Test space start error handling"""
        mock_hp_space_instance = Mock()
        mock_hp_space_instance.start.side_effect = Exception("Start failed")
        mock_hp_space_class.get.return_value = mock_hp_space_instance

        result = self.runner.invoke(space_start, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Error starting space 'test-space': Start failed" in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_stop_success(self, mock_hp_space_class):
        """Test successful space stop"""
        mock_hp_space_instance = Mock()
        mock_hp_space_class.get.return_value = mock_hp_space_instance

        result = self.runner.invoke(space_stop, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Space 'test-space' stop requested" in result.output
        mock_hp_space_class.get.assert_called_once_with(name='test-space', namespace='test-ns')
        mock_hp_space_instance.stop.assert_called_once()

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_stop_hp_space_error(self, mock_hp_space_class):
        """Test space stop error handling"""
        mock_hp_space_instance = Mock()
        mock_hp_space_instance.stop.side_effect = Exception("Stop failed")
        mock_hp_space_class.get.return_value = mock_hp_space_instance

        result = self.runner.invoke(space_stop, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Error stopping space 'test-space': Stop failed" in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_get_logs_success(self, mock_hp_space_class):
        """Test successful space get logs"""
        mock_hp_space_instance = Mock()
        mock_hp_space_instance.get_logs.return_value = "test logs"
        mock_hp_space_class.get.return_value = mock_hp_space_instance

        result = self.runner.invoke(space_get_logs, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "test logs" in result.output
        mock_hp_space_class.get.assert_called_once_with(name='test-space', namespace='test-ns')
        mock_hp_space_instance.get_logs.assert_called_once_with(pod_name=None, container=None)

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_get_logs_no_pods(self, mock_hp_space_class):
        """Test space get logs with no pods"""
        mock_hp_space_instance = Mock()
        mock_hp_space_instance.get_logs.return_value = ""
        mock_hp_space_class.get.return_value = mock_hp_space_instance

        result = self.runner.invoke(space_get_logs, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        # HPSpace.get_logs() handles the "no pods" case internally

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_get_logs_hp_space_error(self, mock_hp_space_class):
        """Test space get logs error handling"""
        mock_hp_space_instance = Mock()
        mock_hp_space_instance.get_logs.side_effect = Exception("Get logs failed")
        mock_hp_space_class.get.return_value = mock_hp_space_instance

        result = self.runner.invoke(space_get_logs, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Error getting logs for space 'test-space': Get logs failed" in result.output

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
