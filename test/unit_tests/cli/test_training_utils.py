import pytest
import json
import click
from click.testing import CliRunner
from unittest.mock import Mock, patch

from sagemaker.hyperpod.cli.training_utils import load_schema_for_version, generate_click_command


class TestLoadSchemaForVersion:
    @patch('sagemaker.hyperpod.cli.training_utils.pkgutil.get_data')
    def test_success(self, mock_get_data):
        """Test successful schema loading"""
        data = {"properties": {"x": {"type": "string"}}}
        mock_get_data.return_value = json.dumps(data).encode()

        result = load_schema_for_version('1.2', 'test_package')

        assert result == data
        mock_get_data.assert_called_once_with('test_package.v1_2', 'schema.json')

    @patch('sagemaker.hyperpod.cli.training_utils.pkgutil.get_data')
    def test_schema_not_found(self, mock_get_data):
        """Test handling of missing schema file"""
        mock_get_data.return_value = None

        with pytest.raises(click.ClickException) as exc:
            load_schema_for_version('1.0', 'test_package')

        assert "Could not load schema.json for version 1.0" in str(exc.value)

    @patch('sagemaker.hyperpod.cli.training_utils.pkgutil.get_data')
    def test_invalid_json_schema(self, mock_get_data):
        """Test handling of invalid JSON in schema file"""
        mock_get_data.return_value = b'invalid json'

        with pytest.raises(json.JSONDecodeError):
            load_schema_for_version('1.0', 'test_package')

class TestGenerateClickCommand:
    def setup_method(self):
        self.runner = CliRunner()

    def test_missing_registry(self):
        """Test that registry is required"""
        with pytest.raises(ValueError) as exc:
            generate_click_command(schema_pkg="test_package")
        assert "You must pass a registry mapping" in str(exc.value)

    @patch('sagemaker.hyperpod.cli.training_utils.pkgutil.get_data')
    def test_pytorch_json_flags(self, mock_get_data):
        """Test handling of JSON flags for PyTorch config"""
        schema = {
            'properties': {
                'environment': {'type': 'object'},
                'label_selector': {'type': 'object'}
            }
        }
        mock_get_data.return_value = json.dumps(schema).encode()

        class DummyModel:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
            def to_domain(self):
                return self

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(
            schema_pkg="hyperpod_pytorchjob_config_schemas",
            registry=registry
        )
        def cmd(version, debug, config):
            click.echo(json.dumps({
                'environment': config.environment,
                'label_selector': config.label_selector
            }))

        # Test valid JSON input
        result = self.runner.invoke(cmd, [
            '--environment', '{"VAR1":"val1"}',
            '--label_selector', '{"key":"value"}'
        ])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output == {
            'environment': {'VAR1': 'val1'},
            'label_selector': {'key': 'value'}
        }

        # Test invalid JSON input
        result = self.runner.invoke(cmd, ['--environment', 'invalid'])
        assert result.exit_code == 2
        assert 'must be valid JSON' in result.output

    @patch('sagemaker.hyperpod.cli.training_utils.pkgutil.get_data')
    def test_list_parameters(self, mock_get_data):
        """Test handling of list parameters"""
        schema = {
            'properties': {
                'command': {'type': 'array'},
                'args': {'type': 'array'}
            }
        }
        mock_get_data.return_value = json.dumps(schema).encode()

        class DummyModel:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
            def to_domain(self):
                return self

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(
            schema_pkg="hyperpod_pytorchjob_config_schemas",
            registry=registry
        )
        def cmd(version, debug, config):
            click.echo(json.dumps({
                'command': config.command,
                'args': config.args
            }))

        # Test list input
        result = self.runner.invoke(cmd, [
            '--command', '[python, train.py]',
            '--args', '[--epochs, 10]'
        ])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output == {
            'command': ['python', 'train.py'],
            'args': ['--epochs', '10']
        }

    @patch('sagemaker.hyperpod.cli.training_utils.pkgutil.get_data')
    def test_version_handling(self, mock_get_data):
        """Test version handling in command generation"""
        schema = {'properties': {}}
        mock_get_data.return_value = json.dumps(schema).encode()

        class DummyModel:
            def __init__(self, **kwargs): pass

            def to_domain(self): return self

        registry = {'2.0': DummyModel}

        @click.command()
        @generate_click_command(
            version_key='2.0',
            schema_pkg="test_package",
            registry=registry
        )
        def cmd(version, debug, config):
            click.echo(version)

        result = self.runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert result.output.strip() == '2.0'

    @patch('sagemaker.hyperpod.cli.training_utils.pkgutil.get_data')
    def test_type_conversion(self, mock_get_data):
        """Test type conversion for different parameter types"""
        # Mock the schema with different types
        schema = {
            'properties': {
                'node_count': {'type': 'integer'},
                'deep_health_check_passed_nodes_only': {'type': 'boolean'},
                'tasks_per_node': {'type': 'integer'},
                'job_name': {'type': 'string'}
            }
        }
        mock_get_data.return_value = json.dumps(schema).encode()

        class DummyModel:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

            def to_domain(self):
                return self

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry)
        def cmd(version, debug, config):
            click.echo(json.dumps({
                'node_count': config.node_count,
                'deep_health_check_passed_nodes_only': config.deep_health_check_passed_nodes_only,
                'tasks_per_node': config.tasks_per_node,
                'job_name': config.job_name
            }))

        # Test integer conversion
        result = self.runner.invoke(cmd, ['--node-count', '5'])
        assert result.exit_code == 0

        # Test boolean conversion
        result = self.runner.invoke(cmd, ['--deep-health-check-passed-nodes-only', 'true'])
        assert result.exit_code == 0

        # Test string conversion
        result = self.runner.invoke(cmd, ['--job-name', 'test-job'])
        assert result.exit_code == 0

        # Test invalid type (should fail gracefully)
        result = self.runner.invoke(cmd, ['--node-count', 'not-a-number'])
        assert result.exit_code == 2
        assert "Invalid value" in result.output
