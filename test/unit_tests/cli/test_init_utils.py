import pytest
import json
import click
from click.testing import CliRunner
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from sagemaker.hyperpod.cli.init_utils import load_schema_for_version, save_template, generate_click_command
from sagemaker.hyperpod.cli.constants.init_constants import CFN


class TestLoadSchemaForVersion:
    @patch('sagemaker.hyperpod.cli.init_utils.pkgutil.get_data')
    def test_success(self, mock_get_data):
        data = {"properties": {"x": {"type": "string"}}}
        mock_get_data.return_value = json.dumps(data).encode()
        result = load_schema_for_version('1.2', 'pkg')
        assert result == data
        mock_get_data.assert_called_once_with('pkg.v1_2', 'schema.json')

    @patch('sagemaker.hyperpod.cli.init_utils.pkgutil.get_data')
    def test_not_found(self, mock_get_data):
        mock_get_data.return_value = None
        with pytest.raises(click.ClickException) as exc:
            load_schema_for_version('3.0', 'mypkg')
        assert "Could not load schema.json for version 3.0" in str(exc.value)

    @patch('sagemaker.hyperpod.cli.init_utils.pkgutil.get_data')
    def test_invalid_json(self, mock_get_data):
        mock_get_data.return_value = b'invalid'
        with pytest.raises(json.JSONDecodeError):
            load_schema_for_version('1.0', 'pkg')


@patch('builtins.open', new_callable=mock_open)
@patch('sagemaker.hyperpod.cli.init_utils.Path')
@patch('sagemaker.hyperpod.cli.init_utils.os.path.join')
def test_save_cfn_jinja_called(mock_join,
                               mock_path,
                               mock_file):
    # Setup
    mock_templates = {
        'test-template': {
            'schema_type': CFN,
            'template': 'test template content'
        }
    }
    mock_join.return_value = '/test/dir/cfn_params.jinja'
    mock_path.return_value.mkdir = Mock()

    with patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates):
        # Execute
        result = save_template('test-template', Path('/test/dir'))

        # Assert
        assert result is True
        mock_file.assert_called_once_with('/test/dir/cfn_params.jinja', 'w', encoding='utf-8')
        mock_file().write.assert_called_once_with('test template content')


def test_generate_click_command_cfn_case():
    # Setup
    mock_templates = {
        'cfn-template': {
            'schema_type': CFN
        }
    }
    
    with patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates):
        # Execute
        decorator = generate_click_command()
        
        # Create a dummy function to decorate
        @decorator
        def dummy_func(template, directory, namespace, version, model_config):
            return model_config
        
        # Assert that the decorator was created successfully
        assert callable(dummy_func)