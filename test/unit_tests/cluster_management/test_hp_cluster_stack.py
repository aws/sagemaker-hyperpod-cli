import unittest
import json
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


class TestHpClusterStackArrayConversion(unittest.TestCase):
    
    def test_create_parameters_converts_instance_group_settings_list(self):
        """Test conversion of instance_group_settings from list to numbered parameters"""
        settings = [
            {"instanceType": "ml.g5.xlarge", "instanceCount": 1},
            {"instanceType": "ml.p4d.24xlarge", "instanceCount": 2}
        ]
        
        stack = HpClusterStack.model_construct(instance_group_settings=settings)
        parameters = stack._create_parameters()
        
        # Find the converted parameters
        ig_params = [p for p in parameters if p['ParameterKey'].startswith('InstanceGroupSettings')]
        
        self.assertEqual(len(ig_params), 2)
        self.assertEqual(ig_params[0]['ParameterKey'], 'InstanceGroupSettings1')
        self.assertEqual(ig_params[1]['ParameterKey'], 'InstanceGroupSettings2')
        
        # Verify JSON serialization
        self.assertEqual(json.loads(ig_params[0]['ParameterValue']), settings[0])
        self.assertEqual(json.loads(ig_params[1]['ParameterValue']), settings[1])
    
    def test_create_parameters_converts_rig_settings_list(self):
        """Test conversion of rig_settings from list to numbered parameters"""
        settings = [
            {"restrictedInstanceType": "ml.g5.xlarge"},
            {"restrictedInstanceType": "ml.p4d.24xlarge"}
        ]
        
        stack = HpClusterStack.model_construct(rig_settings=settings)
        parameters = stack._create_parameters()
        
        # Find the converted parameters
        rig_params = [p for p in parameters if p['ParameterKey'].startswith('RigSettings')]
        
        self.assertEqual(len(rig_params), 2)
        self.assertEqual(rig_params[0]['ParameterKey'], 'RigSettings1')
        self.assertEqual(rig_params[1]['ParameterKey'], 'RigSettings2')
        
        # Verify JSON serialization
        self.assertEqual(json.loads(rig_params[0]['ParameterValue']), settings[0])
        self.assertEqual(json.loads(rig_params[1]['ParameterValue']), settings[1])
    
    def test_create_parameters_handles_json_string_instance_group_settings(self):
        """Test conversion of instance_group_settings from JSON string to numbered parameters"""
        settings_json = '[{"instanceType": "ml.g5.xlarge", "instanceCount": 1}]'
        
        stack = HpClusterStack(instance_group_settings=settings_json)
        parameters = stack._create_parameters()
        
        # Find the converted parameters
        ig_params = [p for p in parameters if p['ParameterKey'].startswith('InstanceGroupSettings')]
        
        self.assertEqual(len(ig_params), 1)
        self.assertEqual(ig_params[0]['ParameterKey'], 'InstanceGroupSettings1')
        self.assertEqual(json.loads(ig_params[0]['ParameterValue']), {"instanceType": "ml.g5.xlarge", "instanceCount": 1})
    
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