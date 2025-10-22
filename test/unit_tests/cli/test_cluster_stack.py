import pytest
import unittest
from unittest.mock import Mock, patch, mock_open
from click.testing import CliRunner
from datetime import datetime
import click
from sagemaker.hyperpod.cli.commands.cluster_stack import update_cluster, list_cluster_stacks, parse_status_list


class TestUpdateCluster:
    
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.Cluster')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_update_cluster_with_instance_groups_string(self, mock_setup_logging, mock_cluster_class):
        # Arrange
        mock_cluster = Mock()
        mock_cluster_class.get.return_value = mock_cluster
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        runner = CliRunner()
        
        # Act
        result = runner.invoke(update_cluster, [
            '--cluster-name', 'test-cluster',
            '--instance-groups', '[{"instance_type": "ml.t3.medium", "instance_count": 1, "instance_group_name": "test-group", "life_cycle_config": {"source_s3_uri": "s3://bucket/path", "on_create": "script.sh"}, "execution_role": "arn:aws:iam::123456789012:role/test-role"}]',
            '--node-recovery', 'Automatic'
        ])
        
        # Assert
        assert result.exit_code == 0
        mock_cluster_class.get.assert_called_once_with(cluster_name="test-cluster", region=None)
        mock_cluster.update.assert_called_once()



    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.Cluster')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_update_cluster_with_none_instance_groups(self, mock_setup_logging, mock_cluster_class):
        # Arrange
        mock_cluster = Mock()
        mock_cluster_class.get.return_value = mock_cluster
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        runner = CliRunner()
        
        # Act
        result = runner.invoke(update_cluster, [
            '--cluster-name', 'test-cluster',
            '--node-recovery', 'Automatic'
        ])
        
        # Assert
        assert result.exit_code == 0
        mock_cluster_class.get.assert_called_once_with(cluster_name="test-cluster", region=None)
        mock_cluster.update.assert_called_once_with(node_recovery="Automatic")


