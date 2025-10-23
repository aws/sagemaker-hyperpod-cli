import pytest
import json
import click
from click.testing import CliRunner
from unittest.mock import Mock, patch
from pydantic import ValidationError

from sagemaker.hyperpod.cli.dev_space_utils import load_schema_for_version, generate_click_command


class TestLoadSchemaForVersion:
    @patch('sagemaker.hyperpod.cli.dev_space_utils.pkgutil.get_data')
    def test_success(self, mock_get_data):
        """Test successful schema loading"""
        data = {"properties": {"name": {"type": "string"}}}
        mock_get_data.return_value = json.dumps(data).encode()

        result = load_schema_for_version('1.2', 'test_package')

        assert result == data
        mock_get_data.assert_called_once_with('test_package.v1_2', 'schema.json')

    @patch('sagemaker.hyperpod.cli.dev_space_utils.pkgutil.get_data')
    def test_schema_not_found(self, mock_get_data):
        """Test handling of missing schema file"""
        mock_get_data.return_value = None

        with pytest.raises(click.ClickException) as exc:
            load_schema_for_version('1.0', 'test_package')

        assert "Could not load schema.json for version 1.0" in str(exc.value)

    @patch('sagemaker.hyperpod.cli.dev_space_utils.pkgutil.get_data')
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

    @patch('sagemaker.hyperpod.cli.dev_space_utils.load_schema_for_version')
    def test_unsupported_version(self, mock_load_schema):
        """Test handling of unsupported version"""
        mock_load_schema.return_value = {'properties': {}, 'required': []}
        registry = {}

        @click.command()
        @generate_click_command(registry=registry)
        def cmd(version, domain_config):
            click.echo('should not reach here')

        result = self.runner.invoke(cmd, [])
        assert result.exit_code != 0
        assert 'Unsupported schema version: 1.0' in result.output

    @patch('sagemaker.hyperpod.cli.dev_space_utils.load_schema_for_version')
    def test_version_handling(self, mock_load_schema):
        """Test version handling in command generation"""
        schema = {'properties': {}, 'required': []}
        mock_load_schema.return_value = schema

        class DummyModel:
            def __init__(self, **kwargs): 
                pass
            def to_domain(self): 
                return self

        registry = {'2.0': DummyModel}

        @click.command()
        @generate_click_command(
            version_key='2.0',
            schema_pkg="test_package",
            registry=registry
        )
        def cmd(version, domain_config):
            click.echo(version)

        result = self.runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert result.output.strip() == '2.0'

    @patch('sagemaker.hyperpod.cli.dev_space_utils.load_schema_for_version')
    def test_resources_building(self, mock_load_schema):
        """Test CPU and memory resource building"""
        schema = {
            'properties': {
                'resources': {
                    'default': {
                        'cpu': '250m',
                        'memory': '256Mi',
                        'nvidia.com/gpu': None
                    }
                }
            },
            'required': []
        }
        mock_load_schema.return_value = schema

        class DummyModel:
            def __init__(self, **kwargs):
                self.resources = kwargs.get('resources')
            def to_domain(self):
                return self

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod_dev_space_template")
        def cmd(version, domain_config):
            click.echo(json.dumps(domain_config.resources))

        # Test with custom CPU and memory
        result = self.runner.invoke(cmd, ['--cpu', '1000m', '--memory', '1Gi'])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['cpu'] == '1000m'
        assert output['memory'] == '1Gi'
        assert output['nvidia.com/gpu'] is None

        # Test with only CPU
        result = self.runner.invoke(cmd, ['--cpu', '750m'])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['cpu'] == '750m'
        assert output['memory'] == '256Mi'  # default

        # Test with no resources specified
        result = self.runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert result.output.strip() == 'null'

    @patch('sagemaker.hyperpod.cli.dev_space_utils.load_schema_for_version')
    def test_type_conversion(self, mock_load_schema):
        """Test type conversion for different parameter types"""
        schema = {
            'properties': {
                'name': {'type': 'string'},
                'desired_status': {'type': 'string', 'enum': ['Running', 'Stopped']},
                'storage_size': {'type': 'string'},
                'port': {'type': 'integer'}
            },
            'required': ['name']
        }
        mock_load_schema.return_value = schema

        class DummyModel:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
            def to_domain(self):
                return self

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod_dev_space_template")
        def cmd(version, domain_config):
            click.echo(json.dumps({
                'name': domain_config.name,
                'desired_status': getattr(domain_config, 'desired_status', None),
                'storage_size': getattr(domain_config, 'storage_size', None),
                'port': getattr(domain_config, 'port', None)
            }))

        # Test string and enum types
        result = self.runner.invoke(cmd, [
            '--name', 'test-space',
            '--desired-status', 'Running',
            '--storage-size', '20Gi'
        ])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['name'] == 'test-space'
        assert output['desired_status'] == 'Running'
        assert output['storage_size'] == '20Gi'

        # Test invalid enum value
        result = self.runner.invoke(cmd, [
            '--name', 'test-space',
            '--desired-status', 'Invalid'
        ])
        assert result.exit_code == 2
        assert "Invalid value" in result.output

    @patch('sagemaker.hyperpod.cli.dev_space_utils.load_schema_for_version')
    def test_successful_command_execution(self, mock_load_schema):
        """Test successful command execution with valid parameters"""
        schema = {
            'properties': {
                'name': {'type': 'string'},
                'image': {'type': 'string', 'default': 'default-image'}
            },
            'required': ['name']
        }
        mock_load_schema.return_value = schema

        class DummyModel:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
            def to_domain(self):
                return self

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod_dev_space_template")
        def cmd(version, domain_config):
            click.echo(f'success: {domain_config.name}')

        # Test successful execution
        result = self.runner.invoke(cmd, ['--name', 'test-space'])
        assert result.exit_code == 0
        assert 'success: test-space' in result.output

    @patch('sagemaker.hyperpod.cli.dev_space_utils.load_schema_for_version')
    def test_immutable_fields_excluded_in_update(self, mock_load_schema):
        """Test that immutable fields are excluded in update mode"""
        schema = {
            'properties': {
                'name': {'type': 'string'},
                'storage_class_name': {'type': 'string'},
                'image': {'type': 'string'}
            },
            'required': ['name']
        }
        mock_load_schema.return_value = schema

        class DummyModel:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
            def to_domain(self):
                return self

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(
            registry=registry, 
            schema_pkg="hyperpod_dev_space_template",
            is_update=True
        )
        def cmd(version, domain_config):
            click.echo('success')

        # Get the command's help to check available options
        result = self.runner.invoke(cmd, ['--help'])
        assert result.exit_code == 0
        # storage_class_name should not be available in update mode
        assert '--storage-class-name' not in result.output
        # but other fields should be available
        assert '--name' in result.output
        assert '--image' in result.output

    @patch('sagemaker.hyperpod.cli.dev_space_utils.load_schema_for_version')
    def test_filtered_kwargs(self, mock_load_schema):
        """Test that None/empty values are filtered out"""
        schema = {
            'properties': {
                'name': {'type': 'string'},
                'image': {'type': 'string', 'default': 'default-image'},
                'namespace': {'type': 'string', 'default': None}
            },
            'required': ['name']
        }
        mock_load_schema.return_value = schema

        class DummyModel:
            def __init__(self, **kwargs):
                self.received_kwargs = kwargs
                self.__dict__.update(kwargs)
            def to_domain(self):
                return self

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod_dev_space_template")
        def cmd(version, domain_config):
            # Check that None values were filtered out
            click.echo(json.dumps(domain_config.received_kwargs))

        result = self.runner.invoke(cmd, ['--name', 'test-space'])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['name'] == 'test-space'
        assert output['image'] == 'default-image'
        assert 'namespace' not in output

    @patch('sagemaker.hyperpod.cli.dev_space_utils.load_schema_for_version')
    def test_default_version_injection(self, mock_load_schema):
        """Test that version flag is injected when no version_key is provided"""
        schema = {'properties': {}, 'required': []}
        mock_load_schema.return_value = schema

        class DummyModel:
            def __init__(self, **kwargs): pass
            def to_domain(self): return self

        registry = {'1.0': DummyModel, '2.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod_dev_space_template")
        def cmd(version, domain_config):
            click.echo(version)

        # Test default version
        result = self.runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert result.output.strip() == '1.0'

        # Test custom version
        result = self.runner.invoke(cmd, ['--version', '2.0'])
        print(result.output)
        assert result.exit_code == 0
        assert result.output.strip() == '2.0'

    @patch('sagemaker.hyperpod.cli.dev_space_utils.load_schema_for_version')
    def test_schema_defaults_and_required_fields(self, mock_load_schema):
        """Test handling of schema defaults and required fields"""
        schema = {
            'properties': {
                'name': {'type': 'string'},
                'image': {'type': 'string', 'default': 'default-image'},
                'namespace': {'type': 'string', 'default': None}
            },
            'required': ['name', 'namespace']
        }
        mock_load_schema.return_value = schema

        class DummyModel:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
            def to_domain(self):
                return self

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod_dev_space_template")
        def cmd(version, domain_config):
            click.echo('success')

        # Test missing required field
        result = self.runner.invoke(cmd, [])
        assert result.exit_code == 2
        assert "Missing option" in result.output

        # Test with required field provided
        result = self.runner.invoke(cmd, ['--name', 'test-space', '--namespace', 'test-ns'])
        print(result.output)
        assert result.exit_code == 0
        assert result.output.strip() == 'success'
