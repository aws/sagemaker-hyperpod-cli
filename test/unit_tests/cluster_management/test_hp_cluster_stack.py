import unittest
import json
from unittest.mock import patch, MagicMock, mock_open
from botocore.exceptions import ClientError

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

    @patch('boto3.session.Session')
    @patch('boto3.client')
    def test_describe_success(self, mock_boto3_client, mock_boto3_session):
        mock_region = "us-west-2"
        mock_boto3_session.return_value.region_name = mock_region
        
        mock_cf_client = MagicMock()
        mock_boto3_client.return_value = mock_cf_client
        
        mock_response = {'Stacks': [{'StackName': 'test-stack', 'StackStatus': 'CREATE_COMPLETE'}]}
        mock_cf_client.describe_stacks.return_value = mock_response
        
        result = HpClusterStack.describe('test-stack')
        
        mock_boto3_client.assert_called_once_with('cloudformation', region_name=mock_region)
        mock_cf_client.describe_stacks.assert_called_once_with(StackName='test-stack')
        self.assertEqual(result, mock_response)

    @patch('boto3.session.Session')
    @patch('boto3.client')
    def test_describe_access_denied(self, mock_boto3_client, mock_boto3_session):
        mock_region = "us-west-2"
        mock_boto3_session.return_value.region_name = mock_region
        
        mock_cf_client = MagicMock()
        mock_cf_client.exceptions.ClientError = ClientError
        mock_boto3_client.return_value = mock_cf_client
        
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}}
        mock_cf_client.describe_stacks.side_effect = ClientError(error_response, 'DescribeStacks')
        
        with self.assertRaises(ValueError):
            HpClusterStack.describe('test-stack')

    @patch('boto3.session.Session')
    @patch('boto3.client')
    def test_list_success(self, mock_boto3_client, mock_boto3_session):
        mock_region = "us-west-2"
        mock_boto3_session.return_value.region_name = mock_region
        
        mock_cf_client = MagicMock()
        mock_boto3_client.return_value = mock_cf_client
        
        mock_response = {'StackSummaries': [{'StackName': 'stack1'}, {'StackName': 'stack2'}]}
        mock_cf_client.list_stacks.return_value = mock_response
        
        result = HpClusterStack.list()
        
        mock_boto3_client.assert_called_once_with('cloudformation', region_name=mock_region)
        mock_cf_client.list_stacks.assert_called_once()
        self.assertEqual(result, mock_response)

    @patch('boto3.session.Session')
    @patch('boto3.client')
    def test_list_access_denied(self, mock_boto3_client, mock_boto3_session):
        from botocore.exceptions import ClientError
        
        mock_region = "us-west-2"
        mock_boto3_session.return_value.region_name = mock_region
        
        mock_cf_client = MagicMock()
        mock_cf_client.exceptions.ClientError = ClientError
        mock_boto3_client.return_value = mock_cf_client
        
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}}
        mock_cf_client.list_stacks.side_effect = ClientError(error_response, 'ListStacks')
        
        with self.assertRaises(ValueError):
            HpClusterStack.list()

    @patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.create_boto3_client')
    def test_get_status_success(self, mock_create_client):
        """Test get_status method returns stack status successfully"""
        mock_cf_client = MagicMock()
        mock_create_client.return_value = mock_cf_client
        
        mock_response = {
            'Stacks': [{
                'StackName': 'test-stack',
                'StackStatus': 'CREATE_COMPLETE',
                'CreationTime': '2023-01-01T00:00:00Z'
            }]
        }
        mock_cf_client.describe_stacks.return_value = mock_response
        
        # Create stack instance with stack_name set
        stack = HpClusterStack(stage="test")
        stack.stack_name = "test-stack"
        
        result = stack.get_status()
        
        mock_create_client.assert_called_once_with('cloudformation', region_name=None)
        mock_cf_client.describe_stacks.assert_called_once_with(StackName='test-stack')
        self.assertEqual(result, 'CREATE_COMPLETE')

    @patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.create_boto3_client')
    def test_get_status_with_region(self, mock_create_client):
        """Test get_status method with explicit region parameter"""
        mock_cf_client = MagicMock()
        mock_create_client.return_value = mock_cf_client
        
        mock_response = {
            'Stacks': [{
                'StackName': 'test-stack',
                'StackStatus': 'UPDATE_IN_PROGRESS'
            }]
        }
        mock_cf_client.describe_stacks.return_value = mock_response
        
        stack = HpClusterStack(stage="test")
        stack.stack_name = "test-stack"
        
        result = stack.get_status(region="us-west-2")
        
        mock_create_client.assert_called_once_with('cloudformation', region_name="us-west-2")
        self.assertEqual(result, 'UPDATE_IN_PROGRESS')

    def test_get_status_no_stack_name(self):
        """Test get_status raises ValueError when stack_name is not set"""
        stack = HpClusterStack(stage="test")
        
        with self.assertRaises(ValueError) as context:
            stack.get_status()
        
        self.assertIn("Stack must be created first", str(context.exception))

    @patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.create_boto3_client')
    def test_get_status_stack_not_found(self, mock_create_client):
        """Test get_status handles stack not found error"""
        mock_cf_client = MagicMock()
        mock_create_client.return_value = mock_cf_client
        
        error_response = {'Error': {'Code': 'ValidationError', 'Message': 'Stack does not exist'}}
        mock_cf_client.describe_stacks.side_effect = ClientError(error_response, 'DescribeStacks')
        mock_cf_client.exceptions.ClientError = ClientError
        
        stack = HpClusterStack(stage="test")
        stack.stack_name = "nonexistent-stack"
        
        with self.assertRaises(ValueError):
            stack.get_status()

    @patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.create_boto3_client')
    def test_check_status_success(self, mock_create_client):
        """Test check_status static method returns stack status successfully"""
        mock_cf_client = MagicMock()
        mock_create_client.return_value = mock_cf_client
        
        mock_response = {
            'Stacks': [{
                'StackName': 'test-stack',
                'StackStatus': 'DELETE_COMPLETE',
                'DeletionTime': '2023-01-01T00:00:00Z'
            }]
        }
        mock_cf_client.describe_stacks.return_value = mock_response
        
        result = HpClusterStack.check_status('test-stack')
        
        mock_create_client.assert_called_once_with('cloudformation', region_name=None)
        mock_cf_client.describe_stacks.assert_called_once_with(StackName='test-stack')
        self.assertEqual(result, 'DELETE_COMPLETE')

    @patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.create_boto3_client')
    def test_check_status_with_region(self, mock_create_client):
        """Test check_status static method with explicit region parameter"""
        mock_cf_client = MagicMock()
        mock_create_client.return_value = mock_cf_client
        
        mock_response = {
            'Stacks': [{
                'StackName': 'test-stack',
                'StackStatus': 'ROLLBACK_COMPLETE'
            }]
        }
        mock_cf_client.describe_stacks.return_value = mock_response
        
        result = HpClusterStack.check_status('test-stack', region="us-west-2")
        
        mock_create_client.assert_called_once_with('cloudformation', region_name="us-west-2")
        self.assertEqual(result, 'ROLLBACK_COMPLETE')

    @patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.create_boto3_client')
    def test_check_status_stack_not_found(self, mock_create_client):
        """Test check_status handles stack not found error"""
        mock_cf_client = MagicMock()
        mock_create_client.return_value = mock_cf_client
        
        error_response = {'Error': {'Code': 'ValidationError', 'Message': 'Stack does not exist'}}
        mock_cf_client.describe_stacks.side_effect = ClientError(error_response, 'DescribeStacks')
        mock_cf_client.exceptions.ClientError = ClientError
        
        with self.assertRaises(ValueError):
            HpClusterStack.check_status('nonexistent-stack')

    @patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.create_boto3_client')
    def test_check_status_access_denied(self, mock_create_client):
        """Test check_status handles access denied error"""
        mock_cf_client = MagicMock()
        mock_create_client.return_value = mock_cf_client
        
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}}
        mock_cf_client.describe_stacks.side_effect = ClientError(error_response, 'DescribeStacks')
        mock_cf_client.exceptions.ClientError = ClientError
        
        with self.assertRaises(ValueError):
            HpClusterStack.check_status('test-stack')

    @patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.create_boto3_client')
    def test_get_status_empty_stacks_response(self, mock_create_client):
        """Test get_status handles empty stacks response"""
        mock_cf_client = MagicMock()
        mock_create_client.return_value = mock_cf_client
        
        mock_response = {'Stacks': []}
        mock_cf_client.describe_stacks.return_value = mock_response
        
        stack = HpClusterStack(stage="test")
        stack.stack_name = "test-stack"
        
        result = stack.get_status()
        self.assertIsNone(result)

    @patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.create_boto3_client')
    def test_check_status_empty_stacks_response(self, mock_create_client):
        """Test check_status handles empty stacks response"""
        mock_cf_client = MagicMock()
        mock_create_client.return_value = mock_cf_client
        
        mock_response = {'Stacks': []}
        mock_cf_client.describe_stacks.return_value = mock_response
        
        result = HpClusterStack.check_status('test-stack')
        self.assertIsNone(result)