class TestListClusterStacks:
    
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.HpClusterStack.list')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_list_cluster_stacks_success(self, mock_setup_logging, mock_hp_cluster_list):
        # Arrange
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        mock_stacks_response = {
            'StackSummaries': [
                {
                    'StackId': 'arn:aws:cloudformation:us-west-2:123456789012:stack/test-stack/12345',
                    'StackName': 'test-stack',
                    'CreationTime': datetime(2024, 1, 1, 12, 0, 0),
                    'StackStatus': 'CREATE_COMPLETE',
                    'DriftInformation': {'StackDriftStatus': 'NOT_CHECKED'}
                }
            ]
        }
        mock_hp_cluster_list.return_value = mock_stacks_response
        
        runner = CliRunner()
        
        # Act
        result = runner.invoke(list_cluster_stacks, [])
        
        # Assert
        assert result.exit_code == 0
        assert 'HyperPod Cluster Stacks (1 found)' in result.output
        assert 'test-stack' in result.output
        assert 'CREATE_COMPLETE' in result.output
        mock_hp_cluster_list.assert_called_once_with(region=None, stack_status_filter=None)

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.HpClusterStack.list')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_list_cluster_stacks_with_region(self, mock_setup_logging, mock_hp_cluster_list):
        # Arrange
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        mock_stacks_response = {'StackSummaries': []}
        mock_hp_cluster_list.return_value = mock_stacks_response
        
        runner = CliRunner()
        
        # Act
        result = runner.invoke(list_cluster_stacks, ['--region', 'us-east-1'])
        
        # Assert
        assert result.exit_code == 0
        mock_hp_cluster_list.assert_called_once_with(region='us-east-1', stack_status_filter=None)

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.HpClusterStack.list')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_list_cluster_stacks_no_stacks(self, mock_setup_logging, mock_hp_cluster_list):
        # Arrange
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        mock_hp_cluster_list.return_value = None
        
        runner = CliRunner()
        
        # Act
        result = runner.invoke(list_cluster_stacks, [])
        
        # Assert
        assert result.exit_code == 0
        assert 'No stacks found' in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.HpClusterStack.list')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_list_cluster_stacks_with_datetime_objects(self, mock_setup_logging, mock_hp_cluster_list):
        # Arrange
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        mock_stacks_response = {
            'StackSummaries': [
                {
                    'StackId': 'arn:aws:cloudformation:us-west-2:123456789012:stack/test-stack/12345',
                    'StackName': 'test-stack',
                    'CreationTime': datetime(2024, 1, 1, 12, 0, 0),
                    'LastUpdatedTime': datetime(2024, 1, 2, 14, 30, 0),
                    'StackStatus': 'CREATE_COMPLETE',
                    'DriftInformation': {
                        'StackDriftStatus': 'DRIFTED',
                        'LastCheckTimestamp': datetime(2024, 1, 3, 16, 45, 0)
                    }
                }
            ]
        }
        mock_hp_cluster_list.return_value = mock_stacks_response
        
        runner = CliRunner()
        
        # Act
        result = runner.invoke(list_cluster_stacks, [])
        
        # Assert
        assert result.exit_code == 0
        assert '2024-01-01 12:00:00' in result.output
        assert '2024-01-02 14:30:00' in result.output
        assert '2024-01-03 16:45:00' in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.HpClusterStack.list')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_list_cluster_stacks_error_handling(self, mock_setup_logging, mock_hp_cluster_list):
        # Arrange
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        mock_hp_cluster_list.side_effect = Exception("AWS error")
        
        runner = CliRunner()
        
        # Act
        result = runner.invoke(list_cluster_stacks, [])
        
        # Assert
        assert result.exit_code == 1
        assert 'Error listing stacks: AWS error' in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.HpClusterStack.list')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_list_cluster_stacks_with_status_filter(self, mock_setup_logging, mock_hp_cluster_list):
        """Test that status filter parameter is passed correctly to SDK."""
        # Arrange
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        mock_stacks_response = {
            'StackSummaries': [
                {
                    'StackId': 'arn:aws:cloudformation:us-west-2:123456789012:stack/create-complete-stack/12345',
                    'StackName': 'create-complete-stack',
                    'CreationTime': datetime(2024, 1, 1, 12, 0, 0),
                    'StackStatus': 'CREATE_COMPLETE',
                    'DriftInformation': {'StackDriftStatus': 'NOT_CHECKED'}
                }
            ]
        }
        mock_hp_cluster_list.return_value = mock_stacks_response
        
        runner = CliRunner()
        
        # Act
        result = runner.invoke(list_cluster_stacks, ['--status', "['CREATE_COMPLETE', 'UPDATE_COMPLETE']"])
        
        # Assert
        assert result.exit_code == 0
        assert 'create-complete-stack' in result.output
        mock_hp_cluster_list.assert_called_once_with(region=None, stack_status_filter=['CREATE_COMPLETE', 'UPDATE_COMPLETE'])

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.HpClusterStack.list')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_list_cluster_stacks_invalid_status_format(self, mock_setup_logging, mock_hp_cluster_list):
        """Test that invalid status format raises appropriate error."""
        # Arrange
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        runner = CliRunner()
        
        # Act
        result = runner.invoke(list_cluster_stacks, ['--status', 'invalid-format'])
        
        # Assert
        assert result.exit_code != 0
        assert 'Invalid list format' in result.output
        mock_hp_cluster_list.assert_not_called()

    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.HpClusterStack.list')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.setup_logging')
    def test_list_cluster_stacks_single_status(self, mock_setup_logging, mock_hp_cluster_list):
        """Test filtering with single status."""
        # Arrange
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        mock_stacks_response = {
            'StackSummaries': [
                {
                    'StackId': 'arn:aws:cloudformation:us-west-2:123456789012:stack/in-progress-stack/12345',
                    'StackName': 'in-progress-stack',
                    'CreationTime': datetime(2024, 1, 1, 12, 0, 0),
                    'StackStatus': 'CREATE_IN_PROGRESS',
                    'DriftInformation': {'StackDriftStatus': 'NOT_CHECKED'}
                }
            ]
        }
        mock_hp_cluster_list.return_value = mock_stacks_response
        
        runner = CliRunner()
        
        # Act
        result = runner.invoke(list_cluster_stacks, ['--status', "['CREATE_IN_PROGRESS']"])
        
        # Assert
        assert result.exit_code == 0
        assert 'in-progress-stack' in result.output
        mock_hp_cluster_list.assert_called_once_with(region=None, stack_status_filter=['CREATE_IN_PROGRESS'])


