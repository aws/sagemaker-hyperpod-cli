# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
import unittest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from botocore.exceptions import ClientError
from sagemaker.hyperpod.cli.commands.cluster import describe_cluster


class DescribeClusterTest(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch('sagemaker.hyperpod.cli.commands.cluster.get_sagemaker_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster.boto3.Session')
    @patch('sagemaker.hyperpod.cli.commands.cluster.setup_logger')
    def test_describe_cluster_happy_case(self, mock_setup_logger, mock_session, mock_get_sagemaker_client):
        """Test successful cluster description with valid cluster name."""
        # Arrange
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger

        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        mock_sm_client = Mock()
        mock_get_sagemaker_client.return_value = mock_sm_client

        # Mock successful cluster response
        cluster_response = {
            "ClusterArn": "arn:aws:sagemaker:us-east-2:123456789012:cluster/test-cluster",
            "ClusterName": "test-cluster",
            "ClusterStatus": "InService",
            "CreationTime": "2023-09-23T14:35:38.223000+00:00",
            "InstanceGroups": [
                {
                    "InstanceGroupName": "controller-group",
                    "InstanceType": "ml.t3.medium",
                    "CurrentCount": 1,
                    "TargetCount": 1
                }
            ],
            "VpcConfig": {
                "SecurityGroupIds": ["sg-1234567890abcdef0"],
                "Subnets": ["subnet-1234567890abcdef0"]
            },
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-east-2:123456789012:cluster/eks-cluster"
                }
            }
        }

        mock_sm_client.describe_cluster.return_value = cluster_response

        # Act
        result = self.runner.invoke(describe_cluster, ["test-cluster"])

        # Assert
        assert result.exit_code == 0
        mock_sm_client.describe_cluster.assert_called_once_with(ClusterName="test-cluster")
        assert "📋 Cluster Details for: test-cluster" in result.output
        assert "test-cluster" in result.output
        assert "InService" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster.get_sagemaker_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster.boto3.Session')
    @patch('sagemaker.hyperpod.cli.commands.cluster.setup_logger')
    def test_describe_cluster_with_region_flag(self, mock_setup_logger, mock_session, mock_get_sagemaker_client):
        """Test cluster description with region flag specified."""
        # Arrange
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger

        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        mock_sm_client = Mock()
        mock_get_sagemaker_client.return_value = mock_sm_client

        # Mock successful cluster response
        cluster_response = {
            "ClusterArn": "arn:aws:sagemaker:us-west-2:123456789012:cluster/test-cluster",
            "ClusterName": "test-cluster",
            "ClusterStatus": "InService",
            "CreationTime": "2023-09-23T14:35:38.223000+00:00",
            "InstanceGroups": [
                {
                    "InstanceGroupName": "worker-group",
                    "InstanceType": "ml.p4d.24xlarge",
                    "CurrentCount": 2,
                    "TargetCount": 2
                }
            ]
        }

        mock_sm_client.describe_cluster.return_value = cluster_response

        # Act
        result = self.runner.invoke(describe_cluster, ["test-cluster", "--region", "us-west-2"])

        # Assert
        assert result.exit_code == 0

        # Verify that boto3.Session was called with the correct region
        mock_session.assert_called_with(region_name="us-west-2")
        mock_sm_client.describe_cluster.assert_called_once_with(ClusterName="test-cluster")
        assert "📋 Cluster Details for: test-cluster" in result.output
        assert "test-cluster" in result.output
        assert "InService" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster.get_sagemaker_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster.boto3.Session')
    @patch('sagemaker.hyperpod.cli.commands.cluster.setup_logger')
    def test_describe_cluster_unknown_cluster_name(self, mock_setup_logger, mock_session, mock_get_sagemaker_client):
        """Test cluster description with unknown/non-existent cluster name."""
        # Arrange
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger

        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        mock_sm_client = Mock()
        mock_get_sagemaker_client.return_value = mock_sm_client

        # Mock cluster not found exception
        error_response = {
            'Error': {
                'Code': 'ResourceNotFound',
                'Message': 'Cluster does not exist'
            }
        }
        mock_sm_client.describe_cluster.side_effect = ClientError(
            error_response, 'DescribeCluster'
        )

        # Act
        result = self.runner.invoke(describe_cluster, ["unknown-cluster"])

        # Assert
        assert result.exit_code == 1
        mock_sm_client.describe_cluster.assert_called_once_with(ClusterName="unknown-cluster")
        # Should show the error message
        assert "❌ Cluster 'unknown-cluster' not found" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster.get_sagemaker_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster.boto3.Session')
    @patch('sagemaker.hyperpod.cli.commands.cluster.setup_logger')
    def test_describe_cluster_access_denied(self, mock_setup_logger, mock_session, mock_get_sagemaker_client):
        """Test cluster description with access denied error."""
        # Arrange
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger

        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        mock_sm_client = Mock()
        mock_get_sagemaker_client.return_value = mock_sm_client

        # Mock access denied exception
        error_response = {
            'Error': {
                'Code': 'AccessDenied',
                'Message': 'User is not authorized to perform this action'
            }
        }
        mock_sm_client.describe_cluster.side_effect = ClientError(
            error_response, 'DescribeCluster'
        )

        # Act
        result = self.runner.invoke(describe_cluster, ["test-cluster"])

        # Assert
        assert result.exit_code == 1
        mock_sm_client.describe_cluster.assert_called_once_with(ClusterName="test-cluster")
        # Should show the access denied message
        assert "❌ Access denied. Check AWS permissions" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster.get_sagemaker_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster.boto3.Session')
    @patch('sagemaker.hyperpod.cli.commands.cluster.setup_logger')
    def test_describe_cluster_generic_error(self, mock_setup_logger, mock_session, mock_get_sagemaker_client):
        """Test cluster description with generic error."""
        # Arrange
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger

        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        mock_sm_client = Mock()
        mock_get_sagemaker_client.return_value = mock_sm_client

        # Mock generic exception
        mock_sm_client.describe_cluster.side_effect = Exception("Unexpected error occurred")

        # Act
        result = self.runner.invoke(describe_cluster, ["test-cluster"])

        # Assert
        assert result.exit_code == 1
        mock_sm_client.describe_cluster.assert_called_once_with(ClusterName="test-cluster")
        # Should show the generic error message
        assert "❌ Error describing cluster: Unexpected error occurred" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster.get_sagemaker_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster.boto3.Session')
    @patch('sagemaker.hyperpod.cli.commands.cluster.setup_logger')
    def test_describe_cluster_with_debug_flag(self, mock_setup_logger, mock_session, mock_get_sagemaker_client):
        """Test cluster description with debug flag enabled."""
        # Arrange
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger

        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        mock_sm_client = Mock()
        mock_get_sagemaker_client.return_value = mock_sm_client

        # Mock successful cluster response
        cluster_response = {
            "ClusterArn": "arn:aws:sagemaker:us-east-2:123456789012:cluster/test-cluster",
            "ClusterName": "test-cluster",
            "ClusterStatus": "InService"
        }

        mock_sm_client.describe_cluster.return_value = cluster_response

        # Act
        result = self.runner.invoke(describe_cluster, ["test-cluster", "--debug"])

        # Assert
        assert result.exit_code == 0
        mock_sm_client.describe_cluster.assert_called_once_with(ClusterName="test-cluster")
        assert "📋 Cluster Details for: test-cluster" in result.output

    @patch('sagemaker.hyperpod.cli.commands.cluster.get_sagemaker_client')
    @patch('sagemaker.hyperpod.cli.commands.cluster.boto3.Session')
    @patch('sagemaker.hyperpod.cli.commands.cluster.setup_logger')
    def test_describe_cluster_empty_response(self, mock_setup_logger, mock_session, mock_get_sagemaker_client):
        """Test cluster description with empty response."""
        # Arrange
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger

        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        mock_sm_client = Mock()
        mock_get_sagemaker_client.return_value = mock_sm_client

        # Mock empty cluster response
        cluster_response = {}

        mock_sm_client.describe_cluster.return_value = cluster_response

        # Act
        result = self.runner.invoke(describe_cluster, ["test-cluster"])

        # Assert
        assert result.exit_code == 0
        mock_sm_client.describe_cluster.assert_called_once_with(ClusterName="test-cluster")
        assert "📋 Cluster Details for: test-cluster" in result.output
        assert "No cluster data available" in result.output


if __name__ == "__main__":
    unittest.main()