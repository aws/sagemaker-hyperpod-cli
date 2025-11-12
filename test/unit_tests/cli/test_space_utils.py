import pytest
import json
import click
from click.testing import CliRunner
from unittest.mock import Mock, patch
from pydantic import ValidationError, BaseModel

from sagemaker.hyperpod.cli.space_utils import load_schema_for_version, generate_click_command


class TestLoadSchemaForVersion:
    @patch('sagemaker.hyperpod.cli.space_utils.pkgutil.get_data')
    def test_success(self, mock_get_data):
        """Test successful schema loading"""
        data = {"properties": {"name": {"type": "string"}}}
        mock_get_data.return_value = json.dumps(data).encode()

        result = load_schema_for_version('1.2', 'test_package')

        assert result == data
        mock_get_data.assert_called_once_with('test_package.v1_2', 'schema.json')

    @patch('sagemaker.hyperpod.cli.space_utils.pkgutil.get_data')
    def test_schema_not_found(self, mock_get_data):
        """Test handling of missing schema file"""
        mock_get_data.return_value = None

        with pytest.raises(click.ClickException) as exc:
            load_schema_for_version('1.0', 'test_package')

        assert "Could not load schema.json for version 1.0" in str(exc.value)

    @patch('sagemaker.hyperpod.cli.space_utils.pkgutil.get_data')
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

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
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

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
    def test_version_handling(self, mock_load_schema):
        """Test version handling in command generation"""
        schema = {'properties': {}, 'required': []}
        mock_load_schema.return_value = schema

        class DummyModel(BaseModel):
            class Config:
                extra = 'allow'

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

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
    def test_resources_building(self, mock_load_schema):
        """Test CPU, memory, GPU and fractional GPU resource building"""
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

        class DummyModel(BaseModel):
            class Config:
                extra = 'allow'

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod_space_template")
        def cmd(version, domain_config):
            click.echo(json.dumps(domain_config.get('resources')))

        # Test with CPU and memory requests and limits
        result = self.runner.invoke(cmd, ['--cpu', '1000m', '--cpu-limit', '2000m', '--memory', '1Gi', '--memory-limit', '2Gi'])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['requests']['cpu'] == '1000m'
        assert output['requests']['memory'] == '1Gi'
        assert output['limits']['cpu'] == '2000m'
        assert output['limits']['memory'] == '2Gi'

        # Test with GPU requests and limits
        result = self.runner.invoke(cmd, ['--gpu', '1', '--gpu-limit', '2'])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['requests']['nvidia.com/gpu'] == '1'
        assert output['limits']['nvidia.com/gpu'] == '2'

        # Test with fractional GPU partitioning
        result = self.runner.invoke(cmd, ['--accelerator-partition-type', 'mig-1g.5gb', '--accelerator-partition-count', '2'])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['requests']['nvidia.com/mig-1g.5gb'] == '2'
        assert output['limits']['nvidia.com/mig-1g.5gb'] == '2'

        # Test with no resources specified
        result = self.runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert result.output.strip() == 'null'

        # Test error when only one accelerator partition parameter is provided
        result = self.runner.invoke(cmd, ['--accelerator-partition-type', 'mig-1g.5gb'])
        assert result.exit_code == 2
        assert 'Both accelerator-partition-type and accelerator-partition-count must be specified together' in result.output

        result = self.runner.invoke(cmd, ['--accelerator-partition-count', '2'])
        assert result.exit_code == 2
        assert 'Both accelerator-partition-type and accelerator-partition-count must be specified together' in result.output

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
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

        class DummyModel(BaseModel):
            class Config:
                extra = 'allow'

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod_space_template")
        def cmd(version, domain_config):
            click.echo(json.dumps({
                'name': domain_config.get('name'),
                'desired_status': domain_config.get('desired_status'),
                'storage_size': domain_config.get('storage_size'),
                'port': domain_config.get('port')
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

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
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

        class DummyModel(BaseModel):
            class Config:
                extra = 'allow'

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod_space_template")
        def cmd(version, domain_config):
            click.echo(f'success: {domain_config.get("name")}')

        # Test successful execution
        result = self.runner.invoke(cmd, ['--name', 'test-space'])
        assert result.exit_code == 0
        assert 'success: test-space' in result.output

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
    def test_immutable_fields_excluded_in_update(self, mock_load_schema):
        """Test that immutable fields are excluded in update mode"""
        schema = {
            'properties': {
                'name': {'type': 'string'},
                'storage': {'type': 'object'},  # storage is immutable
                'template_ref': {'type': 'string'},  # template_ref is immutable
                'image': {'type': 'string'}
            },
            'required': ['name']
        }
        mock_load_schema.return_value = schema

        class DummyModel(BaseModel):
            class Config:
                extra = 'allow'

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(
            registry=registry, 
            schema_pkg="hyperpod_space_template",
            is_update=True
        )
        def cmd(version, domain_config):
            click.echo('success')

        # Get the command's help to check available options
        result = self.runner.invoke(cmd, ['--help'])
        assert result.exit_code == 0
        # storage and template_ref should not be available in update mode
        assert '--storage' not in result.output
        assert '--template-ref' not in result.output
        # but other fields should be available
        assert '--name' in result.output
        assert '--image' in result.output

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
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

        class DummyModel(BaseModel):
            class Config:
                extra = 'allow'

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod_space_template")
        def cmd(version, domain_config):
            # Check that None values were filtered out
            click.echo(json.dumps(domain_config))

        result = self.runner.invoke(cmd, ['--name', 'test-space'])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['name'] == 'test-space'
        assert output['image'] == 'default-image'
        assert 'namespace' not in output

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
    def test_default_version_injection(self, mock_load_schema):
        """Test that version flag is injected when no version_key is provided"""
        schema = {'properties': {}, 'required': []}
        mock_load_schema.return_value = schema

        class DummyModel(BaseModel):
            class Config:
                extra = 'allow'

        registry = {'1.0': DummyModel, '2.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod_space_template")
        def cmd(version, domain_config):
            click.echo(version)

        # Test default version
        result = self.runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert result.output.strip() == '1.0'

        # Test custom version
        result = self.runner.invoke(cmd, ['--version', '2.0'])
        assert result.exit_code == 0
        assert result.output.strip() == '2.0'

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
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

        class DummyModel(BaseModel):
            class Config:
                extra = 'allow'

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod_space_template")
        def cmd(version, domain_config):
            click.echo('success')

        # Test missing required field
        result = self.runner.invoke(cmd, [])
        assert result.exit_code == 2
        assert "Missing option" in result.output

        # Test with required field provided
        result = self.runner.invoke(cmd, ['--name', 'test-space', '--namespace', 'test-ns'])
        assert result.exit_code == 0
        assert result.output.strip() == 'success'

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
    def test_volume_parsing(self, mock_load_schema):
        """Test volume parameter parsing"""
        schema = {
            'properties': {
                'name': {'type': 'string'},
                'volumes': {'type': 'array'}
            },
            'required': ['name']
        }
        mock_load_schema.return_value = schema

        class DummyModel(BaseModel):
            class Config:
                extra = 'allow'

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod_space_template")
        def cmd(version, domain_config):
            click.echo(json.dumps(domain_config.get('volumes')))

        # Test valid volume parsing
        result = self.runner.invoke(cmd, [
            '--name', 'test-space',
            '--volume', 'name=vol1,mountPath=/data,persistentVolumeClaimName=pvc1'
        ])
        assert result.exit_code == 0
        volumes = json.loads(result.output)
        assert len(volumes) == 1
        assert volumes[0]['name'] == 'vol1'
        assert volumes[0]['mountPath'] == '/data'
        assert volumes[0]['persistentVolumeClaimName'] == 'pvc1'

        # Test multiple volumes
        result = self.runner.invoke(cmd, [
            '--name', 'test-space',
            '--volume', 'name=vol1,mountPath=/data1',
            '--volume', 'name=vol2,mountPath=/data2'
        ])
        assert result.exit_code == 0
        volumes = json.loads(result.output)
        assert len(volumes) == 2

        # Test invalid volume format
        result = self.runner.invoke(cmd, [
            '--name', 'test-space',
            '--volume', 'invalid_format'
        ])
        assert result.exit_code == 2
        assert 'Invalid volume format' in result.output

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
    def test_storage_parsing(self, mock_load_schema):
        """Test storage parameter parsing"""
        schema = {
            'properties': {
                'name': {'type': 'string'},
                'storage': {'type': 'object'}
            },
            'required': ['name']
        }
        mock_load_schema.return_value = schema

        class DummyModel(BaseModel):
            class Config:
                extra = 'allow'

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod_space_template")
        def cmd(version, domain_config):
            click.echo(json.dumps(domain_config.get('storage')))

        # Test valid storage parsing
        result = self.runner.invoke(cmd, [
            '--name', 'test-space',
            '--storage', 'storageClassName=gp2,size=20Gi,mountPath=/data'
        ])
        assert result.exit_code == 0
        storage = json.loads(result.output)
        assert storage['storageClassName'] == 'gp2'
        assert storage['size'] == '20Gi'
        assert storage['mountPath'] == '/data'

        # Test invalid storage format
        result = self.runner.invoke(cmd, [
            '--name', 'test-space',
            '--storage', 'invalid_format'
        ])
        assert result.exit_code == 2
        assert 'Invalid storage format' in result.output

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
    def test_container_config_parsing_simple(self, mock_load_schema):
        """Test container config parameter parsing with simple format"""
        schema = {
            'properties': {
                'name': {'type': 'string'},
                'container_config': {'type': 'object'}
            },
            'required': ['name']
        }
        mock_load_schema.return_value = schema

        class DummyModel(BaseModel):
            class Config:
                extra = 'allow'

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod_space_template")
        def cmd(version, domain_config):
            click.echo(json.dumps(domain_config.get('container_config')))

        # Test valid container config with semicolon format
        result = self.runner.invoke(cmd, [
            '--name', 'test-space',
            '--container-config', 'command=python;app.py,args=--port;8080'
        ])
        assert result.exit_code == 0
        config = json.loads(result.output)
        assert config['command'] == ['python', 'app.py']
        assert config['args'] == ['--port', '8080']

        # Test invalid container config format
        result = self.runner.invoke(cmd, [
            '--name', 'test-space',
            '--container-config', 'invalid_format'
        ])
        assert result.exit_code == 2
        assert 'Invalid container-config format' in result.output

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
    def test_json_object_parsing(self, mock_load_schema):
        """Test JSON object parameter parsing"""
        schema = {
            'properties': {
                'name': {'type': 'string'},
                'metadata': {'type': 'object'},
                'tags': {'type': 'array'}
            },
            'required': ['name']
        }
        mock_load_schema.return_value = schema

        class DummyModel(BaseModel):
            class Config:
                extra = 'allow'

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod_space_template")
        def cmd(version, domain_config):
            result = {
                'metadata': domain_config.get('metadata'),
                'tags': domain_config.get('tags')
            }
            click.echo(json.dumps(result))

        # Test valid JSON object
        result = self.runner.invoke(cmd, [
            '--name', 'test-space',
            '--metadata', '{"key": "value", "number": 42}',
            '--tags', '["tag1", "tag2"]'
        ])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['metadata']['key'] == 'value'
        assert output['metadata']['number'] == 42
        assert output['tags'] == ['tag1', 'tag2']

        # Test invalid JSON
        result = self.runner.invoke(cmd, [
            '--name', 'test-space',
            '--metadata', 'invalid json'
        ])
        assert result.exit_code == 2
        assert 'Invalid JSON for --metadata' in result.output

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
    def test_anyof_type_handling(self, mock_load_schema):
        """Test handling of anyOf type specifications"""
        schema = {
            'properties': {
                'name': {'type': 'string'},
                'config': {
                    'anyOf': [
                        {'type': 'object'},
                        {'type': 'null'}
                    ]
                }
            },
            'required': ['name']
        }
        mock_load_schema.return_value = schema

        class DummyModel(BaseModel):
            class Config:
                extra = 'allow'

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod_space_template")
        def cmd(version, domain_config):
            click.echo(json.dumps(domain_config.get('config')))

        # Test with JSON object for anyOf type
        result = self.runner.invoke(cmd, [
            '--name', 'test-space',
            '--config', '{"setting": "value"}'
        ])
        assert result.exit_code == 0
        config = json.loads(result.output)
        assert config['setting'] == 'value'

    @patch('sagemaker.hyperpod.cli.space_utils.load_schema_for_version')
    def test_display_name_optional_in_update_mode(self, mock_load_schema):
        """Test that display_name is optional in update mode"""
        schema = {
            'properties': {
                'name': {'type': 'string'},
                'display_name': {'type': 'string'},
                'image': {'type': 'string'}
            },
            'required': ['name', 'display_name']
        }
        mock_load_schema.return_value = schema

        class DummyModel(BaseModel):
            class Config:
                extra = 'allow'

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(
            registry=registry, 
            schema_pkg="hyperpod_space_template",
            is_update=True
        )
        def cmd(version, domain_config):
            click.echo('success')

        # In update mode, display_name should not be required
        result = self.runner.invoke(cmd, ['--name', 'test-space'])
        assert result.exit_code == 0
        assert 'success' in result.output