class TestParseStatusList:
    """Test cases for parse_status_list function"""

    def test_parse_status_list_valid_format(self):
        """Test parsing valid list format."""
        result = parse_status_list(None, None, "['CREATE_COMPLETE', 'UPDATE_COMPLETE']")
        assert result == ['CREATE_COMPLETE', 'UPDATE_COMPLETE']

    def test_parse_status_list_single_item(self):
        """Test parsing single item list."""
        result = parse_status_list(None, None, "['CREATE_COMPLETE']")
        assert result == ['CREATE_COMPLETE']

    def test_parse_status_list_empty_input(self):
        """Test parsing empty/None input."""
        result = parse_status_list(None, None, None)
        assert result is None
        
        result = parse_status_list(None, None, "")
        assert result is None

    def test_parse_status_list_invalid_format(self):
        """Test parsing invalid format raises BadParameter."""
        with pytest.raises(click.BadParameter) as exc_info:
            parse_status_list(None, None, "invalid-format")
        assert "Invalid list format" in str(exc_info.value)

    def test_parse_status_list_non_list_format(self):
        """Test parsing valid syntax but non-list raises BadParameter."""
        with pytest.raises(click.BadParameter) as exc_info:
            parse_status_list(None, None, "'not-a-list'")
        assert "Expected list format" in str(exc_info.value)


@patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.importlib.resources.read_text')
@patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.HpClusterStack.get_template')

class TestCreateClusterStack(unittest.TestCase):
    """Test create_cluster_stack function"""

    @patch('os.path.exists')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.TEMPLATES')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack._filter_cli_metadata_fields')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.load_config')
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.HpClusterStack')
    def test_create_cluster_stack_success(self, mock_hp_cluster_stack_class, mock_load_config, mock_filter, mock_templates, mock_exists, mock_get_template, mock_read_text):
        """Test successful cluster stack creation"""
        # Arrange
        mock_exists.return_value = True
        mock_load_config.return_value = ({'key': 'value'}, 'hyp-cluster-stack', '1.0')
        mock_filter.return_value = {'key': 'value'}
        
        mock_model_class = Mock()
        mock_model_instance = Mock()
        mock_model_instance.to_config.return_value = {'transformed': 'config'}
        mock_model_class.return_value = mock_model_instance
        
        mock_sdk_instance = Mock()
        mock_sdk_instance.create.return_value = 'stack-123'
        mock_hp_cluster_stack_class.return_value = mock_sdk_instance
        
        # Fix: Make registry a proper dict, not Mock
        mock_registry = {'1.0': mock_model_class}
        mock_template_config = {'registry': mock_registry}
        mock_templates.__getitem__.return_value = mock_template_config
        
        from sagemaker.hyperpod.cli.commands.cluster_stack import create_cluster_stack
        
        create_cluster_stack.callback('config.yaml', 'us-west-2', 1, False)
        
        mock_load_config.assert_called_once()
        mock_filter.assert_called_once_with({'key': 'value'})
        mock_model_class.assert_called_once_with(**{'key': 'value'})
        mock_model_instance.to_config.assert_called_once_with(region='us-west-2')
        mock_hp_cluster_stack_class.assert_called_once_with(**{'transformed': 'config'})
        mock_sdk_instance.create.assert_called_once_with('us-west-2', 1)

    @patch('os.path.exists')
    def test_create_cluster_stack_file_not_found(self, mock_exists, mock_get_template, mock_read_text):
        """Test handling of missing config file"""
        # Arrange
        mock_exists.return_value = False
        
        from sagemaker.hyperpod.cli.commands.cluster_stack import create_cluster_stack
        
        create_cluster_stack.callback('nonexistent.yaml', 'us-west-2', 1, False)
        
        # Assert - function should return early without error
        mock_exists.assert_called_once_with('nonexistent.yaml')
