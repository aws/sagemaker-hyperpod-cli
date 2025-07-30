import pytest
import yaml
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from click.testing import CliRunner
from pydantic import ValidationError

from sagemaker.hyperpod.cli.commands.init import validate
from sagemaker.hyperpod.cli.constants.init_constants import CFN


class TestValidate:
    
    @patch('sagemaker.hyperpod.cli.commands.init.load_config_and_validate')
    @patch('sagemaker.hyperpod.cli.commands.init.TEMPLATES')
    @patch('sagemaker.hyperpod.cli.commands.init.HpClusterStack')
    def test_validate_cfn_success(self, mock_hp_cluster_stack, mock_templates, mock_load_config):
        """Test successful CFN validation"""
        # Setup
        mock_load_config.return_value = (
            {
                'template': 'cfn-template',
                'namespace': 'default',
                'hyperpod_cluster_name': 'test-cluster',
                'tags': [{'Key': 'Environment', 'Value': 'Test'}]
            },
            'cfn-template',
            '1.0'
        )
        
        mock_templates.__getitem__.return_value = {'schema_type': CFN}
        mock_hp_cluster_stack.return_value = Mock()
        
        runner = CliRunner()
        
        # Execute
        result = runner.invoke(validate)
        
        # Assert
        assert result.exit_code == 0
        assert "✔️  config.yaml is valid!" in result.output
        mock_hp_cluster_stack.assert_called_once_with(
            hyperpod_cluster_name='test-cluster',
            tags='[{"Key": "Environment", "Value": "Test"}]'
        )
    
    @patch('sagemaker.hyperpod.cli.commands.init.load_config_and_validate')
    @patch('sagemaker.hyperpod.cli.commands.init.TEMPLATES')
    @patch('sagemaker.hyperpod.cli.commands.init.HpClusterStack')
    def test_validate_cfn_validation_error(self, mock_hp_cluster_stack, mock_templates, mock_load_config):
        """Test CFN validation with validation errors"""
        # Setup
        mock_load_config.return_value = (
            {
                'template': 'cfn-template',
                'namespace': 'default',
                'invalid_field': 'invalid_value'
            },
            'cfn-template',
            '1.0'
        )
        
        mock_templates.__getitem__.return_value = {'schema_type': CFN}
        
        # Create a real ValidationError by trying to validate invalid data
        from pydantic import BaseModel, Field
        
        class TestModel(BaseModel):
            required_field: str = Field(...)
        
        try:
            TestModel()
        except ValidationError as e:
            validation_error = e
        
        mock_hp_cluster_stack.side_effect = validation_error
        
        runner = CliRunner()
        
        # Execute
        result = runner.invoke(validate)
        
        # Assert
        assert result.exit_code == 1
        assert "❌  Validation errors:" in result.output
        assert "required_field: Field required" in result.output