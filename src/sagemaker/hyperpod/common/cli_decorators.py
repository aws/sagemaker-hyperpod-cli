"""
CLI decorators for consistent error handling across all commands.
Template-agnostic design that dynamically detects resource and operation types.
"""

import sys
import click
import functools
import logging
from kubernetes.client.exceptions import ApiException

logger = logging.getLogger(__name__)

def _extract_resource_from_command(func) -> tuple[str, str]:
    """
    Extract resource type and display name from command context - template-agnostic.
    Simplified version focused on this codebase's specific Click usage patterns.
    
    Returns:
        Tuple of (raw_resource_type, display_name) where:
        - raw_resource_type: for list commands (e.g., "resource-type")  
        - display_name: for user messages (e.g., "Resource Type")
    """
    try:
        command_name = None
        
        # Method 1: Direct access to func.name (covers 90% of cases in this codebase)
        if hasattr(func, 'name') and func.name:
            command_name = func.name.lower()
        
        # Method 2: Check __wrapped__ attribute chain (for complex decorator combinations)
        elif hasattr(func, '__wrapped__'):
            wrapped = func.__wrapped__
            if hasattr(wrapped, 'name') and wrapped.name:
                command_name = wrapped.name.lower()
        
        # If we found a Click command name, parse it
        if command_name and command_name.startswith('hyp-'):
            resource_part = command_name[4:]  # Remove 'hyp-' prefix
            display_name = _format_display_name(resource_part)
            return resource_part, display_name
        
        # Fallback: extract from function name if no Click command found
        func_name = func.__name__.lower()
        if '_' in func_name:
            # "js_delete" -> "js", "custom_describe" -> "custom"
            prefix = func_name.split('_')[0]
            display_name = _format_display_name(prefix)
            return f"{prefix}-resource", display_name
            
    except (AttributeError, TypeError):
        pass
    
    return "resource", "Resource"  # Generic fallback

def _format_display_name(resource_part: str) -> str:
    """
    Format resource part into user-friendly display name.
    Completely template-agnostic - no hardcoded template names.
    """
    # Split on hyphens and capitalize each part
    parts = resource_part.split('-')
    formatted_parts = [part.capitalize() for part in parts]
    return ' '.join(formatted_parts)

def _get_list_command_from_resource_type(raw_resource_type: str) -> str:
    """
    Generate appropriate list command for resource type.
    Fully template-agnostic - constructs command directly from raw resource type.
    """
    # raw_resource_type is already in the correct format (e.g., "resource-type")
    return f"hyp list hyp-{raw_resource_type}"

def _check_resources_exist(raw_resource_type: str, namespace: str) -> bool:
    """
    Check if any resources exist in namespace - template-agnostic CLI approach.
    Uses the existing CLI commands to check for resource existence without importing template classes.
    Returns True if resources exist, False if no resources, None if unable to determine.
    """
    try:
        import subprocess
        
        # Construct the list command that already exists (use hyp directly)
        cmd = ["hyp", "list", f"hyp-{raw_resource_type}"]
        if namespace != "default":
            cmd.extend(["--namespace", namespace])
        
        logger.debug(f"Executing command to check resource existence: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,  
            timeout=15,  # 15 second timeout
            check=False  # Don't raise on non-zero exit
        )
        
        if result.returncode == 0 and result.stdout.strip():
            # Check if output contains any data rows (simple heuristic: more than 2 lines means header + separator + data)
            lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            
            # If we have more than 2 lines, likely we have: header + separator + at least one data row
            # This is much simpler and more reliable than parsing the table format
            has_data = len(lines) > 2
            
            logger.debug(f"Found {len(lines)} lines in output, has_data: {has_data}")
            return has_data
        
        # If command failed or no output, assume no resources
        logger.debug(f"List command failed or returned no data. Return code: {result.returncode}")
        return False
        
    except subprocess.TimeoutExpired:
        logger.debug(f"List command timed out for {raw_resource_type}")
        return None
    except Exception as e:
        logger.debug(f"Failed to check resource existence for {raw_resource_type}: {e}")
        return None

