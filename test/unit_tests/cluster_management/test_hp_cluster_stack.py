import unittest
import json
from unittest.mock import patch, MagicMock, mock_open
from botocore.exceptions import ClientError
import boto3

from sagemaker.hyperpod.cluster_management.hp_cluster_stack import HpClusterStack

class TestHpClusterStack(unittest.TestCase):
    @patch('uuid.uuid4')
    @patch('boto3.session.Session')
    @patch('boto3.client')
    def test_create(self, mock_boto3_client, mock_boto3_session, mock_uuid):
        # Setup mocks
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = MagicMock(return_value="12345-67890-abcde")
        
        mock_region = "us-west-2"
        mock_boto3_session.return_value.region_name = mock_region
        
        # Mock clients
        mock_cf_client = MagicMock()
        mock_s3_client = MagicMock()
        mock_sts_client = MagicMock()
        
        def mock_client_factory(service_name, **kwargs):
            if service_name == 'cloudformation':
                return mock_cf_client
            elif service_name == 's3':
                return mock_s3_client
            elif service_name == 'sts':
                return mock_sts_client
            return MagicMock()
        
        mock_boto3_client.side_effect = mock_client_factory
        
        # Mock STS response
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        
        # Create test instance with sample data
        stack = HpClusterStack(
            stage="gamma",
            eks_cluster_name="test-cluster",
            create_eks_cluster_stack=True
        )
        
        mock_create_response = {'StackId': 'test-stack-id'}
        mock_cf_client.create_stack.return_value = mock_create_response
        
        # Mock the describe response that create() returns
        mock_describe_response = {'Stacks': [{'StackId': 'test-stack-id', 'StackStatus': 'CREATE_IN_PROGRESS'}]}
        mock_cf_client.describe_stacks.return_value = mock_describe_response
        
        # Call the method under test
        result = stack.create()
        
        # Verify the result is the describe response
        self.assertEqual(result, mock_describe_response)
        
        # Verify create_stack was called
        self.assertTrue(mock_cf_client.create_stack.called)

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
        self.assertIn('HyperPodClusterName', param_keys)
        self.assertIn('CreateVPCStack', param_keys)
        
        # Verify boolean conversion
        vpc_param = next(p for p in other_params if p['ParameterKey'] == 'CreateVPCStack')
        self.assertEqual(vpc_param['ParameterValue'], 'true')

class TestHpClusterStackInit(unittest.TestCase):
    """Test HpClusterStack __init__ method array conversion"""
    
    def test_init_converts_arrays_to_json_strings(self):
        """Test that __init__ converts array values to JSON strings"""
        data = {
            'tags': [{'Key': 'Environment', 'Value': 'Test'}],
            'availability_zone_ids': ['us-east-1a', 'us-east-1b'],
            'hyperpod_cluster_name': 'test-cluster',
            'storage_capacity': 1200
        }
        
        stack = HpClusterStack(**data)
        
        # Arrays should be converted to JSON strings
        self.assertEqual(stack.tags, '[{"Key": "Environment", "Value": "Test"}]')
        self.assertEqual(stack.availability_zone_ids, '["us-east-1a", "us-east-1b"]')
        
        # Other types should remain unchanged
        self.assertEqual(stack.hyperpod_cluster_name, 'test-cluster')
        self.assertEqual(stack.storage_capacity, 1200)
    
    def test_init_handles_empty_arrays(self):
        """Test that empty arrays are converted to empty JSON arrays"""
        data = {'tags': []}
        
        stack = HpClusterStack(**data)
        
        self.assertEqual(stack.tags, '[]')
    
    def test_init_handles_no_arrays(self):
        """Test that __init__ works normally when no arrays are present"""
        data = {
            'hyperpod_cluster_name': 'test-cluster',
            'stage': 'gamma'
        }
        
        stack = HpClusterStack(**data)
        
        self.assertEqual(stack.hyperpod_cluster_name, 'test-cluster')
        self.assertEqual(stack.stage, 'gamma')


class TestHpClusterStackParseTags(unittest.TestCase):
    """Test HpClusterStack _parse_tags method"""
    
    def test_parse_tags_valid_json_array(self):
        """Test parsing valid JSON array of tags"""
        tags_json = '[{"Key": "Environment", "Value": "Test"}, {"Key": "Project", "Value": "HyperPod"}]'
        stack = HpClusterStack(tags=tags_json)
        
        result = stack._parse_tags()
        
        expected = [
            {"Key": "Environment", "Value": "Test"},
            {"Key": "Project", "Value": "HyperPod"}
        ]
        self.assertEqual(result, expected)
    
    def test_parse_tags_empty_string(self):
        """Test parsing empty tags string returns empty list"""
        stack = HpClusterStack(tags="")
        
        result = stack._parse_tags()
        
        self.assertEqual(result, [])
    
    def test_parse_tags_none_value(self):
        """Test parsing None tags returns empty list"""
        stack = HpClusterStack(tags=None)
        
        result = stack._parse_tags()
        
        self.assertEqual(result, [])
    
    def test_parse_tags_invalid_json(self):
        """Test parsing invalid JSON returns empty list"""
        stack = HpClusterStack(tags="invalid json")
        
        result = stack._parse_tags()
        
        self.assertEqual(result, [])
    
    def test_parse_tags_empty_json_array(self):
        """Test parsing empty JSON array returns empty list"""
        stack = HpClusterStack(tags="[]")
        
        result = stack._parse_tags()
        
        self.assertEqual(result, [])


class TestHpClusterStackGetTemplate(unittest.TestCase):
    """Test HpClusterStack get_template method using package instead of S3"""
    
    @patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.importlib.resources.read_text')
    @patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.yaml.safe_load')
    def test_get_template_from_package(self, mock_yaml_load, mock_read_text):
        """Test get_template reads from package instead of S3"""
        mock_yaml_content = "Parameters:\n  TestParam:\n    Type: String"
        mock_read_text.return_value = mock_yaml_content
        
        mock_yaml_data = {"Parameters": {"TestParam": {"Type": "String"}}}
        mock_yaml_load.return_value = mock_yaml_data
        
        result = HpClusterStack.get_template()
        
        # Verify package resource was read
        mock_read_text.assert_called_once_with('hyperpod_cluster_stack_template', 'creation_template.yaml')
        mock_yaml_load.assert_called_once_with(mock_yaml_content)
        
        # Verify JSON output
        expected_json = json.dumps(mock_yaml_data, indent=2, ensure_ascii=False)
        self.assertEqual(result, expected_json)
    
    @patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.importlib.resources.read_text')
    def test_get_template_handles_package_error(self, mock_read_text):
        """Test get_template handles package read errors"""
        mock_read_text.side_effect = FileNotFoundError("Template not found")
        
        with self.assertRaises(RuntimeError) as context:
            HpClusterStack.get_template()
        
        self.assertIn("Failed to load template from package", str(context.exception))
