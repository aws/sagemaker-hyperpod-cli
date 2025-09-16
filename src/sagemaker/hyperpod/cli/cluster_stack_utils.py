"""
CloudFormation cluster stack deletion utilities.

This module provides utilities for managing CloudFormation stack deletion operations
with support for both CLI and SDK interfaces through a callback pattern.

Public Interface:
    delete_stack_with_confirmation() - Main orchestration function for stack deletion
    StackNotFoundError - Exception raised when stack is not found

All other functions are private implementation details and should not be used directly.
"""

import boto3
import click
import logging
from typing import List, Dict, Any, Optional, Tuple, Callable
from botocore.exceptions import ClientError
from sagemaker.hyperpod.cli.common_utils import (
    parse_comma_separated_list,
    categorize_resources_by_type
)


class _StackNotFoundError(Exception):
    """Exception raised when a CloudFormation stack is not found."""
    pass


# Make the exception available with the original name
StackNotFoundError = _StackNotFoundError

MessageCallback = Callable[[str], None]
ConfirmCallback = Callable[[str], bool]
SuccessCallback = Callable[[str], None]


def _get_stack_resources(stack_name: str, region: str, logger: Optional[logging.Logger] = None) -> List[Dict[str, Any]]:
    """Get all resources in a CloudFormation stack.
    
    Args:
        stack_name: Name of the CloudFormation stack
        region: AWS region for CloudFormation operations
        logger: Optional logger for debug information
        
    Returns:
        List of resource summaries from CloudFormation
        
    Raises:
        _StackNotFoundError: When stack doesn't exist
        ClientError: For other CloudFormation errors
    """
    if logger:
        logger.debug(f"Fetching resources for stack '{stack_name}' in region '{region}'")
    
    cf_client = boto3.client('cloudformation', region_name=region)
    try:
        resources_response = cf_client.list_stack_resources(StackName=stack_name)
        resources = resources_response.get('StackResourceSummaries', [])
        
        if logger:
            logger.debug(f"Found {len(resources)} resources in stack '{stack_name}'")
        
        return resources
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ValidationError' and "does not exist" in str(e):
            raise _StackNotFoundError(f"Stack '{stack_name}' not found")
        raise