def handle_cli_exceptions():
    """
    Template-agnostic decorator that dynamically detects resource/operation types.
    
    This decorator:
    1. Dynamically detects resource type from Click command name
    2. Dynamically detects operation type from function name
    3. Applies enhanced 404 handling with contextual messages
    4. Handles all other exceptions consistently
    
    Usage:
        @handle_cli_exceptions()
        @click.command("hyp-resource-type")
        def resource_delete(name, namespace):
            # Command logic here - no try/catch needed!
            # Resource type automatically detected from command name
            # Operation type automatically detected from function name
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check if this is a 404 error that can benefit from enhanced handling
                if isinstance(e, ApiException) and e.status == 404:
                    # Extract name and namespace from kwargs if available
                    name = kwargs.get('name') or kwargs.get('job_name', 'unknown')
                    namespace = kwargs.get('namespace', 'default')
                    
                    # Dynamically detect resource and operation types
                    raw_resource_type, display_name = _extract_resource_from_command(func)
                    
                    try:
                        # Check if any resources exist for contextual message
                        resources_exist = _check_resources_exist(raw_resource_type, namespace)
                        list_command = _get_list_command_from_resource_type(raw_resource_type)
                        namespace_flag = f" --namespace {namespace}" if namespace != "default" else ""
                        
                        if resources_exist is False:
                            # No resources exist in namespace
                            enhanced_message = (
                                f"❓ {display_name} '{name}' not found in namespace '{namespace}'. "
                                f"No resources of this type exist in the namespace. "
                                f"Use '{list_command}' to check for available resources."
                            )
                        elif resources_exist is True:
                            # Resources exist in namespace
                            enhanced_message = (
                                f"❓ {display_name} '{name}' not found in namespace '{namespace}'. "
                                f"Please check the resource name - other resources exist in this namespace. "
                                f"Use '{list_command}{namespace_flag}' to see available resources."
                            )
                        else:
                            # Unable to determine - fallback to basic contextual message
                            enhanced_message = (
                                f"❓ {display_name} '{name}' not found in namespace '{namespace}'. "
                                f"Please check the resource name and try again. "
                                f"Use '{list_command}{namespace_flag}' to see available resources."
                            )
                        
                        click.echo(enhanced_message)
                        sys.exit(1)
                        return  # Prevent fallback execution in tests
                        
                    except Exception:
                        # Fallback to basic message (no ❓ emoji for fallback)
                        fallback_message = (
                            f"{display_name} '{name}' not found in namespace '{namespace}'. "
                            f"Please check the resource name and namespace."
                        )
                        click.echo(fallback_message)
                        sys.exit(1)
                        return  # Prevent fallback execution in tests
                
                # Check if this might be a wrapped 404 in a regular Exception
                elif "404" in str(e) or "not found" in str(e).lower():
                    # Extract name and namespace from kwargs if available
                    name = kwargs.get('name') or kwargs.get('job_name', 'unknown')
                    namespace = kwargs.get('namespace', 'default')
                    
                    # Get Click command name from context - this is the key to template-agnostic approach!
                    click_ctx = click.get_current_context(silent=True)
                    if click_ctx and hasattr(click_ctx, 'info_name'):
                        command_name = click_ctx.info_name
                        
                        if command_name.startswith('hyp-'):
                            # Parse the command name directly from Click context
                            resource_part = command_name[4:]  # Remove 'hyp-' prefix
                            display_name = _format_display_name(resource_part)
                            raw_resource_type = resource_part
                        else:
                            # Fallback to function-based extraction
                            raw_resource_type, display_name = _extract_resource_from_command(func)
                    else:
                        # No Click context - use function-based extraction
                        raw_resource_type, display_name = _extract_resource_from_command(func)
                    
                    try:
                        # Check if any resources exist for contextual message
                        resources_exist = _check_resources_exist(raw_resource_type, namespace)
                        list_command = _get_list_command_from_resource_type(raw_resource_type)
                        namespace_flag = f" --namespace {namespace}" if namespace != "default" else ""
                        
                        if resources_exist is False:
                            # No resources exist in namespace
                            enhanced_message = (
                                f"❓ {display_name} '{name}' not found in namespace '{namespace}'. "
                                f"No resources of this type exist in the namespace. "
                                f"Use '{list_command}' to check for available resources."
                            )
                        elif resources_exist is True:
                            # Resources exist in namespace
                            enhanced_message = (
                                f"❓ {display_name} '{name}' not found in namespace '{namespace}'. "
                                f"Please check the resource name - other resources exist in this namespace. "
                                f"Use '{list_command}{namespace_flag}' to see available resources."
                            )
                        else:
                            # Unable to determine - fallback to basic contextual message
                            enhanced_message = (
                                f"❓ {display_name} '{name}' not found in namespace '{namespace}'. "
                                f"Please check the resource name and try again. "
                                f"Use '{list_command}{namespace_flag}' to see available resources."
                            )
                        
                        click.echo(enhanced_message)
                        sys.exit(1)
                        return  # Prevent fallback execution in tests
                        
                    except Exception:
                        # Fall through to standard handling
                        pass
                
                # For non-404 errors, use standard handling 
                click.echo(str(e))
                sys.exit(1)
        
        return wrapper
    return decorator
