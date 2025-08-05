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
            return response['StackId']
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
                        parameters.append({
                            'ParameterKey': f'InstanceGroupSettings{i}',
                            'ParameterValue': json.dumps(setting) if isinstance(setting, (dict, list)) else str(setting)
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
                        parameters.append({
                            'ParameterKey': f'RigSettings{i}',
                            'ParameterValue': json.dumps(setting) if isinstance(setting, (dict, list)) else str(setting)
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


def _yaml_to_json_string(yaml_path):
    """Convert YAML file to JSON string"""
    with open(yaml_path, 'r') as file:
        yaml_data = yaml.safe_load(file)
    return json.dumps(yaml_data, indent=2, ensure_ascii=False)
