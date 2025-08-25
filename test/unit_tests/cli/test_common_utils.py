import pytest
import json
import sys
from unittest.mock import Mock, patch
import click

from sagemaker.hyperpod.cli.common_utils import (
    extract_version_from_args,
    get_latest_version,
    load_schema_for_version,
    JUMPSTART_SCHEMA,
    CUSTOM_SCHEMA,
    PYTORCH_SCHEMA,
    JUMPSTART_COMMAND,
    CUSTOM_COMMAND,
    PYTORCH_COMMAND
)


class TestExtractVersionFromArgs:
    """Test cases for extract_version_from_args function"""

    def setup_method(self):
        """Setup test fixtures"""
        self.registry = {'1.0': Mock(), '1.1': Mock(), '2.0': Mock()}
        self.default_version = '1.0'

    @patch('sys.argv', ['script'])
    def test_no_version_flag_returns_default(self):
        """Test that default version is returned when --version flag is not present"""
        result = extract_version_from_args(self.registry, JUMPSTART_SCHEMA, self.default_version)
        assert result == self.default_version

    @patch('sys.argv', ['script', '--version'])
    def test_version_flag_without_value_returns_default(self):
        """Test that default version is returned when --version flag has no value"""
        result = extract_version_from_args(self.registry, JUMPSTART_SCHEMA, self.default_version)
        assert result == self.default_version

    @patch('sys.argv', ['script', '--version', '1.1'])
    def test_version_flag_with_supported_version_no_command(self):
        """Test that requested version is returned when no hyp- command is present"""
        result = extract_version_from_args(self.registry, JUMPSTART_SCHEMA, self.default_version)
        assert result == '1.1'

    @patch('sys.argv', ['script', '--version', '3.0'])
    def test_version_flag_with_unsupported_version_no_command(self):
        """Test that default version is returned when no hyp- command is present and version is unsupported"""
        result = extract_version_from_args(self.registry, JUMPSTART_SCHEMA, self.default_version)
        assert result == self.default_version

    @patch('sys.argv', ['script', 'hyp-jumpstart-endpoint', '--version', '1.1'])
    def test_jumpstart_command_with_supported_version(self):
        """Test jumpstart command with supported version"""
        result = extract_version_from_args(self.registry, JUMPSTART_SCHEMA, self.default_version)
        assert result == '1.1'

    @patch('sys.argv', ['script', 'hyp-jumpstart-endpoint', '--version', '3.0'])
    def test_jumpstart_command_with_unsupported_version_raises_exception(self):
        """Test jumpstart command with unsupported version raises ClickException"""
        with pytest.raises(click.ClickException) as exc_info:
            extract_version_from_args(self.registry, JUMPSTART_SCHEMA, self.default_version)
        assert "Unsupported schema version: 3.0" in str(exc_info.value)

    @patch('sys.argv', ['script', 'hyp-custom-endpoint', '--version', '1.1'])
    def test_custom_command_with_supported_version(self):
        """Test custom command with supported version"""
        result = extract_version_from_args(self.registry, CUSTOM_SCHEMA, self.default_version)
        assert result == '1.1'

    @patch('sys.argv', ['script', 'hyp-custom-endpoint', '--version', '3.0'])
    def test_custom_command_with_unsupported_version_raises_exception(self):
        """Test custom command with unsupported version raises ClickException"""
        with pytest.raises(click.ClickException) as exc_info:
            extract_version_from_args(self.registry, CUSTOM_SCHEMA, self.default_version)
        assert "Unsupported schema version: 3.0" in str(exc_info.value)

    @patch('sys.argv', ['script', 'hyp-pytorch-job', '--version', '1.1'])
    def test_pytorch_command_with_supported_version(self):
        """Test pytorch command with supported version"""
        result = extract_version_from_args(self.registry, PYTORCH_SCHEMA, self.default_version)
        assert result == '1.1'

    @patch('sys.argv', ['script', 'hyp-pytorch-job', '--version', '3.0'])
    def test_pytorch_command_with_unsupported_version_raises_exception(self):
        """Test pytorch command with unsupported version raises ClickException"""
        with pytest.raises(click.ClickException) as exc_info:
            extract_version_from_args(self.registry, PYTORCH_SCHEMA, self.default_version)
        assert "Unsupported schema version: 3.0" in str(exc_info.value)

    @patch('sys.argv', ['script', 'hyp-jumpstart-endpoint', '--version', '3.0'])
    def test_wrong_schema_pkg_with_jumpstart_command_returns_default(self):
        """Test that wrong schema package with jumpstart command returns default for unsupported version"""
        result = extract_version_from_args(self.registry, CUSTOM_SCHEMA, self.default_version)
        assert result == self.default_version

    @patch('sys.argv', ['script', 'hyp-custom-endpoint', '--version', '3.0'])
    def test_wrong_schema_pkg_with_custom_command_returns_default(self):
        """Test that wrong schema package with custom command returns default for unsupported version"""
        result = extract_version_from_args(self.registry, JUMPSTART_SCHEMA, self.default_version)
        assert result == self.default_version

    @patch('sys.argv', ['script', 'hyp-pytorch-job', '--version', '3.0'])
    def test_wrong_schema_pkg_with_pytorch_command_returns_default(self):
        """Test that wrong schema package with pytorch command returns default for unsupported version"""
        result = extract_version_from_args(self.registry, JUMPSTART_SCHEMA, self.default_version)
        assert result == self.default_version

    @patch('sys.argv', ['script', 'hyp-other-command', '--version', '3.0'])
    def test_unrecognized_command_returns_default_for_unsupported_version(self):
        """Test that unrecognized hyp- command returns default version when version is unsupported"""
        result = extract_version_from_args(self.registry, JUMPSTART_SCHEMA, self.default_version)
        assert result == self.default_version

    @patch('sys.argv', ['script', 'hyp-other-command', '--version', '1.1'])
    def test_unrecognized_command_returns_requested_version_if_supported(self):
        """Test that unrecognized hyp- command returns requested version when version is supported"""
        result = extract_version_from_args(self.registry, JUMPSTART_SCHEMA, self.default_version)
        assert result == '1.1'

    @patch('sys.argv', ['script', '--version', '1.1', 'hyp-jumpstart-endpoint'])
    def test_version_flag_before_command(self):
        """Test that version flag works when it appears before the command"""
        result = extract_version_from_args(self.registry, JUMPSTART_SCHEMA, self.default_version)
        assert result == '1.1'

    def test_empty_registry_with_validation_needed(self):
        """Test behavior with empty registry when validation is needed"""
        empty_registry = {}
        with patch('sys.argv', ['script', 'hyp-jumpstart-endpoint', '--version', '1.0']):
            with pytest.raises(click.ClickException) as exc_info:
                extract_version_from_args(empty_registry, JUMPSTART_SCHEMA, self.default_version)
            assert "Unsupported schema version: 1.0" in str(exc_info.value)

    def test_none_registry_with_validation_needed(self):
        """Test behavior with None registry when validation is needed"""
        with patch('sys.argv', ['script', 'hyp-jumpstart-endpoint', '--version', '1.0']):
            result = extract_version_from_args(None, JUMPSTART_SCHEMA, self.default_version)
            assert result == '1.0'


