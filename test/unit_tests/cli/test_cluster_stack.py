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
@patch('sagemaker.hyperpod.cli.init_utils.HpClusterStack.get_template')
class TestCreateClusterStackHelper(unittest.TestCase):
    """Test create_cluster_stack_helper function"""
    
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.HpClusterStack')
    @patch('yaml.safe_load')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_cluster_stack_helper_success(self, mock_file, mock_exists, mock_yaml_load, mock_cluster_stack, mock_get_template, mock_read_text):
        """Test successful cluster stack creation"""
        # Mock template methods
        mock_get_template.return_value = '{"Parameters": {}}'
        mock_read_text.return_value = 'Parameters: {}'
        
        with patch('sagemaker.hyperpod.cli.commands.cluster_stack.logger') as mock_logger:
            from sagemaker.hyperpod.cli.commands.cluster_stack import create_cluster_stack_helper
            
            # Setup mocks
            mock_exists.return_value = True
            mock_yaml_load.return_value = {
                'template': 'hyp-cluster',
                'version': '1.0',
                'eks_cluster_name': 'test-cluster',
                'namespace': 'test-namespace'
            }
            
            mock_stack_instance = Mock()
            mock_stack_instance.create.return_value = {'StackId': 'test-stack-id'}
            mock_cluster_stack.return_value = mock_stack_instance
            
            # Execute
            create_cluster_stack_helper('config.yaml', 'us-west-2', False)
            
            # Verify
            mock_exists.assert_called_once_with('config.yaml')
            mock_yaml_load.assert_called_once()
            mock_cluster_stack.assert_called_once_with(
                eks_cluster_name='test-cluster',
                version='1.0'
            )
            mock_stack_instance.create.assert_called_once_with('us-west-2')
    
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.logger')
    @patch('os.path.exists')
    def test_create_cluster_stack_helper_file_not_found(self,
                                                        mock_exists,
                                                        mock_logger,
                                                        mock_get_template,
                                                        mock_read_text):
        """Test handling of missing config file"""
        from sagemaker.hyperpod.cli.commands.cluster_stack import create_cluster_stack_helper
        
        mock_exists.return_value = False
        
        create_cluster_stack_helper('nonexistent.yaml', 'us-west-2', False)
        from sagemaker.hyperpod.cli.commands.cluster_stack import create_cluster_stack_helper
        
        mock_exists.return_value = False
        
        create_cluster_stack_helper('nonexistent.yaml', 'us-west-2', False)

    
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.HpClusterStack')
    @patch('yaml.safe_load')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_cluster_stack_helper_filters_template_fields(self, mock_file, mock_exists, mock_yaml_load, mock_cluster_stack, mock_get_template, mock_read_text):
        """Test that template and namespace fields are filtered out"""
        # Mock template methods
        mock_get_template.return_value = '{"Parameters": {}}'
        mock_read_text.return_value = 'Parameters: {}'
        
        with patch('sagemaker.hyperpod.cli.commands.cluster_stack.logger') as mock_logger:
            from sagemaker.hyperpod.cli.commands.cluster_stack import create_cluster_stack_helper
            
            # Setup mocks
            mock_exists.return_value = True
            mock_yaml_load.return_value = {
                'template': 'hyp-cluster',
                'namespace': 'test-namespace',
                'version': '1.0',
                'eks_cluster_name': 'test-cluster',
                'stage': 'gamma'
            }
            
            mock_stack_instance = Mock()
            mock_stack_instance.create.return_value = {'StackId': 'test-stack-id'}
            mock_cluster_stack.return_value = mock_stack_instance
            
            # Execute
            create_cluster_stack_helper('config.yaml', 'us-west-2', False)
            
            # Verify template and namespace were filtered out
            call_args = mock_cluster_stack.call_args[1]
            assert 'template' not in call_args
            assert 'namespace' not in call_args
            assert 'eks_cluster_name' in call_args
            assert 'stage' in call_args
    
    @patch('sagemaker.hyperpod.cli.commands.cluster_stack.HpClusterStack')
    @patch('yaml.safe_load')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_cluster_stack_helper_filters_none_values(self, mock_file, mock_exists, mock_yaml_load, mock_cluster_stack, mock_get_template, mock_read_text):
        """Test that None values are filtered out"""
        # Mock template methods
        mock_get_template.return_value = '{"Parameters": {}}'
        mock_read_text.return_value = 'Parameters: {}'
        
        # Setup mocks
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            'template': 'hyp-cluster',
            'eks_cluster_name': 'test-cluster',
            'optional_field': None,
            'required_field': 'value'
        }
        
        # Mock the stack instance and its create method to avoid AWS calls
        mock_stack_instance = Mock()
        mock_stack_instance.create.return_value = {'StackId': 'test-stack-id'}
        mock_cluster_stack.return_value = mock_stack_instance
        
        with patch('sagemaker.hyperpod.cli.commands.cluster_stack.logger') as mock_logger:
            from sagemaker.hyperpod.cli.commands.cluster_stack import create_cluster_stack_helper
            
            # Execute
            create_cluster_stack_helper('config.yaml', 'us-west-2', False)
            
            # Verify None values were filtered out
            call_args = mock_cluster_stack.call_args[1]
            assert 'optional_field' not in call_args
            assert 'required_field' in call_args