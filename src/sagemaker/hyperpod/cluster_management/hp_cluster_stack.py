import importlib.resources
import json
import logging
from typing import Optional

import boto3
import yaml
from sagemaker.hyperpod.cluster_management.config.hp_cluster_stack_config import _ClusterStackBase

CLUSTER_CREATION_TEMPLATE_FILE_NAME = "creation_template.yaml"
CLUSTER_STACK_TEMPLATE_PACKAGE_NAME = "hyperpod_cluster_stack_template"

log = logging.getLogger()


class HpClusterStack(_ClusterStackBase):

    def create(self,
               stack_name: str,
               region: Optional[str] = None):
        # Get the region from the boto3 session or use the provided region
        region = region or boto3.session.Session().region_name
        cf = boto3.client('cloudformation', region_name=region)

        # Convert the input object to CloudFormation parameters
        parameters = self._create_parameters()

        print("Params",parameters)
        files = importlib.resources.files(CLUSTER_STACK_TEMPLATE_PACKAGE_NAME)
        template_file = files / CLUSTER_CREATION_TEMPLATE_FILE_NAME

        template_body = _yaml_to_json_string(template_file)
        try:
            response = cf.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=parameters,
                Tags=self.tags or [{
                        'Key': 'Environment',
                        'Value': 'Development'
                    }]
            )
            log.error(f"Stack creation initiated. Stack ID: {response['StackId']}")
        except Exception as e:
            log.error(f"Error creating stack: {e}")

    def _create_parameters(self):
        parameters = []
        for field_name, field_info in _ClusterStackBase.model_fields.items():
            value = getattr(self, field_name, None)
            if value is not None:
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


def _yaml_to_json_string(yaml_path):
    """Convert YAML file to JSON string"""
    with open(yaml_path, 'r') as file:
        yaml_data = yaml.safe_load(file)
    return json.dumps(yaml_data, indent=2, ensure_ascii=False)
