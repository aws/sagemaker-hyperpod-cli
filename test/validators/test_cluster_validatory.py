import unittest
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from hyperpod_cli.validators.cluster_validator import ClusterValidator


class TestClusterValidator(unittest.TestCase):
    def setUp(self):
        self.validator = ClusterValidator()
        self.mock_sm_client = MagicMock()

    @patch("boto3.client")
    def test_validate_cluster_and_get_eks_arn_success(self, mock_boto3_client):
        cluster_name = "my-cluster"
        eks_arn = "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"
        mock_describe_cluster_response = {"Orchestrator": {"Eks": {"ClusterArn": eks_arn}}}
        mock_sm_client = MagicMock()
        mock_sm_client.describe_cluster.return_value = mock_describe_cluster_response
        mock_boto3_client.return_value = mock_sm_client

        result = self.validator.validate_cluster_and_get_eks_arn(cluster_name, mock_sm_client)
        self.assertEqual(result, eks_arn)

    @patch("boto3.client")
    def test_validate_cluster_and_get_eks_arn_non_eks_cluster(self, mock_boto3_client):
        cluster_name = "my-cluster"
        mock_describe_cluster_response = {"Orchestrator": "SomeOtherOrchestrator"}
        mock_sm_client = MagicMock()
        mock_sm_client.describe_cluster.return_value = mock_describe_cluster_response
        mock_boto3_client.return_value = mock_sm_client

        result = self.validator.validate_cluster_and_get_eks_arn(cluster_name, mock_sm_client)
        self.assertIsNone(result)

    @patch("boto3.client")
    def test_validate_cluster_and_get_eks_arn_resource_not_found(self, mock_boto3_client):
        cluster_name = "my-cluster"
        mock_sm_client = MagicMock()
        mock_sm_client.describe_cluster.side_effect = ClientError(
            error_response={"Error": {"Code": "ResourceNotFoundException"}},
            operation_name="DescribeCluster",
        )
        mock_boto3_client.return_value = mock_sm_client

        result = self.validator.validate_cluster_and_get_eks_arn(cluster_name, mock_sm_client)
        self.assertIsNone(result)

    @patch("boto3.client")
    def test_validate_cluster_and_get_eks_arn_other_client_error(self, mock_boto3_client):
        cluster_name = "my-cluster"
        mock_sm_client = MagicMock()
        mock_sm_client.describe_cluster.side_effect = ClientError(
            error_response={"Error": {"Code": "SomeOtherError"}}, operation_name="DescribeCluster"
        )
        mock_boto3_client.return_value = mock_sm_client

        result = self.validator.validate_cluster_and_get_eks_arn(cluster_name, mock_sm_client)
        self.assertIsNone(result)

    @patch("boto3.client")
    def test_validate_cluster_and_get_eks_arn_other_exception(self, mock_boto3_client):
        cluster_name = "my-cluster"
        mock_sm_client = MagicMock()
        mock_sm_client.describe_cluster.side_effect = Exception("Some other exception")
        mock_boto3_client.return_value = mock_sm_client

        result = self.validator.validate_cluster_and_get_eks_arn(cluster_name, mock_sm_client)
        self.assertIsNone(result)