class TestHpClusterStackArrayConversion(unittest.TestCase):
    
    def test_create_parameters_converts_instance_group_settings_list(self):
        """Test conversion of instance_group_settings from list to numbered parameters"""
        settings = [
            {"instance_type": "ml.g5.xlarge", "instance_count": 1},
            {"instance_type": "ml.p4d.24xlarge", "instance_count": 2}
        ]
        
        stack = HpClusterStack.model_construct(instance_group_settings=settings)
        parameters = stack._create_parameters()
        
        # Find the converted parameters
        ig_params = [p for p in parameters if p['ParameterKey'].startswith('InstanceGroupSettings')]
        
        self.assertEqual(len(ig_params), 2)
        self.assertEqual(ig_params[0]['ParameterKey'], 'InstanceGroupSettings1')
        self.assertEqual(ig_params[1]['ParameterKey'], 'InstanceGroupSettings2')
        
        # Verify JSON serialization
        self.assertEqual(json.loads(ig_params[0]['ParameterValue']), {"InstanceType": "ml.g5.xlarge", "InstanceCount": 1})
        self.assertEqual(json.loads(ig_params[1]['ParameterValue']), {"InstanceType": "ml.p4d.24xlarge", "InstanceCount": 2})
    
    def test_create_parameters_converts_rig_settings_list(self):
        """Test conversion of rig_settings from list to numbered parameters"""
        settings = [
            {"restricted_instance_type": "ml.g5.xlarge"},
            {"restricted_instance_type": "ml.p4d.24xlarge"}
        ]
        
        stack = HpClusterStack.model_construct(rig_settings=settings)
        parameters = stack._create_parameters()
        
        # Find the converted parameters
        rig_params = [p for p in parameters if p['ParameterKey'].startswith('RigSettings')]
        
        self.assertEqual(len(rig_params), 2)
        self.assertEqual(rig_params[0]['ParameterKey'], 'RigSettings1')
        self.assertEqual(rig_params[1]['ParameterKey'], 'RigSettings2')
        
        # Verify JSON serialization
        self.assertEqual(json.loads(rig_params[0]['ParameterValue']), {"RestrictedInstanceType": "ml.g5.xlarge"})
        self.assertEqual(json.loads(rig_params[1]['ParameterValue']), {"RestrictedInstanceType": "ml.p4d.24xlarge"})
    
    def test_create_parameters_handles_json_string_instance_group_settings(self):
        """Test conversion of instance_group_settings from JSON string to numbered parameters"""
        settings_json = '[{"instance_type": "ml.g5.xlarge", "instance_count": 1}]'
        
        stack = HpClusterStack(instance_group_settings=settings_json)
        parameters = stack._create_parameters()
        
        # Find the converted parameters
        ig_params = [p for p in parameters if p['ParameterKey'].startswith('InstanceGroupSettings')]
        
        self.assertEqual(len(ig_params), 1)
        self.assertEqual(ig_params[0]['ParameterKey'], 'InstanceGroupSettings1')
        self.assertEqual(json.loads(ig_params[0]['ParameterValue']), {"InstanceType": "ml.g5.xlarge", "InstanceCount": 1})
    
    def test_create_parameters_handles_malformed_json_gracefully(self):
        """Test that malformed JSON strings are handled gracefully"""
        malformed_json = 'invalid json string'
        
        stack = HpClusterStack(instance_group_settings=malformed_json)
        parameters = stack._create_parameters()
        
        # Should not create any InstanceGroupSettings parameters for malformed JSON
        ig_params = [p for p in parameters if p['ParameterKey'].startswith('InstanceGroupSettings')]
        self.assertEqual(len(ig_params), 0)
    
    def test_create_parameters_handles_empty_arrays(self):
        """Test that empty arrays don't create parameters"""
        stack = HpClusterStack.model_construct(instance_group_settings=[], rig_settings=[])
        parameters = stack._create_parameters()
        
        # Should not create any array-related parameters
        ig_params = [p for p in parameters if p['ParameterKey'].startswith('InstanceGroupSettings')]
        rig_params = [p for p in parameters if p['ParameterKey'].startswith('RigSettings')]
        
        self.assertEqual(len(ig_params), 0)
        self.assertEqual(len(rig_params), 0)
    
    def test_create_parameters_preserves_other_fields(self):
        """Test that other fields are still processed normally"""
        stack = HpClusterStack.model_construct(
            hyperpod_cluster_name="test-cluster",
            instance_group_settings=[{"instanceType": "ml.g5.xlarge"}],
            create_vpc_stack=True
        )
        parameters = stack._create_parameters()
        
        # Find non-array parameters
        other_params = [p for p in parameters if not p['ParameterKey'].startswith(('InstanceGroupSettings', 'RigSettings'))]
        
        # Should have the other fields
        param_keys = [p['ParameterKey'] for p in other_params]
        self.assertIn('HyperpodClusterName', param_keys)
        self.assertIn('CreateVPCStack', param_keys)
        
        # Verify boolean conversion
        vpc_param = next(p for p in other_params if p['ParameterKey'] == 'CreateVPCStack')
        self.assertEqual(vpc_param['ParameterValue'], 'true')