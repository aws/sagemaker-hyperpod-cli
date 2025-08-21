import importlib.resources
import json
import logging
import uuid
from pydantic import Field, field_validator
from typing import Optional, List, Dict, Any, Union

import boto3
import click
import yaml
from hyperpod_cluster_stack_template.v1_0.model import ClusterStackBase

from sagemaker.hyperpod import create_boto3_client

CAPABILITIES_FOR_STACK_CREATION = [
'CAPABILITY_IAM',
'CAPABILITY_NAMED_IAM'
]
log = logging.getLogger()


class HpClusterStack(ClusterStackBase):
    stack_id: Optional[str] = Field(
        None,
        description="CloudFormation stack ID set after stack creation"
    )
    stack_name: Optional[str] = Field(
        None,
        description="CloudFormation stack name set after stack creation"
    )
    
    def __init__(self, **data):
        # Convert array values to JSON strings
        for key, value in data.items():
            if isinstance(value, list):
                data[key] = json.dumps(value)
        super().__init__(**data)
    
    @field_validator('kubernetes_version', mode='before')
    @classmethod
    def validate_kubernetes_version(cls, v):
        if v is not None:
            return str(v)
        return v
    
    @field_validator('availability_zone_ids', 'nat_gateway_ids', 'eks_private_subnet_ids', 'security_group_ids', 'private_route_table_ids', 'private_subnet_ids', 'tags', mode='before')
    @classmethod
    def validate_list_fields(cls, v):
        # Convert JSON string to list if needed
        if isinstance(v, str) and v.startswith('['):
            try:
                import json
                v = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                pass  # Keep original value if parsing fails
        
        if isinstance(v, list) and len(v) == 0:
            raise ValueError('Empty lists [] are not allowed. Use proper YAML array format or leave field empty.')
        return v
    
    @field_validator('instance_group_settings', 'rig_settings', mode='before')
    @classmethod
    def validate_json_string_fields(cls, v):
        # Check for empty lists first
        if isinstance(v, list) and len(v) == 0:
            raise ValueError('Empty lists [] are not allowed. Use proper YAML array format or leave field empty.')
        
        # For instance_group_settings and rig_settings, keep as JSON strings
        # Just validate that they're valid JSON if they're strings
        if isinstance(v, str) and v.strip():
            if v.startswith('['):
                try:
                    import json
                    json.loads(v)  # Validate JSON but don't convert
                except (json.JSONDecodeError, TypeError):
                    raise ValueError('Must be valid JSON array string')
        return v  # Return original string
    


    @staticmethod
    def get_template() -> str:
        try:
            template_content = importlib.resources.read_text(
                'hyperpod_cluster_stack_template', 
                'creation_template.yaml'
            )
            yaml_data = yaml.safe_load(template_content)
            return json.dumps(yaml_data, indent=2, ensure_ascii=False)
        except Exception as e:
            raise RuntimeError(f"Failed to load template from package: {e}")

    def create(self,
               region: Optional[str] = None) -> str:
        # Get the region from the boto3 session or use the provided region
        region = region or boto3.session.Session().region_name
        cf = create_boto3_client('cloudformation', region_name=region)

        # Convert the input object to CloudFormation parameters
        parameters = self._create_parameters()

        stack_name = f"HyperpodClusterStack-{str(uuid.uuid4())[:5]}"
        # Get account ID and create bucket name
        bucket_name = f"sagemaker-hyperpod-cluster-stack-bucket"
        template_key = f"1.1/main-stack-eks-based-template.yaml"

        try:
            # Use TemplateURL for large templates (>51KB)
            template_url = f"https://{bucket_name}.s3.amazonaws.com/{template_key}"
            

            
            response = cf.create_stack(
                StackName=stack_name,
                TemplateURL=template_url,
                Parameters=parameters,
                Tags=self._parse_tags(),
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

    def _create_parameters(self) -> List[Dict[str, str]]:
        parameters = []
        for field_name, field_info in ClusterStackBase.model_fields.items():
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
                    
                    # Send the entire array as InstanceGroupSettings1 (not individual objects)
                    if settings_list:
                        parameters.append({
                            'ParameterKey': 'InstanceGroupSettings1',
                            'ParameterValue': json.dumps(settings_list)
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
                    
                    # Send the entire array as RigSettings1 (not individual objects)
                    if settings_list:
                        parameters.append({
                            'ParameterKey': 'RigSettings1',
                            'ParameterValue': json.dumps(settings_list)
                        })
                else:
                    # Convert array fields to comma-separated strings
                    if field_name in ['availability_zone_ids', 'nat_gateway_ids', 'eks_private_subnet_ids', 
                                    'security_group_ids', 'private_route_table_ids', 'private_subnet_ids']:
                        if isinstance(value, list):
                            value = ','.join(str(item) for item in value)
                        elif isinstance(value, str) and value.startswith('['):
                            # Handle JSON string format from CLI
                            try:
                                parsed_list = json.loads(value)
                                value = ','.join(str(item) for item in parsed_list)
                            except (json.JSONDecodeError, TypeError):
                                pass  # Keep original string value
                    # Convert tags array to JSON string
                    elif field_name == 'tags':
                        if isinstance(value, list):
                            value = json.dumps(value)
                        elif isinstance(value, str) and not value.startswith('['):
                            # If it's already a JSON string, keep it as is
                            pass
                    # Convert boolean values to strings for CloudFormation
                    elif isinstance(value, bool):
                        value = str(value).lower()

                    parameters.append({
                        'ParameterKey': self._snake_to_pascal(field_name),
                        'ParameterValue': str(value)
                    })
        return parameters

    def _parse_tags(self) -> List[Dict[str, str]]:
        """Parse tags field and return proper CloudFormation tags format."""
        if not self.tags:
            return []

        tags_list = self.tags
        if isinstance(self.tags, str):
            try:
                tags_list = json.loads(self.tags)
            except (json.JSONDecodeError, TypeError):
                return []

        # Convert array of strings to Key-Value format
        if isinstance(tags_list, list) and tags_list:
            # Check if already in Key-Value format
            if isinstance(tags_list[0], dict) and 'Key' in tags_list[0]:
                return tags_list
            # Convert string array to Key-Value format
            return [{'Key': tag, 'Value': ''} for tag in tags_list if isinstance(tag, str)]

        return []

    def _convert_nested_keys(self, obj: Any) -> Any:
        """Convert nested JSON keys from snake_case to PascalCase."""
        if isinstance(obj, dict):
            return {self._snake_to_pascal(k): self._convert_nested_keys(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_nested_keys(item) for item in obj]
        return obj

    @staticmethod
    def _snake_to_pascal(snake_str: str) -> str:
        """Convert snake_case string to PascalCase."""
        if not snake_str:
            return snake_str
            
        # Handle specific cases
        mappings = {
            "eks_cluster_name": "EKSClusterName",
            "create_eks_cluster_stack": "CreateEKSClusterStack",
            "create_hyperpod_cluster_stack": "CreateHyperPodClusterStack",
            "create_sagemaker_iam_role_stack": "CreateSageMakerIAMRoleStack",
            "create_vpc_stack": "CreateVPCStack",
            "sagemaker_iam_role_name": "SageMakerIAMRoleName",
            "vpc_cidr": "VpcCIDR",
            "enable_hp_inference_feature": "EnableHPInferenceFeature",
            "fsx_availability_zone_id": "FsxAvailabilityZoneId",
            "hyperpod_cluster_name": "HyperPodClusterName"
        }
        
        if snake_str in mappings:
            return mappings[snake_str]


        # Default case: capitalize each word
        return ''.join(word.capitalize() for word in snake_str.split('_'))
    
    def _snake_to_camel(self, snake_str: str) -> str:
        """Convert snake_case string to camelCase for nested JSON keys."""
        if not snake_str:
            return snake_str
        words = snake_str.split('_')
        return words[0] + ''.join(word.capitalize() for word in words[1:])

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
    def list(region: Optional[str] = None, stack_status_filter: Optional[List[str]] = None):
        cf = create_boto3_client('cloudformation', region_name=region)

        try:
            # Prepare API call parameters
            list_params = {}
            
            if stack_status_filter is not None:
                list_params['StackStatusFilter'] = stack_status_filter
            
            response = cf.list_stacks(**list_params)
            
            # Only filter DELETE_COMPLETE when no explicit filter is provided
            if stack_status_filter is None and 'StackSummaries' in response:
                response['StackSummaries'] = [
                    stack for stack in response['StackSummaries'] 
                    if stack.get('StackStatus') != 'DELETE_COMPLETE'
                ]
            
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


def _yaml_to_json_string(yaml_path) -> str:
    """Convert YAML file to JSON string"""
    with open(yaml_path, 'r') as file:
        yaml_data = yaml.safe_load(file)
    return json.dumps(yaml_data, indent=2, ensure_ascii=False)