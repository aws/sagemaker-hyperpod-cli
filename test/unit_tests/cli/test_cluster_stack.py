import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from datetime import datetime
from sagemaker.hyperpod.cli.commands.cluster_stack import update_cluster, list_cluster_stacks


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
            'hyp-cluster',  # template argument
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
            'hyp-cluster',  # template argument
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
        mock_hp_cluster_list.assert_called_once_with(region=None)

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
        mock_hp_cluster_list.assert_called_once_with(region='us-east-1')

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
