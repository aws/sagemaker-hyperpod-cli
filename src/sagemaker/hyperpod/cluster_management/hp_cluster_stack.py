import importlib.resources
import json
import logging
import uuid
from typing import Optional
import click
import yaml
from sagemaker.hyperpod.cluster_management.config.hp_cluster_stack_config import _ClusterStackBase
from sagemaker.hyperpod.common.utils import create_boto3_client

CLUSTER_CREATION_TEMPLATE_FILE_NAME = "creation_template.yaml"
CLUSTER_STACK_TEMPLATE_PACKAGE_NAME = "hyperpod_cluster_stack_template"

CAPABILITIES_FOR_STACK_CREATION = [
'CAPABILITY_IAM',
'CAPABILITY_NAMED_IAM'
]
log = logging.getLogger()


class HpClusterStack(_ClusterStackBase):

    @staticmethod
    def get_template() -> str:
        files = importlib.resources.files(CLUSTER_STACK_TEMPLATE_PACKAGE_NAME)
        template_file = files / CLUSTER_CREATION_TEMPLATE_FILE_NAME
        return _yaml_to_json_string(template_file)


    def create(self,
               region: Optional[str] = None):
        cf = create_boto3_client('cloudformation', region_name=region)

        # Convert the input object to CloudFormation parameters
        parameters = self._create_parameters()

        template_body = HpClusterStack.get_template()
        stack_name = f"HyperpodClusterStack-{str(uuid.uuid4())[:5]}"
        try:
            response = cf.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=parameters,
                Tags=self.tags or [{
                        'Key': 'Environment',
                        'Value': 'Development'
                    }],
                Capabilities=CAPABILITIES_FOR_STACK_CREATION
            )
            
            log.info(f"Stack creation initiated. Stack ID: {response['StackId']}")
            click.secho(f"Stack creation initiated. Stack ID: {response['StackId']}")

            self.stack_id = response['StackId']
            # Setting the stack name here to avoid calling multiple cloud formation APIs again
            self.stack_name = stack_name

            describe_response = self.describe(stack_name, region)

            return describe_response
        except Exception as e:
            log.error(f"Error creating stack: {e}")
            raise

    def _create_parameters(self):
        parameters = []
        for field_name, field_info in _ClusterStackBase.model_fields.items():
            value = getattr(self, field_name, None)
            if value is not None:
                # Handle array attributes that need to be converted to numbered parameters
                if field_name == 'instance_group_settings':
                    # Handle both list and JSON string formats
                    if isinstance(value, list):
                        settings_list = value
                    else:
                        # Parse JSON string to list
                        try:
                            settings_list = json.loads(str(value))
                        except (json.JSONDecodeError, TypeError):
                            settings_list = []
                    
                    for i, setting in enumerate(settings_list, 1):
                        formatted_setting = self._convert_nested_keys(setting)
                        parameters.append({
                            'ParameterKey': f'InstanceGroupSettings{i}',
                            'ParameterValue': json.dumps(formatted_setting) if isinstance(formatted_setting, (dict, list)) else str(formatted_setting)
                        })
                elif field_name == 'rig_settings':
                    # Handle both list and JSON string formats
                    if isinstance(value, list):
                        settings_list = value
                    else:
                        # Parse JSON string to list
                        try:
                            settings_list = json.loads(str(value))
                        except (json.JSONDecodeError, TypeError):
                            settings_list = []
                    
                    for i, setting in enumerate(settings_list, 1):
                        formatted_setting = self._convert_nested_keys(setting)
                        parameters.append({
                            'ParameterKey': f'RigSettings{i}',
                            'ParameterValue': json.dumps(formatted_setting) if isinstance(formatted_setting, (dict, list)) else str(formatted_setting)
                        })
                else:
                    # Convert boolean values to strings for CloudFormation
                    if isinstance(value, bool):
                        value = str(value).lower()

                    parameters.append({
                        'ParameterKey': self._snake_to_pascal(field_name),
                        'ParameterValue': str(value)
                    })
        return parameters

    def _convert_nested_keys(self, obj):
        """Convert nested JSON keys from snake_case to PascalCase."""
        if isinstance(obj, dict):
            return {self._snake_to_pascal(k): self._convert_nested_keys(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_nested_keys(item) for item in obj]
        return obj

    @staticmethod
    def _snake_to_pascal(snake_str):
        """Convert snake_case string to PascalCase."""
        if not snake_str:
            return snake_str
            
        # Handle specific cases
        if snake_str == "eks_cluster_name":
            return "EKSClusterName"
        elif snake_str == "create_eks_cluster_stack":
            return "CreateEKSClusterStack"
        elif snake_str == "create_hyperpod_cluster_stack":
            return "CreateHyperPodClusterStack"
        elif snake_str == "create_sagemaker_iam_role_stack":
            return "CreateSageMakerIAMRoleStack"
        elif snake_str == "create_vpc_stack":
            return "CreateVPCStack"
            
        # Default case: capitalize each word
        return ''.join(word.capitalize() for word in snake_str.split('_'))
    
    
    @staticmethod
    def describe(stack_name, region: Optional[str] = None):
        cf = create_boto3_client('cloudformation', region_name=region)
        
        try:
            response = cf.describe_stacks(StackName=stack_name)
            return response
        except cf.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            
            log.debug(f"CloudFormation error: {error_code} for operation on stack")
            
            if error_code in ['ValidationError', 'AccessDenied']:
                log.error("Stack operation failed - check stack name and permissions")
                raise ValueError("Stack not accessible")
            else:
                log.error("CloudFormation operation failed")
                raise RuntimeError("Stack operation failed")
        except Exception as e:
            log.error("Unexpected error during stack operation")
            raise RuntimeError("Stack operation failed")
    
    @staticmethod
    def list(region: Optional[str] = None):
        cf = create_boto3_client('cloudformation', region_name=region)
        
        try:
            response = cf.list_stacks()
            return response
        except cf.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            
            log.debug(f"CloudFormation error: {error_code} for list stacks operation")
            
            if error_code == 'AccessDenied':
                log.error("List stacks operation failed - check permissions")
                raise ValueError("Insufficient permissions to list stacks")
            else:
                log.error("CloudFormation list operation failed")
                raise RuntimeError("List stacks operation failed")
        except Exception as e:
            log.error("Unexpected error during list stacks operation")
            raise RuntimeError("List stacks operation failed")
    
    @staticmethod
    def _get_stack_status_helper(stack_name: str, region: Optional[str] = None):
        """Helper method to get stack status for any stack identifier."""        
        log.debug(f"Getting status for stack: {stack_name}")        
        stack_description = HpClusterStack.describe(stack_name, region)

        if stack_description.get('Stacks'):
            status = stack_description['Stacks'][0].get('StackStatus')
            log.debug(f"Stack {stack_name} status: {status}")
            return status
        
        log.debug(f"Stack {stack_name} not found")
        click.secho(f"Stack {stack_name} not found")
        return None

    def get_status(self, region: Optional[str] = None):
        """Get stack status using stored stack_id from create method."""
        if not self.stack_name:
            raise ValueError("Stack must be created first. Call create() before checking status.")
        return self._get_stack_status_helper(self.stack_name, region)
    
    @staticmethod
    def check_status(stack_name: str, region: Optional[str] = None):
        """Check stack status without instance. Static method for SDK usage."""
        return HpClusterStack._get_stack_status_helper(stack_name, region)


def _yaml_to_json_string(yaml_path):
    """Convert YAML file to JSON string"""
    with open(yaml_path, 'r') as file:
        yaml_data = yaml.safe_load(file)
    return json.dumps(yaml_data, indent=2, ensure_ascii=False)
