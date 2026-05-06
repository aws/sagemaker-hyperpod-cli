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

    @patch('sagemaker.hyperpod.cli.commands.space_access.HPSpace')
    def test_space_access_create_kiro_remote(self, mock_hp_space_class):
        """Test space access creation with kiro-remote connection type"""
        mock_space_instance = Mock()
        mock_space_instance.create_space_access.return_value = {
            "SpaceConnectionType": "kiro-remote",
            "SpaceConnectionUrl": "https://kiro-url.com"
        }
        mock_hp_space_class.get.return_value = mock_space_instance

        result = self.runner.invoke(space_access_create, [
            '--name', 'test-space',
            '--connection-type', 'kiro-remote'
        ])

        assert result.exit_code == 0
        assert "https://kiro-url.com" in result.output
        mock_space_instance.create_space_access.assert_called_once_with(connection_type='kiro-remote')

    @patch('sagemaker.hyperpod.cli.commands.space_access.HPSpace')
    def test_space_access_create_cursor_remote(self, mock_hp_space_class):
        """Test space access creation with cursor-remote connection type"""
        mock_space_instance = Mock()
        mock_space_instance.create_space_access.return_value = {
            "SpaceConnectionType": "cursor-remote",
            "SpaceConnectionUrl": "https://cursor-url.com"
        }
        mock_hp_space_class.get.return_value = mock_space_instance

        result = self.runner.invoke(space_access_create, [
            '--name', 'test-space',
            '--connection-type', 'cursor-remote'
        ])

        assert result.exit_code == 0
        assert "https://cursor-url.com" in result.output
        mock_space_instance.create_space_access.assert_called_once_with(connection_type='cursor-remote')


    @pytest.mark.parametrize("invalid_type", [
        "invalid-type", "-remote", "remote", "my--vscode-remote", "vscode_remote", "",
    ])
    @patch('sagemaker.hyperpod.cli.commands.space_access.HPSpace')
    def test_space_access_create_invalid_connection_type(self, mock_hp_space_class, invalid_type):
        """Test space access creation rejects invalid connection type patterns"""
        mock_space_instance = Mock()
        mock_space_instance.create_space_access.side_effect = ValueError(
            "--connection-type must be 'web-ui' or follow the '{ide}-remote' pattern"
        )
        mock_hp_space_class.get.return_value = mock_space_instance

        result = self.runner.invoke(space_access_create, [
            '--name', 'test-space',
            '--connection-type', invalid_type
        ] if invalid_type else ['--name', 'test-space', '--connection-type', ''])

        assert result.exit_code != 0