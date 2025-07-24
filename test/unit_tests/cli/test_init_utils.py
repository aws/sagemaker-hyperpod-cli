import pytest
import json
import click
from click.testing import CliRunner
from unittest.mock import Mock, patch

from sagemaker.hyperpod.cli.init_utils import load_schema_for_version


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