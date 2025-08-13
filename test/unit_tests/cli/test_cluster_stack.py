import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from sagemaker.hyperpod.cli.commands.cluster_stack import update_cluster


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