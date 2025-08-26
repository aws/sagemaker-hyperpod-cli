import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from sagemaker.hyperpod.cli.init_utils import save_template
from sagemaker.hyperpod.cli.constants.init_constants import CFN


class TestSaveTemplate:
    @patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES')
    @patch('sagemaker.hyperpod.cli.init_utils.save_cfn_jinja')
    def test_save_cfn_jinja_called(self, mock_save_cfn_jinja, mock_templates):
        # Setup
        mock_templates = {
            'test-template': {
                'schema_type': CFN,
                'template': 'test template content'
            }
        }
        mock_save_cfn_jinja.return_value = '/path/to/cfn_params.jinja'
        
        with patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates):
            # Execute
            result = save_template('test-template', Path('/test/dir'))
            
            # Assert
            assert result is True
            mock_save_cfn_jinja.assert_called_once_with(
                directory='/test/dir',
                content='test template content'
            )