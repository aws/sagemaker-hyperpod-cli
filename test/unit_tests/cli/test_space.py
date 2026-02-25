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
    space_portforward,
)


@patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists', return_value=True)
class TestSpaceCommands:
    """Test cases for space commands"""

    def setup_method(self, mock_namespace_exists):
        self.runner = CliRunner()
        self.mock_hp_space = Mock()

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
    def test_space_create_success(self, mock_load_schema, mock_hp_space_class, mock_namespace_exists):
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
    def test_space_create_missing_required_args(self, mock_load_schema, mock_namespace_exists):
        """Test space creation with missing required arguments"""
        mock_load_schema.return_value = {
            "properties": {"name": {"type": "string"}},
            "required": ["name"]
        }

        result = self.runner.invoke(space_create, ['--version', '1.0'])
        assert result.exit_code != 0
        assert 'Missing option' in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_list_table_output(self, mock_hp_space_class, mock_namespace_exists):
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
    def test_space_list_json_output(self, mock_hp_space_class, mock_namespace_exists):
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
    def test_space_list_empty(self, mock_hp_space_class, mock_namespace_exists):
        """Test space list with no items"""
        mock_hp_space_class.list.return_value = []

        result = self.runner.invoke(space_list, [
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "No spaces found" in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_describe_yaml_output(self, mock_hp_space_class, mock_namespace_exists):
        """Test space describe with YAML output"""
        mock_resource = {"metadata": {"name": "test-space"}}

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
    def test_space_describe_json_output(self, mock_hp_space_class, mock_namespace_exists):
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
    def test_space_delete_success(self, mock_hp_space_class, mock_namespace_exists):
        """Test successful space deletion"""
        mock_hp_space_instance = Mock()
        mock_hp_space_class.get.return_value = mock_hp_space_instance

        result = self.runner.invoke(space_delete, [
            '--name', 'test-space',
            '--namespace', 'test-ns'
        ])

        assert result.exit_code == 0
        assert "Requested deletion for Space 'test-space' in namespace 'test-ns'" in result.output
        mock_hp_space_class.get.assert_called_once_with(name='test-space', namespace='test-ns')
        mock_hp_space_instance.delete.assert_called_once()


    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
    def test_space_update_success(self, mock_load_schema, mock_hp_space_class, mock_namespace_exists):
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
    def test_space_start_success(self, mock_hp_space_class, mock_namespace_exists):
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
    def test_space_stop_success(self, mock_hp_space_class, mock_namespace_exists):
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
    def test_space_get_logs_success(self, mock_hp_space_class, mock_namespace_exists):
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
    def test_space_get_logs_no_pods(self, mock_hp_space_class, mock_namespace_exists):
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

    def test_missing_required_arguments(self, mock_namespace_exists):
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

        # Test portforward without name
        result = self.runner.invoke(space_portforward, ['--namespace', 'test-ns', '--local-port', '8080'])
        assert result.exit_code == 2
        assert "Missing option '--name'" in result.output

    @patch('sagemaker.hyperpod.cli.commands.space.HPSpace')
    def test_space_portforward_success(self, mock_hp_space_class, mock_namespace_exists):
        """Test successful space port forwarding"""
        mock_hp_space_instance = Mock()
        mock_hp_space_class.get.return_value = mock_hp_space_instance

        result = self.runner.invoke(space_portforward, [
            '--name', 'test-space',
            '--namespace', 'test-ns',
            '--local-port', '8080'
        ])

        assert result.exit_code == 0
        assert "Forwarding from local port 8080 to space `test-space` in namespace `test-ns`" in result.output
        assert "Please access the service via `http://localhost:8080`. Press Ctrl+C to stop." in result.output
        mock_hp_space_class.get.assert_called_once_with(name='test-space', namespace='test-ns')
        mock_hp_space_instance.portforward_space.assert_called_once_with(8080)
