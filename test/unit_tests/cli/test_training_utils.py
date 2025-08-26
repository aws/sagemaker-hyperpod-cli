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
            schema_pkg="hyperpod_pytorch_job_template",
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
            '--label-selector', '{"key":"value"}'
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
            schema_pkg="hyperpod_pytorch_job_template",
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
                # Set default values for all expected attributes
                self.node_count = kwargs.get('node_count', None)
                self.deep_health_check_passed_nodes_only = kwargs.get('deep_health_check_passed_nodes_only', None)
                self.tasks_per_node = kwargs.get('tasks_per_node', None)
                self.job_name = kwargs.get('job_name', None)

            def to_domain(self):
                return self

        registry = {'1.0': DummyModel}

        @click.command()
        @generate_click_command(registry=registry, schema_pkg="hyperpod-pytorch-job")
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


    @patch('sagemaker.hyperpod.cli.training_utils.pkgutil.get_data')
    def test_volume_flag_parsing(self, mock_get_data):
        """Test volume flag parsing functionality"""
        schema = {
            'properties': {
                'volume': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'type': {'type': 'string'},
                            'mount_path': {'type': 'string'},
                            'path': {'type': 'string'},
                            'claim_name': {'type': 'string'},
                            'read_only': {'type': 'string'}
                        }
                    }
                }
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
            schema_pkg="hyperpod_pytorch_job_template",
            registry=registry
        )
        def cmd(version, debug, config):
            click.echo(json.dumps({
                'volume': config.volume if hasattr(config, 'volume') else None
            }))

        # Test single hostPath volume
        result = self.runner.invoke(cmd, [
            '--volume', 'name=model-data,type=hostPath,mount_path=/data,path=/host/data'
        ])
        assert result.exit_code == 0
        output = json.loads(result.output)
        expected_volume = [{
            'name': 'model-data',
            'type': 'hostPath',
            'mount_path': '/data',
            'path': '/host/data'
        }]
        assert output['volume'] == expected_volume

        # Test single PVC volume
        result = self.runner.invoke(cmd, [
            '--volume', 'name=training-output,type=pvc,mount_path=/output,claim_name=my-pvc,read_only=false'
        ])
        assert result.exit_code == 0
        output = json.loads(result.output)
        expected_volume = [{
            'name': 'training-output',
            'type': 'pvc',
            'mount_path': '/output',
            'claim_name': 'my-pvc',
            'read_only': 'false'
        }]
        assert output['volume'] == expected_volume

        # Test multiple volumes
        result = self.runner.invoke(cmd, [
            '--volume', 'name=model-data,type=hostPath,mount_path=/data,path=/host/data',
            '--volume', 'name=training-output,type=pvc,mount_path=/output,claim_name=my-pvc,read_only=true'
        ])
        assert result.exit_code == 0
        output = json.loads(result.output)
        expected_volumes = [
            {
                'name': 'model-data',
                'type': 'hostPath',
                'mount_path': '/data',
                'path': '/host/data'
            },
            {
                'name': 'training-output',
                'type': 'pvc',
                'mount_path': '/output',
                'claim_name': 'my-pvc',
                'read_only': 'true'
            }
        ]
        assert output['volume'] == expected_volumes


    @patch('sagemaker.hyperpod.cli.training_utils.pkgutil.get_data')
    def test_volume_domain_conversion(self, mock_get_data):
        """Test volume domain conversion functionality"""
        schema = {
            'properties': {
                'job_name': {'type': 'string'},
                'image': {'type': 'string'},
                'volume': {
                    'type': 'array',
                    'items': {'type': 'object'}
                }
            },
            'required': ['job_name', 'image']
        }
        mock_get_data.return_value = json.dumps(schema).encode()

        class MockVolumeModel:
            def __init__(self, **kwargs):
                self.job_name = kwargs.get('job_name')
                self.image = kwargs.get('image')
                self.volume = kwargs.get('volume')

            def to_domain(self):
                domain_volumes = []
                if self.volume:
                    for vol in self.volume:
                        if vol.get('type') == 'hostPath':
                            domain_volumes.append({
                                'name': vol.get('name'),
                                'type': 'hostPath',
                                'mount_path': vol.get('mount_path'),
                                'host_path': {'path': vol.get('path')}
                            })
                        elif vol.get('type') == 'pvc':
                            domain_volumes.append({
                                'name': vol.get('name'),
                                'type': 'pvc',
                                'mount_path': vol.get('mount_path'),
                                'persistent_volume_claim': {
                                    'claim_name': vol.get('claim_name'),
                                    'read_only': vol.get('read_only') == 'true'
                                }
                            })
                
                return {
                    'name': self.job_name,
                    'image': self.image,
                    'volumes': domain_volumes
                }

        registry = {'1.0': MockVolumeModel}

        @click.command()
        @generate_click_command(
            schema_pkg="hyperpod_pytorch_job_template",
            registry=registry
        )
        def cmd(version, debug, config):
            click.echo(json.dumps(config))

        # Test hostPath volume domain conversion
        result = self.runner.invoke(cmd, [
            '--job-name', 'test-job',
            '--image', 'test-image',
            '--volume', 'name=model-data,type=hostPath,mount_path=/data,path=/host/data'
        ])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['volumes'][0]['type'] == 'hostPath'
        assert output['volumes'][0]['host_path']['path'] == '/host/data'

        # Test PVC volume domain conversion
        result = self.runner.invoke(cmd, [
            '--job-name', 'test-job',
            '--image', 'test-image',
            '--volume', 'name=training-output,type=pvc,mount_path=/output,claim_name=my-pvc,read_only=true'
        ])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['volumes'][0]['type'] == 'pvc'
        assert output['volumes'][0]['persistent_volume_claim']['claim_name'] == 'my-pvc'
        assert output['volumes'][0]['persistent_volume_claim']['read_only'] is True


    @patch('sagemaker.hyperpod.cli.training_utils.pkgutil.get_data')
    def test_volume_flag_parsing_errors(self, mock_get_data):
        """Test volume flag parsing error handling"""
        schema = {
            'properties': {
                'volume': {
                    'type': 'array',
                    'items': {'type': 'object'}
                }
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
            schema_pkg="hyperpod_pytorch_job_template",
            registry=registry
        )
        def cmd(version, debug, config):
            click.echo("success")

        # Test invalid format (missing equals sign)
        result = self.runner.invoke(cmd, [
            '--volume', 'name=model-data,type=hostPath,mount_path,path=/host/data'
        ])
        assert result.exit_code == 2
        assert "should be key=value" in result.output

        # Test empty volume parameter
        result = self.runner.invoke(cmd, [
            '--volume', ''
        ])
        assert result.exit_code == 2
        assert "Error parsing volume" in result.output

    @patch('sagemaker.hyperpod.cli.training_utils.pkgutil.get_data')
    def test_volume_flag_with_equals_in_value(self, mock_get_data):
        """Test volume flag parsing with equals signs in values"""
        schema = {
            'properties': {
                'volume': {
                    'type': 'array',
                    'items': {'type': 'object'}
                }
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
            schema_pkg="hyperpod_pytorch_job_template",
            registry=registry
        )
        def cmd(version, debug, config):
            click.echo(json.dumps({
                'volume': config.volume if hasattr(config, 'volume') else None
            }))

        # Test volume with equals sign in path value
        result = self.runner.invoke(cmd, [
            '--volume', 'name=model-data,type=hostPath,mount_path=/data,path=/host/data=special'
        ])
        assert result.exit_code == 0
        output = json.loads(result.output)
        expected_volume = [{
            'name': 'model-data',
            'type': 'hostPath',
            'mount_path': '/data',
            'path': '/host/data=special'
        }]
        assert output['volume'] == expected_volume

    @patch('sagemaker.hyperpod.cli.training_utils.extract_version_from_args')
    @patch('sagemaker.hyperpod.cli.training_utils.load_schema_for_version')
    def test_version_handling(self, mock_load_schema, mock_extract_version):
        """Test basic version handling and command generation"""
        # Setup mocks
        schema = {
            'properties': {
                'job-name': {
                    'type': 'string',
                    'description': 'Job name'
                }
            },
            'required': ['job-name']
        }
        mock_load_schema.return_value = schema
        mock_extract_version.return_value = '2.0'

        class DummyModel:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def to_domain(self):
                return {'job-name': self.kwargs.get('job_name'),}
                #return self.kwargs

        registry = {'2.0': DummyModel}

        @click.command()
        @click.option('--version', default='2.0', help='Schema version')
        @click.option('--debug', is_flag=True, help='Enable debug mode')
        @generate_click_command(
            schema_pkg="test_package",
            registry=registry
        )
        def cmd(version, debug, domain):
            click.echo(f"version:{version}")
            click.echo(f"debug:{debug}")
            click.echo(f"job-name:{domain.get('job-name')}")

        # Test basic command execution
        result = self.runner.invoke(cmd, ['--job-name', 'test-job'])
        assert result.exit_code == 0
        assert "version:2.0" in result.output
        assert "debug:False" in result.output
        assert "job-name:test-job" in result.output

        # Test with debug flag
        result = self.runner.invoke(cmd, [
            '--job-name', 'test-job',
            '--debug'
        ])
        assert result.exit_code == 0
        assert "debug:True" in result.output

        # Verify mock calls
        mock_load_schema.assert_called_with('2.0', 'test_package')
        mock_extract_version.assert_called()

    @patch('sagemaker.hyperpod.cli.training_utils.extract_version_from_args')
    @patch('sagemaker.hyperpod.cli.training_utils.load_schema_for_version')
    def test_parameter_validation(self, mock_load_schema, mock_extract_version):
        """Test parameter validation and special parameter handling"""
        # Setup mocks
        schema = {
            'properties': {
                'job_name': {
                    'type': 'string',
                    'description': 'Job name'
                }
            },
            'required': ['job_name']
        }
        mock_load_schema.return_value = schema
        mock_extract_version.return_value = '2.0'

        class DummyModel:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def to_domain(self):
                domain_data = {
                    'job-name': self.kwargs.get('job_name'),
                    'environment': self.kwargs.get('environment'),
                    'command': self.kwargs.get('command'),
                    'args': self.kwargs.get('args'),
                    'volume': self.kwargs.get('volume')
                }
                return {k: v for k, v in domain_data.items() if v is not None}

        registry = {'2.0': DummyModel}

        @click.command()
        @generate_click_command(
            schema_pkg="test_package",
            registry=registry
        )
        def cmd(version, debug, domain):
            click.echo(json.dumps(domain))

        # Test with all special parameters
        result = self.runner.invoke(cmd, [
            '--job-name', 'test-job',
            '--environment', '{"VAR1":"value1"}',
            '--command', '[python,train.py]',
            '--args', '[--epochs,10]',
            '--volume', 'name=vol1,type=hostPath,mount_path=/data,path=/mnt/data'
        ])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output.get('job-name') == 'test-job'
        assert output.get('environment') == {"VAR1": "value1"}
        assert 'python' in output.get('command', [])
        assert '--epochs' in output.get('args', [])

        # Test validation errors
        test_cases = [
            # Missing required parameter
            {
                'args': [],
                'expected_error': True,
                'error_message': None  # Will fail because job-name is required
            },
            # Invalid JSON for environment
            {
                'args': ['--job-name', 'test-job', '--environment', 'invalid-json'],
                'expected_error': True,
                'error_message': "must be valid JSON"
            },
            # Invalid volume format
            {
                'args': ['--job-name', 'test-job', '--volume', 'invalid-volume-format'],
                'expected_error': True,
                'error_message': "Invalid volume format"
            },
            # Multiple valid volumes
            {
                'args': [
                    '--job-name', 'test-job',
                    '--volume', 'name=vol1,type=hostPath,mount_path=/data1,path=/mnt/data1',
                    '--volume', 'name=vol2,type=hostPath,mount_path=/data2,path=/mnt/data2'
                ],
                'expected_error': False,
                'error_message': None
            }
        ]

        for test_case in test_cases:
            result = self.runner.invoke(cmd, test_case['args'])
            if test_case['expected_error']:
                assert result.exit_code != 0
                if test_case['error_message']:
                    assert test_case['error_message'] in result.output
            else:
                assert result.exit_code == 0
