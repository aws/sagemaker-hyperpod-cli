import pytest
import json
import click
from click.testing import CliRunner
from unittest.mock import Mock, patch
import sys

from sagemaker.hyperpod.cli.inference_utils import generate_click_command


class TestGenerateClickCommand:
    def setup_method(self):
        self.runner = CliRunner()

    def test_registry_required(self):
        with pytest.raises(ValueError):
            generate_click_command()

    @patch('sagemaker.hyperpod.cli.inference_utils.load_schema_for_version')
    def test_unsupported_version(self, mock_load_schema):
        mock_load_schema.return_value = {'properties': {}, 'required': []}
        # Registry with version 2.0, but the default version (1.0) is not in registry
        # This will cause get_latest_version to return 2.0, but extract_version_from_args
        # will try to use default 1.0 which is not in registry
        registry = {'2.0': Mock()}
        with patch('sagemaker.hyperpod.cli.inference_utils.extract_version_from_args', return_value='1.0'):
            @click.command()
            @generate_click_command(registry=registry)
            def cmd(namespace, version, domain):
                click.echo('should not')

        # Invocation with no args uses default version 1.0 which is unsupported
        res = self.runner.invoke(cmd, [])
        assert res.exit_code != 0
        assert 'Unsupported schema version: 1.0' in res.output

    @patch('sagemaker.hyperpod.cli.inference_utils.load_schema_for_version')
    def test_json_flags(self, mock_load_schema):
        mock_load_schema.return_value = {
            'properties': {
                'env': {'type': 'object'},
                'dimensions': {'type': 'object'},
                'resources_limits': {'type': 'object'},
                'resources_requests': {'type': 'object'}
            },
            'required': []
        }
        # Domain receives flags as attributes env, dimensions, resources_limits, resources_requests
        class DummyFlat:
            def __init__(self, **kwargs): self.__dict__.update(kwargs)
            def to_domain(self): return self
        registry = {'1.0': DummyFlat}

        @click.command()
        @generate_click_command(registry=registry)
        def cmd(version, debug, domain):
            click.echo(json.dumps({
                'env': domain.env, 'dimensions': domain.dimensions,
                'limits': domain.resources_limits, 'reqs': domain.resources_requests
            }))

        # valid JSON
        res_ok = self.runner.invoke(cmd, [
            '--env', '{"a":1}',
            '--dimensions', '{"b":2}',
            '--resources-limits', '{"c":3}',
            '--resources-requests', '{"d":4}'
        ])
        assert res_ok.exit_code == 0
        out = json.loads(res_ok.output)
        assert out == {'env': {'a':1}, 'dimensions': {'b':2}, 'limits': {'c':3}, 'reqs': {'d':4}}

        # invalid JSON produces click error
        res_err = self.runner.invoke(cmd, ['--env', 'notjson'])
        assert res_err.exit_code == 2
        assert 'must be valid JSON' in res_err.output

    @patch('sagemaker.hyperpod.cli.inference_utils.load_schema_for_version')
    def test_type_mapping_and_defaults(self, mock_load_schema):
        mock_load_schema.return_value = {
            'properties': {
                's': {'type': 'string'},
                'i': {'type': 'integer'},
                'n': {'type': 'number'},
                'b': {'type': 'boolean'},
                'e': {'type': 'string', 'enum': ['x','y']},
                'd': {'type': 'string', 'default': 'Z'}
            },
            'required': ['s']
        }
        class DummyFlat:
            def __init__(self, **kwargs): self.__dict__.update(kwargs)
            def to_domain(self): return self
        registry = {'1.0': DummyFlat}

        @click.command()
        @generate_click_command(registry=registry)
        def cmd(version, debug, domain):
            click.echo(f"{domain.s},{domain.i},{domain.n},{domain.b},{domain.e},{domain.d}")

        res = self.runner.invoke(cmd, [
            '--s', 'hello', '--i', '5', '--n', '2.5', '--b', 'True', '--e', 'x'
        ])
        assert res.exit_code == 0
        assert res.output.strip() == 'hello,5,2.5,True,x,Z'

    @patch('sagemaker.hyperpod.cli.inference_utils.extract_version_from_args')
    @patch('sagemaker.hyperpod.cli.inference_utils.load_schema_for_version')
    def test_version_and_schema_pkg(self, mock_load_schema, mock_extract_version):
        # Setup mocks
        mock_load_schema.return_value = {'properties': {}, 'required': []}
        mock_extract_version.return_value = '2.0'

        # Create dummy model class
        class DummyFlat:
            def __init__(self, **kwargs):
                pass

            def to_domain(self):
                return {}

        # Setup registry
        registry = {'2.0': DummyFlat}

        # Create test command
        @click.command()
        @generate_click_command(schema_pkg='mypkg', registry=registry)
        def cmd(version, debug, domain):
            click.echo(f"version: {version}")

        # Test command execution
        result = self.runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert "version: 2.0" in result.output

        # Verify mock calls
        mock_load_schema.assert_called_once_with('2.0', 'mypkg')
        mock_extract_version.assert_called_once()