def _validate_retain_resources(retain_list: List[str], existing_resources: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
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


def _categorize_stack_resources(resources: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Categorize CloudFormation resources by type using generic utility."""
    type_mappings = {
        "EC2 Instances": ["AWS::EC2::Instance"],
        "Networking": ["AWS::EC2::VPC", "AWS::EC2::Subnet", "AWS::EC2::SecurityGroup", 
                      "AWS::EC2::InternetGateway", "AWS::EC2::RouteTable", "AWS::EC2::Route"],
        "IAM": ["AWS::IAM::Role", "AWS::IAM::Policy", "AWS::IAM::InstanceProfile"],
        "Storage": ["AWS::S3::Bucket", "AWS::EBS::Volume", "AWS::EFS::FileSystem"]
    }
    
    return categorize_resources_by_type(resources, type_mappings)


def _compare_resource_states(original_resources: List[Dict[str, Any]], current_resources: List[Dict[str, Any]]) -> Tuple[set[str], set[str]]:
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


def _display_deletion_warning(categorized_resources: Dict[str, List[str]], message_callback: MessageCallback) -> None:
    """Display warning about resources to be deleted."""
    total_count = sum(len(item_list) for item_list in categorized_resources.values())
    message_callback(f"\n⚠ WARNING: This will delete the following {total_count} resources:\n")
    
    for category, item_list in categorized_resources.items():
        if item_list:
            message_callback(f"{category} ({len(item_list)}):")
            for item in item_list:
                message_callback(f" - {item}")
            message_callback("")


def _display_invalid_resources_warning(invalid_resources: List[str], message_callback: MessageCallback) -> None:
    """Display warning about invalid retain resources."""
    if not invalid_resources:
        return
        
    message_callback(f"⚠️  Warning: The following {len(invalid_resources)} resources don't exist in the stack:")
    for resource in invalid_resources:
        message_callback(f" - {resource} (not found)")
    message_callback("")


def _display_retention_info(retained_items: List[str], message_callback: MessageCallback) -> None:
    """Display information about items that will be retained."""
    if retained_items:
        message_callback(f"\nThe following {len(retained_items)} resources will be RETAINED:")
        for item in retained_items:
            message_callback(f" ✓ {item} (retained)")




def _handle_termination_protection_error(stack_name: str, region: str, message_callback: MessageCallback) -> None:
    """Handle termination protection error."""
    message_callback("❌ Stack deletion blocked: Termination Protection is enabled")
    message_callback("")
    message_callback("To delete this stack, first disable termination protection:")
    message_callback(f"aws cloudformation update-termination-protection --no-enable-termination-protection --stack-name {stack_name} --region {region}")
    message_callback("")
    message_callback("Then retry the delete command.")


def _handle_retention_limitation_error(stack_name: str, retain_resources: str, region: str, message_callback: MessageCallback) -> None:
    """Handle CloudFormation retention limitation error."""
    message_callback("❌ CloudFormation limitation: --retain-resources only works on failed deletions")
    message_callback("")
    message_callback("💡 Recommended workflow:")
    message_callback("1. First try deleting without --retain-resources:")
    message_callback(f"   hyp delete cluster-stack {stack_name} --region {region}")
    message_callback("")
    message_callback("2. If deletion fails, the stack will be in DELETE_FAILED state")
    message_callback("3. Then retry with --retain-resources to keep specific resources:")
    message_callback(f"   hyp delete cluster-stack {stack_name} --retain-resources {retain_resources} --region {region}")


def _handle_generic_deletion_error(error_str: str, message_callback: MessageCallback) -> None:
    """Handle generic deletion errors."""
    if "does not exist" in error_str:
        message_callback("❌ Stack not found")
    elif "AccessDenied" in error_str:
        message_callback("❌ Access denied. Check AWS permissions")
    else:
        message_callback(f"❌ Error deleting stack: {error_str}")


def _handle_partial_deletion_failure(stack_name: str, region: str, original_resources: List[Dict[str, Any]], 
                                    retain_list: List[str], message_callback: MessageCallback) -> None:
    """Handle partial deletion failures by showing what succeeded vs failed.
    
    Args:
        stack_name: Name of the stack
        region: AWS region
        original_resources: Resources before deletion attempt
        retain_list: List of resources that were supposed to be retained
        message_callback: Function to call for outputting messages
    """
    message_callback("✗ Stack deletion failed")
    
    try:
        cf_client = boto3.client('cloudformation', region_name=region)
        current_resources_response = cf_client.list_stack_resources(StackName=stack_name)
        current_resources = current_resources_response.get('StackResourceSummaries', [])
        
        deleted_resources, remaining_resources = _compare_resource_states(
            original_resources, current_resources
        )
        
        # Show what was successfully deleted
        if deleted_resources:
            message_callback("")
            message_callback(f"Successfully deleted ({len(deleted_resources)}):")
            for resource in deleted_resources:
                message_callback(f" ✓ {resource}")
        
        # Show what failed to delete (excluding retained resources)
        failed_resources = remaining_resources - set(retain_list) if retain_list else remaining_resources
        if failed_resources:
            message_callback("")
            message_callback(f"Failed to delete ({len(failed_resources)}):")
            for resource in failed_resources:
                message_callback(f" ✗ {resource} (DependencyViolation: has dependent resources)")
        
        # Show retained resources
        if retain_list:
            message_callback("")
            message_callback(f"Successfully retained as requested ({len(retain_list)}):")
            for resource in retain_list:
                message_callback(f" ✓ {resource} (retained)")
        
        message_callback("")
        message_callback("💡 Note: Some resources may have dependencies preventing deletion")
        message_callback("   Check the AWS CloudFormation console for detailed dependency information")
        
    except Exception:
        # If we can't get current resources, show generic error
        message_callback("Unable to determine which resources were deleted")

def _parse_retain_resources(retain_resources_str: str) -> List[str]:
    """Parse comma-separated retain resources string."""
    return parse_comma_separated_list(retain_resources_str)


def _perform_stack_deletion(stack_name: str, region: str, retain_list: List[str], 
                           logger: Optional[logging.Logger] = None) -> None:
    """Perform the actual CloudFormation stack deletion.
    
    This is a private low-level function that directly calls the CloudFormation delete_stack API.
    Use delete_stack_with_confirmation() for the public interface.
    
    Args:
        stack_name: Name of the stack to delete
        region: AWS region
        retain_list: List of resources to retain during deletion
        logger: Optional logger for debug information
        
    Raises:
        ClientError: If deletion fails due to CloudFormation errors
        Exception: For other deletion failures
    """
    if logger:
        logger.debug(f"Initiating deletion of stack '{stack_name}' in region '{region}'")
        if retain_list:
            logger.debug(f"Retaining resources: {retain_list}")
    
    cf_client = boto3.client('cloudformation', region_name=region)
    
    delete_params = {'StackName': stack_name}
    if retain_list:
        delete_params['RetainResources'] = retain_list
    
    cf_client.delete_stack(**delete_params)
    
    if logger:
        logger.info(f"Stack '{stack_name}' deletion initiated successfully")




def _get_stack_resources_and_validate_retention(stack_name: str, region: str, retain_resources_str: str, 
                                               logger: Optional[logging.Logger] = None) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """Get stack resources and validate retention list.
    
    Args:
        stack_name: Name of the CloudFormation stack
        region: AWS region
        retain_resources_str: Comma-separated retain resources string
        logger: Optional logger for debug information
        
    Returns:
        Tuple of (all_resources, valid_retain_list, invalid_retain_list)
        
    Raises:
        StackNotFoundError: When stack doesn't exist
    """
    resources = _get_stack_resources(stack_name, region, logger)
    if not resources:
        raise _StackNotFoundError(f"No resources found in stack '{stack_name}'")
    
    retain_list = _parse_retain_resources(retain_resources_str)
    valid_retain, invalid_retain = _validate_retain_resources(retain_list, resources)
    
    if logger and retain_list:
        logger.debug(f"Retention validation - Valid: {len(valid_retain)}, Invalid: {len(invalid_retain)}")
    
    return resources, valid_retain, invalid_retain


def _handle_stack_deletion_error(error: Exception, stack_name: str, region: str, retain_resources: Optional[str] = None, 
                                message_callback: Optional[MessageCallback] = None, 
                                logger: Optional[logging.Logger] = None) -> bool:
    """Handle various CloudFormation deletion errors with customizable output.
    
    Args:
        error: The exception that occurred
        stack_name: Name of the stack being deleted
        region: AWS region
        retain_resources: Original retain resources string (for error messages)
        message_callback: Function to call for outputting messages (default: click.echo)
        logger: Optional logger for debug information
        
    Returns:
        True if error was handled gracefully (don't re-raise), False if should re-raise
    """
    if message_callback is None:
        message_callback = click.echo
        
    error_str = str(error)
    
    if logger:
        logger.debug(f"Handling deletion error for stack '{stack_name}': {error_str}")
    
    # Handle termination protection specifically
    if "TerminationProtection is enabled" in error_str:
        _handle_termination_protection_error(stack_name, region, message_callback)
        return False  # Should re-raise
    
    # Handle CloudFormation retain-resources limitation
    # Always re-raise for SDK usage to ensure clear exceptions
    if retain_resources and "specify which resources to retain only when the stack is in the DELETE_FAILED state" in error_str:
        _handle_retention_limitation_error(stack_name, retain_resources, region, message_callback)
        return False  # ensure SDK gets the exception
    
    # Handle other deletion errors
    _handle_generic_deletion_error(error_str, message_callback)
    return False  # Should re-raise


def _display_stack_deletion_confirmation(resources: List[Dict[str, Any]], valid_retain_list: List[str], 
                                        invalid_retain_list: List[str], 
                                        message_callback: Optional[MessageCallback] = None, 
                                        confirm_callback: Optional[ConfirmCallback] = None,
                                        logger: Optional[logging.Logger] = None) -> bool:
    """Display deletion warnings and get user confirmation with customizable output.
    
    Args:
        resources: All stack resources
        valid_retain_list: Valid resources to retain
        invalid_retain_list: Invalid resources that don't exist
        message_callback: Function to call for outputting messages (default: click.echo)
        confirm_callback: Function to call for confirmation (default: click.confirm)
        logger: Optional logger for debug information
        
    Returns:
        True if user confirms deletion, False otherwise
    """
    if message_callback is None:
        message_callback = click.echo
    if confirm_callback is None:
        confirm_callback = lambda msg: click.confirm("Continue?", default=False)
    
    if logger:
        logger.debug(f"Displaying confirmation for {len(resources)} resources, {len(valid_retain_list)} to retain")
    
    # Show warning for invalid retain resources
    _display_invalid_resources_warning(invalid_retain_list, message_callback)
    
    # Display deletion warning
    resource_categories = _categorize_stack_resources(resources)
    _display_deletion_warning(resource_categories, message_callback)
    
    # Show retention info
    _display_retention_info(valid_retain_list, message_callback)
    
    return confirm_callback("Continue with deletion?")


def _handle_stack_deletion_partial_failure(stack_name: str, region: str, original_resources: List[Dict[str, Any]], 
                                          retain_list: List[str], message_callback: Optional[MessageCallback] = None) -> None:
    """Handle partial deletion failures by showing what succeeded vs failed.
    
    Args:
        stack_name: Name of the stack
        region: AWS region
        original_resources: Resources before deletion attempt
        retain_list: List of resources that were supposed to be retained
        message_callback: Function to call for outputting messages (default: click.echo)
    """
    if message_callback is None:
        message_callback = click.echo
        
    _handle_partial_deletion_failure(stack_name, region, original_resources, retain_list, message_callback)




def delete_stack_with_confirmation(stack_name: str, region: str, retain_resources_str: str = "", 
                                 message_callback: Optional[MessageCallback] = None, 
                                 confirm_callback: Optional[ConfirmCallback] = None, 
                                 success_callback: Optional[SuccessCallback] = None,
                                 logger: Optional[logging.Logger] = None) -> None:
    """
    This is the main public interface for stack deletion, supporting both CLI and SDK
    usage through customizable callback functions. It handles resource validation,
    user confirmation, deletion execution, and comprehensive error handling.
    
    Args:
        stack_name: Name of the stack to delete
        region: AWS region
        retain_resources_str: Comma-separated retain resources string
        message_callback: Function to call for outputting messages (default: click.echo)
        confirm_callback: Function to call for confirmation (default: click.confirm)
        success_callback: Function to call on successful deletion (default: click.echo)
        logger: Optional logger for debug information
        
    Raises:
        StackNotFoundError: When stack doesn't exist
        click.ClickException: For CLI usage
        Exception: For SDK usage (depending on callback implementation)
        
    Example:
        # CLI usage
        delete_stack_with_confirmation(
            stack_name="my-stack",
            region="us-west-2",
            message_callback=click.echo,
            confirm_callback=lambda msg: click.confirm("Continue?", default=False)
        )
        
        # SDK usage
        delete_stack_with_confirmation(
            stack_name="my-stack", 
            region="us-west-2",
            message_callback=logger.info,
            confirm_callback=lambda msg: True  # Auto-confirm
        )
    """
    if message_callback is None:
        message_callback = click.echo
    if success_callback is None:
        success_callback = lambda msg: click.echo(f"✓ {msg}")
    
    if logger:
        logger.info(f"Starting deletion workflow for stack '{stack_name}' in region '{region}'")
    
    # 1. Get and validate resources
    resources, valid_retain, invalid_retain = _get_stack_resources_and_validate_retention(
        stack_name, region, retain_resources_str, logger
    )
    
    # 2. Display warnings and get confirmation
    if not _display_stack_deletion_confirmation(resources, valid_retain, invalid_retain, 
                                              message_callback, confirm_callback, logger):
        message_callback("Operation cancelled.")
        return
    
    # 3. Perform deletion
    try:
        _perform_stack_deletion(stack_name, region, valid_retain, logger)
        success_callback(f"Stack '{stack_name}' deletion initiated successfully")
    except Exception as e:
        # Handle deletion errors
        should_handle_gracefully = _handle_stack_deletion_error(
            e, stack_name, region, retain_resources_str, message_callback, logger
        )
        
        if should_handle_gracefully:
            return  # Exit gracefully for retention limitation error
        
        # For other errors, try to show partial failure info if possible
        try:
            _handle_stack_deletion_partial_failure(stack_name, region, resources, valid_retain, message_callback)
        except Exception:
            if logger:
                logger.debug("Failed to show partial failure information")
        
        # Re-raise the original exception
        raise