class TestGetLatestVersion:
    """Test cases for get_latest_version function"""

    def test_empty_registry_raises_error(self):
        """Test that empty registry raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            get_latest_version({})
        assert "Schema registry is empty" in str(exc_info.value)

    def test_none_registry_raises_error(self):
        """Test that None registry raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            get_latest_version(None)
        assert "Schema registry is empty" in str(exc_info.value)

    def test_single_version_registry(self):
        """Test registry with single version"""
        registry = {'1.0': Mock()}
        result = get_latest_version(registry)
        assert result == '1.0'

    def test_multiple_versions_returns_latest(self):
        """Test that latest version is returned from multiple versions"""
        registry = {'1.0': Mock(), '1.1': Mock(), '2.0': Mock(), '1.2': Mock()}
        result = get_latest_version(registry)
        assert result == '2.0'

    def test_semantic_version_sorting(self):
        """Test that semantic versions are sorted correctly"""
        registry = {'1.10': Mock(), '1.2': Mock(), '1.1': Mock(), '2.0': Mock()}
        result = get_latest_version(registry)
        assert result == '2.0'

    def test_complex_version_sorting(self):
        """Test complex version number sorting"""
        registry = {
            '1.0': Mock(),
            '1.1': Mock(), 
            '1.10': Mock(),
            '1.2': Mock(),
            '2.0': Mock(),
            '10.0': Mock()
        }
        result = get_latest_version(registry)
        assert result == '10.0'

    def test_three_part_versions(self):
        """Test three-part version numbers"""
        registry = {
            '1.0.0': Mock(),
            '1.0.1': Mock(),
            '1.1.0': Mock(),
            '2.0.0': Mock()
        }
        result = get_latest_version(registry)
        assert result == '2.0.0'


