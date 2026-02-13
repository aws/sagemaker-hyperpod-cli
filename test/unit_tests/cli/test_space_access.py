import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch

from sagemaker.hyperpod.cli.commands.space_access import space_access_create


class TestSpaceAccessCommands:
    """Test cases for space access commands"""

    def setup_method(self):
        self.runner = CliRunner()

    @patch('sagemaker.hyperpod.cli.commands.space_access.HPSpace')
    def test_space_access_create_success(self, mock_hp_space_class):
        """Test successful space access creation"""
        # Mock HPSpace.get() and create_space_access()
        mock_space_instance = Mock()
        mock_space_instance.create_space_access.return_value = {
            "SpaceConnectionType": "vscode-remote",
            "SpaceConnectionUrl": "https://test-url.com"
        }
        mock_hp_space_class.get.return_value = mock_space_instance

        result = self.runner.invoke(space_access_create, [
            '--name', 'test-space',
            '--namespace', 'test-namespace',
            '--connection-type', 'vscode-remote'
        ])

        assert result.exit_code == 0
        assert "https://test-url.com" in result.output
        mock_hp_space_class.get.assert_called_once_with(name='test-space', namespace='test-namespace')
        mock_space_instance.create_space_access.assert_called_once_with(connection_type='vscode-remote')

    @patch('sagemaker.hyperpod.cli.commands.space_access.HPSpace')
    def test_space_access_create_default_values(self, mock_hp_space_class):
        """Test space access creation with default values"""
        mock_space_instance = Mock()
        mock_space_instance.create_space_access.return_value = {
            "SpaceConnectionType": "vscode-remote",
            "SpaceConnectionUrl": "https://default-url.com"
        }
        mock_hp_space_class.get.return_value = mock_space_instance

        result = self.runner.invoke(space_access_create, [
            '--name', 'test-space'
        ])

        assert result.exit_code == 0
        assert "https://default-url.com" in result.output
        mock_hp_space_class.get.assert_called_once_with(name='test-space', namespace='default')
        mock_space_instance.create_space_access.assert_called_once_with(connection_type='vscode-remote')

