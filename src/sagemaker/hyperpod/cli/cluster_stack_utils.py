"""
Utility classes for CloudFormation cluster stack operations.

This module provides reusable components for managing CloudFormation stacks,
handling errors, and user interactions. These utilities promote code reuse
across different stack operations and CLI commands.
"""

import boto3
import click
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError
from sagemaker.hyperpod.cli.common_utils import (
    GenericConfirmationHandler, 
    parse_comma_separated_list,
    categorize_resources_by_type
)


class CloudFormationResourceManager:
    """Handles CloudFormation resource operations - reusable for any stack type."""
    
    def __init__(self, region: str):
        """Initialize the resource manager with a specific region.
        
        Args:
            region: AWS region for CloudFormation operations
        """
        self.region = region
        self.cf_client = boto3.client('cloudformation', region_name=region)
    
    def get_stack_resources(self, stack_name: str) -> List[Dict[str, Any]]:
        """Get all resources in a CloudFormation stack.
        
        Args:
            stack_name: Name of the CloudFormation stack
            
        Returns:
            List of resource summaries from CloudFormation
            
        Raises:
            StackNotFoundError: When stack doesn't exist
            Exception: For other CloudFormation errors
        """
        try:
            resources_response = self.cf_client.list_stack_resources(StackName=stack_name)
            return resources_response.get('StackResourceSummaries', [])
        except Exception as e:
            if "does not exist" in str(e):
                raise StackNotFoundError(f"Stack '{stack_name}' not found")
            raise
    
    def validate_retain_resources(self, retain_list: List[str], existing_resources: List[Dict[str, Any]]) -> tuple[List[str], List[str]]:
        """Validate that retain resources exist in the stack.
        
        Args:
            retain_list: List of logical resource IDs to retain
            existing_resources: List of existing stack resources
            
        Returns:
            Tuple of (valid_resources, invalid_resources)
        """
        if not retain_list:
            return [], []
        
        existing_resource_names = {r.get('LogicalResourceId', '') for r in existing_resources}
        valid_retain_resources = []
        invalid_retain_resources = []
        
        for resource in retain_list:
            if resource in existing_resource_names:
                valid_retain_resources.append(resource)
            else:
                invalid_retain_resources.append(resource)
        
        return valid_retain_resources, invalid_retain_resources
    
    def categorize_resources(self, resources: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Categorize CloudFormation resources by type using generic utility."""
        type_mappings = {
            "EC2 Instances": ["AWS::EC2::Instance"],
            "Networking": ["AWS::EC2::VPC", "AWS::EC2::Subnet", "AWS::EC2::SecurityGroup", 
                          "AWS::EC2::InternetGateway", "AWS::EC2::RouteTable", "AWS::EC2::Route"],
            "IAM": ["AWS::IAM::Role", "AWS::IAM::Policy", "AWS::IAM::InstanceProfile"],
            "Storage": ["AWS::S3::Bucket", "AWS::EBS::Volume", "AWS::EFS::FileSystem"]
        }
        
        return categorize_resources_by_type(resources, type_mappings)
    
    def compare_resource_states(self, original_resources: List[Dict[str, Any]], current_resources: List[Dict[str, Any]]) -> tuple[set[str], set[str]]:
        """Compare original and current resource states to identify changes.
        
        Args:
            original_resources: Resources before deletion attempt
            current_resources: Resources after deletion attempt
            
        Returns:
            Tuple of (deleted_resources, remaining_resources)
        """
        original_names = {r['LogicalResourceId'] for r in original_resources}
        current_names = {r['LogicalResourceId'] for r in current_resources}
        
        deleted_resources = original_names - current_names
        remaining_resources = current_names
        
        return deleted_resources, remaining_resources


class DeletionConfirmationHandler(GenericConfirmationHandler):
    """Handles user confirmation and display of deletion information for CloudFormation stacks."""
    
    def display_deletion_warning(self, categorized_resources: Dict[str, List[str]]) -> None:
        """Display warning about resources to be deleted."""
        self.display_warning_list(
            "WARNING: This will delete the following", 
            categorized_resources
        )
    
    def display_invalid_resources_warning(self, invalid_resources: List[str]) -> None:
        """Display warning about invalid retain resources."""
        if not invalid_resources:
            return
            
        click.echo(f"⚠️  Warning: The following {len(invalid_resources)} resources don't exist in the stack:")
        for resource in invalid_resources:
            click.echo(f" - {resource} (not found)")
        click.echo()
    
    def confirm_deletion(self) -> bool:
        """Get user confirmation for deletion."""
        return click.confirm("Continue?", default=False)


class CloudFormationErrorHandler:
    """Handles CloudFormation-specific errors - reusable for create/update/delete operations."""
    
    def __init__(self, region: str):
        """Initialize the error handler with a specific region.
        
        Args:
            region: AWS region for CloudFormation operations
        """
        self.region = region
        self.cf_client = boto3.client('cloudformation', region_name=region)
    
    def handle_deletion_error(self, error: Exception, stack_name: str, retain_resources: Optional[str] = None) -> None:
        """Handle various CloudFormation deletion errors.
        
        Args:
            error: The exception that occurred
            stack_name: Name of the stack being deleted
            retain_resources: Original retain resources string (for error messages)
        """
        error_str = str(error)
        
        # Handle termination protection specifically
        if "TerminationProtection is enabled" in error_str:
            self._handle_termination_protection_error(stack_name)
            raise click.ClickException("Termination protection must be disabled before deletion")
        
        # Handle CloudFormation retain-resources limitation
        if retain_resources and "specify which resources to retain only when the stack is in the DELETE_FAILED state" in error_str:
            self._handle_retention_limitation_error(stack_name, retain_resources)
            return  # Exit gracefully without raising exception
        
        # Handle other deletion errors
        self._handle_generic_deletion_error(error_str)
        raise click.ClickException(str(error))
    
    def handle_partial_deletion_failure(self, stack_name: str, original_resources: List[Dict[str, Any]], retain_list: List[str]) -> None:
        """Handle partial deletion failures by showing what succeeded vs failed.
        
        Args:
            stack_name: Name of the stack
            original_resources: Resources before deletion attempt
            retain_list: List of resources that were supposed to be retained
        """
        click.echo("✗ Stack deletion failed")
        
        try:
            current_resources_response = self.cf_client.list_stack_resources(StackName=stack_name)
            current_resources = current_resources_response.get('StackResourceSummaries', [])
            
            deleted_resources, remaining_resources = CloudFormationResourceManager(self.region).compare_resource_states(
                original_resources, current_resources
            )
            
            # Show what was successfully deleted
            if deleted_resources:
                click.echo()
                click.echo(f"Successfully deleted ({len(deleted_resources)}):")
                for resource in deleted_resources:
                    click.echo(f" ✓ {resource}")
            
            # Show what failed to delete (excluding retained resources)
            failed_resources = remaining_resources - set(retain_list) if retain_list else remaining_resources
            if failed_resources:
                click.echo()
                click.echo(f"Failed to delete ({len(failed_resources)}):")
                for resource in failed_resources:
                    click.echo(f" ✗ {resource} (DependencyViolation: has dependent resources)")
            
            # Show retained resources
            if retain_list:
                click.echo()
                click.echo(f"Successfully retained as requested ({len(retain_list)}):")
                for resource in retain_list:
                    click.echo(f" ✓ {resource} (retained)")
            
            click.echo()
            click.echo("💡 Note: Some resources may have dependencies preventing deletion")
            click.echo("   Check the AWS CloudFormation console for detailed dependency information")
            
        except Exception:
            # If we can't get current resources, show generic error
            click.echo("Unable to determine which resources were deleted")
    
    def _handle_termination_protection_error(self, stack_name: str) -> None:
        """Handle termination protection error."""
        click.echo("❌ Stack deletion blocked: Termination Protection is enabled")
        click.echo()
        click.echo("To delete this stack, first disable termination protection:")
        click.echo(f"aws cloudformation update-termination-protection --no-enable-termination-protection --stack-name {stack_name} --region {self.region}")
        click.echo()
        click.echo("Then retry the delete command.")
    
    def _handle_retention_limitation_error(self, stack_name: str, retain_resources: str) -> None:
        """Handle CloudFormation retention limitation error."""
        click.echo("❌ CloudFormation limitation: --retain-resources only works on failed deletions")
        click.echo()
        click.echo("💡 Recommended workflow:")
        click.echo("1. First try deleting without --retain-resources:")
        click.echo(f"   hyp delete cluster-stack {stack_name} --region {self.region}")
        click.echo()
        click.echo("2. If deletion fails, the stack will be in DELETE_FAILED state")
        click.echo("3. Then retry with --retain-resources to keep specific resources:")
        click.echo(f"   hyp delete cluster-stack {stack_name} --retain-resources {retain_resources} --region {self.region}")
    
    def _handle_generic_deletion_error(self, error_str: str) -> None:
        """Handle generic deletion errors."""
        if "does not exist" in error_str:
            click.echo("❌ Stack not found")
        elif "AccessDenied" in error_str:
            click.echo("❌ Access denied. Check AWS permissions")
        else:
            click.echo(f"❌ Error deleting stack: {error_str}")


class StackNotFoundError(Exception):
    """Raised when a CloudFormation stack is not found."""
    pass


def parse_retain_resources(retain_resources_str: str) -> List[str]:
    """Parse comma-separated retain resources string."""
    return parse_comma_separated_list(retain_resources_str)


def perform_stack_deletion(stack_name: str, region: str, retain_list: List[str]) -> None:
    """Perform the actual CloudFormation stack deletion.
    
    Args:
        stack_name: Name of the stack to delete
        region: AWS region
        retain_list: List of resources to retain during deletion
        
    Raises:
        Exception: If deletion fails
    """
    cf_client = boto3.client('cloudformation', region_name=region)
    
    delete_params = {'StackName': stack_name}
    if retain_list:
        delete_params['RetainResources'] = retain_list
    
    cf_client.delete_stack(**delete_params)
    
    click.echo(f"✓ Stack '{stack_name}' deletion initiated successfully")
