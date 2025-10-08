import importlib.resources
import json
import logging
import uuid
from pydantic import Field, field_validator
from typing import Optional, List, Dict, Any, Union
import ast
import boto3
import click
import yaml
from hyperpod_cluster_stack_template.v1_0.model import ClusterStackBase

from sagemaker.hyperpod import create_boto3_client
from sagemaker.hyperpod.common.telemetry import _hyperpod_telemetry_emitter
from sagemaker.hyperpod.common.telemetry.constants import Feature

CAPABILITIES_FOR_STACK_CREATION = [
    'CAPABILITY_AUTO_EXPAND',
    'CAPABILITY_IAM',
    'CAPABILITY_NAMED_IAM'
]
log = logging.getLogger()


class HpClusterStack(ClusterStackBase):
    """Manages SageMaker HyperPod cluster CloudFormation stacks.

    This class provides functionality to create, manage, and monitor CloudFormation stacks
    for SageMaker HyperPod clusters. It extends ClusterStackBase with stack lifecycle operations.

    .. dropdown:: Usage Examples
       :open:

       .. code-block:: python

          >>> # Create a cluster stack instance
          >>> stack = HpClusterStack()
          >>> response = stack.create(region="us-west-2")
          >>>
          >>> # Check stack status
          >>> status = stack.get_status()
          >>> print(status)
    """
    stack_id: Optional[str] = Field(
        None,
        description="CloudFormation stack ID set after stack creation"
    )
    stack_name: Optional[str] = Field(
        None,
        description="CloudFormation stack name set after stack creation"
    )

    def __init__(self, **data):
        super().__init__(**data)

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

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "create_cluster_stack")
    def create(self,
               region: Optional[str] = None,
               template_version: Optional[int] = 1) -> str:
        """Creates a new HyperPod cluster CloudFormation stack.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - region
             - str, optional
             - AWS region for stack creation. Uses current session region if not specified

        **Returns:**

        dict: CloudFormation describe_stacks response containing stack details

        **Raises:**

        Exception: When CloudFormation stack creation fails

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Create stack in default region
              >>> stack = HpClusterStack()
              >>> response = stack.create()
              >>>
              >>> # Create stack in specific region
              >>> response = stack.create(region="us-east-1")
        """
        # Get the region from the boto3 session or use the provided region
        region = region or boto3.session.Session().region_name
        cf = create_boto3_client('cloudformation', region_name=region)

        # Convert the input object to CloudFormation parameters
        parameters = self._create_parameters()

        stack_name = f"HyperpodClusterStack-{str(uuid.uuid4())[:5]}"
        # Use the fixed bucket name from the model
        bucket_name = "aws-sagemaker-hyperpod-cluster-setup"
        template_key = f"{template_version}/templates/main-stack-eks-based-template.yaml"

        try:
            # Use TemplateURL for large templates (>51KB)
            template_url = f"https://{bucket_name}-{region}-{self.stage}.s3.amazonaws.com/{template_key}"
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

                    for i, setting in enumerate(settings_list, 1):
                        formatted_setting = self._convert_nested_keys(setting)
                        parameters.append({
                            'ParameterKey': f'InstanceGroupSettings{i}',
                            'ParameterValue': "[" + json.dumps(formatted_setting) + "]" if isinstance(formatted_setting, (dict, list)) else str(formatted_setting)
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
                            'ParameterValue': "[" + json.dumps(formatted_setting) + "]" if isinstance(formatted_setting, (dict, list)) else str(formatted_setting)
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
            "hyperpod_cluster_name": "HyperPodClusterName",
            "InstanceCount": "InstanceCount",
            "InstanceGroupName": "InstanceGroupName",
            "InstanceType": "InstanceType",
            "TargetAvailabilityZoneId": "TargetAvailabilityZoneId",
            "ThreadsPerCore": "ThreadsPerCore",
            "InstanceStorageConfigs": "InstanceStorageConfigs",
            "EbsVolumeConfig": "EbsVolumeConfig",
            "VolumeSizeInGB": "VolumeSizeInGB"
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
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "describe_cluster_stack")
    def describe(stack_name, region: Optional[str] = None):
        """Describes a CloudFormation stack by name.

        .. note::
           Stack descriptions are region-specific. You must use the correct region where the stack was created to retrieve its description.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - stack_name
             - str
             - Name of the CloudFormation stack to describe. For ARN format arn:aws:cloudformation:region:account:stack/stack-name/stack-id, use the stack-name part
           * - region
             - str, optional
             - AWS region where the stack exists

        **Returns:**

        dict: CloudFormation describe_stacks response

        **Raises:**

        ValueError: When stack is not accessible or doesn't exist
        RuntimeError: When CloudFormation operation fails

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Describe a stack by name
              >>> response = HpClusterStack.describe("my-stack-name")
              >>>
              >>> # Describe stack in specific region
              >>> response = HpClusterStack.describe("my-stack", region="us-west-2")
        """
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
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "list_cluster_stack")
    def list(region: Optional[str] = None, stack_status_filter: Optional[List[str]] = None):
        """Lists all CloudFormation stacks in the specified region.

        .. note::
           Stack listings are region-specific. If no region is provided, uses the default region from your AWS configuration.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - region
             - str, optional
             - AWS region to list stacks from. Uses default region if not specified

        **Returns:**

        dict: CloudFormation list_stacks response containing stack summaries

        **Raises:**

        ValueError: When insufficient permissions to list stacks
        RuntimeError: When CloudFormation list operation fails

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # List stacks in current region
              >>> stacks = HpClusterStack.list()
              >>>
              >>> # List stacks in specific region
              >>> stacks = HpClusterStack.list(region="us-east-1")
        """
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
        """Gets the status of the current stack instance.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - region
             - str, optional
             - AWS region where the stack exists

        **Returns:**

        str: CloudFormation stack status (e.g., 'CREATE_COMPLETE', 'UPDATE_IN_PROGRESS')

        **Raises:**

        ValueError: When stack hasn't been created yet (call create() first)

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Create stack first, then check status
              >>> stack = HpClusterStack()
              >>> stack.create()
              >>> status = stack.get_status()
              >>> print(f"Stack status: {status}")
        """
        if not self.stack_name:
            raise ValueError("Stack must be created first. Call create() before checking status.")
        return self._get_stack_status_helper(self.stack_name, region)

    @staticmethod
    def check_status(stack_name: str, region: Optional[str] = None):
        """Checks the status of any CloudFormation stack by name.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - stack_name
             - str
             - Name of the CloudFormation stack
           * - region
             - str, optional
             - AWS region where the stack exists

        **Returns:**

        str: CloudFormation stack status or None if stack not found

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Check status of any stack
              >>> status = HpClusterStack.check_status("my-stack-name")
              >>> 
              >>> # Check status in specific region
              >>> status = HpClusterStack.check_status("my-stack", region="us-west-2")
        """
        return HpClusterStack._get_stack_status_helper(stack_name, region)
    
    @staticmethod
    def delete(stack_name: str, region: Optional[str] = None, retain_resources: Optional[List[str]] = None, 
                logger: Optional[logging.Logger] = None) -> None:
        """Deletes a HyperPod cluster CloudFormation stack.

        Removes the specified CloudFormation stack and all associated AWS resources.
        This operation cannot be undone and proceeds automatically without confirmation.

        **Parameters:**

        .. list-table::
            :header-rows: 1
            :widths: 20 20 60

            * - Parameter
                - Type
                - Description
            * - stack_name
                - str
                - Name of the CloudFormation stack to delete
            * - region
                - str, optional
                - AWS region where the stack exists
            * - retain_resources
                - List[str], optional
                - List of logical resource IDs to retain during deletion (only works on DELETE_FAILED stacks)
            * - logger
                - logging.Logger, optional
                - Logger instance for output messages. Uses default logger if not provided

        **Raises:**

        ValueError: When stack doesn't exist or retain_resources limitation is encountered
        RuntimeError: When CloudFormation deletion fails
        Exception: For other deletion errors

        .. dropdown:: Usage Examples
            :open:

            .. code-block:: python

                >>> # Delete a stack (automatically proceeds without confirmation)
                >>> HpClusterStack.delete("my-stack-name")
                >>>
                >>> # Delete in specific region
                >>> HpClusterStack.delete("my-stack-name", region="us-west-2")
                >>>
                >>> # Delete with retained resources (only works on DELETE_FAILED stacks)
                >>> HpClusterStack.delete("my-stack-name", retain_resources=["S3Bucket", "EFSFileSystem"])
                >>>
                >>> # Delete with custom logger
                >>> import logging
                >>> logger = logging.getLogger(__name__)
                >>> HpClusterStack.delete("my-stack-name", logger=logger)
        """
        from sagemaker.hyperpod.cli.cluster_stack_utils import (
            delete_stack_with_confirmation, 
            StackNotFoundError
        )
        
        if logger is None:
            logger = logging.getLogger(__name__)
        
        # Convert retain_resources list to comma-separated string for the utility function
        retain_resources_str = ",".join(retain_resources) if retain_resources else ""

        def sdk_confirm_callback(message: str) -> bool:
            """SDK-specific confirmation callback - always auto-confirms."""
            logger.info(f"Auto-confirming: {message}")
            return True
        
        try:
            delete_stack_with_confirmation(
                stack_name=stack_name,
                region=region or boto3.session.Session().region_name,
                retain_resources_str=retain_resources_str,
                message_callback=logger.info,
                confirm_callback=sdk_confirm_callback,
                success_callback=logger.info
            )
        except StackNotFoundError:
            error_msg = f"Stack '{stack_name}' not found"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_str = str(e)
            
            # Handle CloudFormation retain-resources limitation with clear exception for SDK
            if retain_resources and "specify which resources to retain only when the stack is in the DELETE_FAILED state" in error_str:
                error_msg = (
                    f"CloudFormation limitation: retain_resources can only be used on stacks in DELETE_FAILED state. "
                    f"Current stack state allows normal deletion. Try deleting without retain_resources first, "
                    f"then retry with retain_resources if deletion fails."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Handle termination protection
            if "TerminationProtection is enabled" in error_str:
                error_msg = (
                    f"Stack deletion blocked: Termination Protection is enabled. "
                    f"Disable termination protection first using AWS CLI or Console."
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Handle other errors
            logger.error(f"Failed to delete stack: {error_str}")
            raise RuntimeError(f"Stack deletion failed: {error_str}")

    @staticmethod
    def delete(stack_name: str, region: Optional[str] = None, retain_resources: Optional[List[str]] = None, 
               logger: Optional[logging.Logger] = None) -> None:
        """Deletes a HyperPod cluster CloudFormation stack.

        Removes the specified CloudFormation stack and all associated AWS resources.
        This operation cannot be undone and proceeds automatically without confirmation.

        **Parameters:**

        .. list-table::
           :header-rows: 1
           :widths: 20 20 60

           * - Parameter
             - Type
             - Description
           * - stack_name
             - str
             - Name of the CloudFormation stack to delete
           * - region
             - str, optional
             - AWS region where the stack exists
           * - retain_resources
             - List[str], optional
             - List of logical resource IDs to retain during deletion (only works on DELETE_FAILED stacks)
           * - logger
             - logging.Logger, optional
             - Logger instance for output messages. Uses default logger if not provided

        **Raises:**

        ValueError: When stack doesn't exist or retain_resources limitation is encountered
        RuntimeError: When CloudFormation deletion fails
        Exception: For other deletion errors

        .. dropdown:: Usage Examples
           :open:

           .. code-block:: python

              >>> # Delete a stack (automatically proceeds without confirmation)
              >>> HpClusterStack.delete("my-stack-name")
              >>>
              >>> # Delete in specific region
              >>> HpClusterStack.delete("my-stack-name", region="us-west-2")
              >>>
              >>> # Delete with retained resources (only works on DELETE_FAILED stacks)
              >>> HpClusterStack.delete("my-stack-name", retain_resources=["S3Bucket", "EFSFileSystem"])
              >>>
              >>> # Delete with custom logger
              >>> import logging
              >>> logger = logging.getLogger(__name__)
              >>> HpClusterStack.delete("my-stack-name", logger=logger)
        """
        from sagemaker.hyperpod.cli.cluster_stack_utils import (
            delete_stack_with_confirmation, 
            StackNotFoundError
        )
        
        if logger is None:
            logger = logging.getLogger(__name__)
        
        # Convert retain_resources list to comma-separated string for the utility function
        retain_resources_str = ",".join(retain_resources) if retain_resources else ""

        def sdk_confirm_callback(message: str) -> bool:
            """SDK-specific confirmation callback - always auto-confirms."""
            logger.info(f"Auto-confirming: {message}")
            return True
        
        try:
            delete_stack_with_confirmation(
                stack_name=stack_name,
                region=region or boto3.session.Session().region_name,
                retain_resources_str=retain_resources_str,
                message_callback=logger.info,
                confirm_callback=sdk_confirm_callback,
                success_callback=logger.info
            )
        except StackNotFoundError:
            error_msg = f"Stack '{stack_name}' not found"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_str = str(e)
            
            # Handle CloudFormation retain-resources limitation with clear exception for SDK
            if retain_resources and "specify which resources to retain only when the stack is in the DELETE_FAILED state" in error_str:
                error_msg = (
                    f"CloudFormation limitation: retain_resources can only be used on stacks in DELETE_FAILED state. "
                    f"Current stack state allows normal deletion. Try deleting without retain_resources first, "
                    f"then retry with retain_resources if deletion fails."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Handle termination protection
            if "TerminationProtection is enabled" in error_str:
                error_msg = (
                    f"Stack deletion blocked: Termination Protection is enabled. "
                    f"Disable termination protection first using AWS CLI or Console."
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Handle other errors
            logger.error(f"Failed to delete stack: {error_str}")
            raise RuntimeError(f"Stack deletion failed: {error_str}")


    def _yaml_to_json_string(yaml_path) -> str:
        """Convert YAML file to JSON string"""
        with open(yaml_path, 'r') as file:
            yaml_data = yaml.safe_load(file)
        return json.dumps(yaml_data, indent=2, ensure_ascii=False)