class TestLoadSchemaForVersion:
    """Test cases for load_schema_for_version function"""

    @patch('sagemaker.hyperpod.cli.common_utils.pkgutil.get_data')
    def test_successful_schema_load(self, mock_get_data):
        """Test successful schema loading"""
        schema_data = {"properties": {"test": {"type": "string"}}, "required": ["test"]}
        mock_get_data.return_value = json.dumps(schema_data).encode()
        
        result = load_schema_for_version('1.0', 'test_package')
        
        assert result == schema_data
        mock_get_data.assert_called_once_with('test_package.v1_0', 'schema.json')

    @patch('sagemaker.hyperpod.cli.common_utils.pkgutil.get_data')
    def test_schema_not_found_raises_exception(self, mock_get_data):
        """Test that missing schema raises ClickException"""
        mock_get_data.return_value = None
        
        with pytest.raises(click.ClickException) as exc_info:
            load_schema_for_version('1.0', 'test_package')
        
        assert "Could not load schema.json for version 1.0" in str(exc_info.value)
        assert "test_package.v1_0" in str(exc_info.value)

    @patch('sagemaker.hyperpod.cli.common_utils.pkgutil.get_data')
    def test_invalid_json_raises_exception(self, mock_get_data):
        """Test that invalid JSON raises JSONDecodeError"""
        mock_get_data.return_value = b'invalid json content'
        
        with pytest.raises(json.JSONDecodeError):
            load_schema_for_version('1.0', 'test_package')

    @patch('sagemaker.hyperpod.cli.common_utils.pkgutil.get_data')
    def test_version_with_dots_converted_to_underscores(self, mock_get_data):
        """Test that version dots are converted to underscores in package name"""
        schema_data = {"test": "data"}
        mock_get_data.return_value = json.dumps(schema_data).encode()
        
        load_schema_for_version('1.2.3', 'my_package')
        
        mock_get_data.assert_called_once_with('my_package.v1_2_3', 'schema.json')

    @patch('sagemaker.hyperpod.cli.common_utils.pkgutil.get_data')
    def test_empty_schema_loads_successfully(self, mock_get_data):
        """Test that empty schema loads successfully"""
        empty_schema = {}
        mock_get_data.return_value = json.dumps(empty_schema).encode()
        
        result = load_schema_for_version('1.0', 'test_package')
        
        assert result == empty_schema

    @patch('sagemaker.hyperpod.cli.common_utils.pkgutil.get_data')
    def test_complex_schema_loads_successfully(self, mock_get_data):
        """Test that complex schema loads successfully"""
        complex_schema = {
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "age": {"type": "integer", "minimum": 0},
                "nested": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "number"}
                    }
                }
            },
            "required": ["name", "age"],
            "additionalProperties": False
        }
        mock_get_data.return_value = json.dumps(complex_schema).encode()
        
        result = load_schema_for_version('2.1', 'complex_package')
        
        assert result == complex_schema
        mock_get_data.assert_called_once_with('complex_package.v2_1', 'schema.json')


class TestConstants:
    """Test that constants are defined correctly"""

    def test_schema_constants(self):
        """Test that schema constants are defined"""
        assert JUMPSTART_SCHEMA == "hyperpod_jumpstart_inference_template"
        assert CUSTOM_SCHEMA == "hyperpod_custom_inference_template"
        assert PYTORCH_SCHEMA == "hyperpod_pytorch_job_template"

    def test_command_constants(self):
        """Test that command constants are defined"""
        assert JUMPSTART_COMMAND == "hyp-jumpstart-endpoint"
        assert CUSTOM_COMMAND == "hyp-custom-endpoint"
        assert PYTORCH_COMMAND == "hyp-pytorch-job"
