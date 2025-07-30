import unittest
from unittest.mock import patch, MagicMock, mock_open

import boto3

from sagemaker.hyperpod.cluster_management.hp_cluster_stack import HpClusterStack, CLUSTER_STACK_TEMPLATE_PACKAGE_NAME, CLUSTER_CREATION_TEMPLATE_FILE_NAME


class TestHpClusterStack(unittest.TestCase):
    @patch('uuid.uuid4')
    @patch('boto3.session.Session')
    @patch('boto3.client')
    @patch('importlib.resources.files')
    @patch('builtins.open', new_callable=mock_open, read_data="template: data")
    @patch('yaml.safe_load')
    @patch('json.dumps')
    def test_create(self, mock_json_dumps, mock_yaml_load, mock_file_open, 
                   mock_files, mock_boto3_client, mock_boto3_session, mock_uuid):
        # Setup mocks
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = MagicMock(return_value="12345-67890-abcde")
        
        mock_region = "us-west-2"
        mock_boto3_session.return_value.region_name = mock_region
        
        mock_cf_client = MagicMock()
        mock_boto3_client.return_value = mock_cf_client
        
        mock_template_path = MagicMock()
        mock_files.return_value = MagicMock()
        mock_files.return_value.__truediv__.return_value = mock_template_path
        
        mock_yaml_data = {"Resources": {}}
        mock_yaml_load.return_value = mock_yaml_data
        
        mock_template_body = '{"Resources": {}}'
        mock_json_dumps.return_value = mock_template_body
        
        # Create test instance with sample data
        stack = HpClusterStack(
            stage="gamma",
            eks_cluster_name="test-cluster",
            create_eks_cluster_stack=True
        )
        
        # Call the method under test
        stack.create()
        
        # Verify mocks were called correctly
        mock_boto3_session.assert_called_once()
        mock_boto3_client.assert_called_once_with('cloudformation', region_name=mock_region)
        mock_files.assert_called_once_with(CLUSTER_STACK_TEMPLATE_PACKAGE_NAME)
        mock_files.return_value.__truediv__.assert_called_once_with(CLUSTER_CREATION_TEMPLATE_FILE_NAME)
        mock_file_open.assert_called_once_with(mock_template_path, 'r')
        mock_yaml_load.assert_called_once()
        mock_json_dumps.assert_called_once_with(mock_yaml_data, indent=2, ensure_ascii=False)
        
        # Expected parameters based on the actual _create_parameters implementation
        expected_params = [
            {'ParameterKey': 'Stage', 'ParameterValue': 'gamma'},
            {'ParameterKey': 'EKSClusterName', 'ParameterValue': 'test-cluster'},
            {'ParameterKey': 'CreateEKSClusterStack', 'ParameterValue': 'true'}
        ]
        
        # Verify create_stack was called with expected parameters
        mock_cf_client.create_stack.assert_called_once_with(
            StackName="HyperpodClusterStack-12345",
            TemplateBody=mock_template_body,
            Parameters=expected_params,
            Tags=[{'Key': 'Environment', 'Value': 'Development'}],
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
        )
