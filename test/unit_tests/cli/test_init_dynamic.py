import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from sagemaker.hyperpod.cli.commands.init import validate, _default_create, reset


class TestInitDynamicTemplateIntegration:
    """Test cases for init.py dynamic template integration"""

    @patch('sagemaker.hyperpod.cli.commands.init.is_dynamic_template')
    @patch('sagemaker.hyperpod.cli.commands.init._validate_dynamic_template')
    @patch('sagemaker.hyperpod.cli.commands.init.load_config')
    def test_validate_command_dynamic_template(self, mock_load_config, mock_validate_dynamic, mock_is_dynamic):
        """Test validate command with dynamic template"""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with runner.isolated_filesystem(temp_dir):
                # Mock config loading
                mock_load_config.return_value = ({"job_name": "test"}, "hyp-recipe-job", "1.0")
                mock_is_dynamic.return_value = True
                mock_validate_dynamic.return_value = True
                
                result = runner.invoke(validate)
                
                assert result.exit_code == 0
                mock_validate_dynamic.assert_called_once()

    @patch('sagemaker.hyperpod.cli.commands.init.is_dynamic_template')
    @patch('sagemaker.hyperpod.cli.commands.init._create_dynamic_template')
    @patch('sagemaker.hyperpod.cli.commands.init.load_config_and_validate')
    def test_create_command_dynamic_template(self, mock_load_config, mock_create_dynamic, mock_is_dynamic):
        """Test create command with dynamic template"""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with runner.isolated_filesystem(temp_dir):
                # Mock config loading
                config_data = {"job_name": "test-job", "epochs": 50}
                mock_load_config.return_value = (config_data, "hyp-recipe-job", "1.0")
                mock_is_dynamic.return_value = True
                
                result = runner.invoke(_default_create)
                
                assert result.exit_code == 0
                mock_create_dynamic.assert_called_once()

    @patch('sagemaker.hyperpod.cli.commands.init.is_dynamic_template')
    @patch('sagemaker.hyperpod.cli.commands.init._generate_dynamic_config_yaml')
    @patch('sagemaker.hyperpod.cli.commands.init.load_config')
    def test_reset_command_dynamic_template(self, mock_load_config, mock_generate_config, mock_is_dynamic):
        """Test reset command with dynamic template"""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with runner.isolated_filesystem(temp_dir):
                # Mock config loading
                mock_load_config.return_value = ({"job_name": "test"}, "hyp-recipe-job", "1.0")
                mock_is_dynamic.return_value = True
                
                result = runner.invoke(reset)
                
                assert result.exit_code == 0
                mock_generate_config.assert_called_once_with(Path(".").resolve(), "hyp-recipe-job", "1.0")
                assert "config.yaml reset: all fields set to default values" in result.output

    @patch('sagemaker.hyperpod.cli.commands.init.is_dynamic_template')
    @patch('sagemaker.hyperpod.cli.commands.init.build_config_from_schema')
    @patch('sagemaker.hyperpod.cli.commands.init.save_config_yaml')
    @patch('sagemaker.hyperpod.cli.commands.init.load_config')
    def test_reset_command_standard_template(self, mock_load_config, mock_save_config, mock_build_config, mock_is_dynamic):
        """Test reset command with standard template (non-dynamic)"""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with runner.isolated_filesystem(temp_dir):
                # Mock config loading
                mock_load_config.return_value = ({"namespace": "test"}, "hyp-pytorch-job", "1.0")
                mock_is_dynamic.return_value = False
                mock_build_config.return_value = ({"namespace": "default"}, {})
                
                result = runner.invoke(reset)
                
                assert result.exit_code == 0
                mock_build_config.assert_called_once_with("hyp-pytorch-job", "1.0")
                mock_save_config.assert_called_once()
