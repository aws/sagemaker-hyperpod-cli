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
    Extract resource type and display name from command context - fully template-agnostic.
    No hardcoded mappings - works with any hyp-<noun> pattern.
    
    Returns:
        Tuple of (raw_resource_type, display_name) where:
        - raw_resource_type: for list commands (e.g., "jumpstart-endpoint")  
        - display_name: for user messages (e.g., "JumpStart endpoint")
    """
    try:
        # Try multiple ways to get Click command name - template-agnostic
        command_name = None
        
        # Method 1: Direct access to func.name (if available)
        if hasattr(func, 'name') and func.name:
            command_name = func.name.lower()
        
        # Method 2: Access Click command through function attributes
        elif hasattr(func, 'callback') and hasattr(func.callback, 'name'):
            command_name = func.callback.name.lower()
        
        # Method 3: Check __wrapped__ attribute chain
        elif hasattr(func, '__wrapped__'):
            wrapped = func.__wrapped__
            if hasattr(wrapped, 'name') and wrapped.name:
                command_name = wrapped.name.lower()
        
        # Method 4: Inspect all function attributes for Click command info
        for attr_name in dir(func):
            if not attr_name.startswith('_'):
                try:
                    attr_value = getattr(func, attr_name)
                    if hasattr(attr_value, 'name') and isinstance(getattr(attr_value, 'name', None), str):
                        attr_name_val = attr_value.name
                        if attr_name_val and attr_name_val.startswith('hyp-'):
                            command_name = attr_name_val.lower()
                            break
                except:
                    continue
        
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
    Template-agnostic formatting rules.
    """
    # Handle common patterns with proper capitalization
    parts = resource_part.split('-')
    formatted_parts = []
    
    for part in parts:
        if part.lower() == 'jumpstart':
            formatted_parts.append('JumpStart')
        elif part.lower() == 'pytorch':
            formatted_parts.append('PyTorch')
        else:
            # Capitalize first letter of other parts
            formatted_parts.append(part.capitalize())
    
    return ' '.join(formatted_parts)

def _detect_operation_type_from_function(func) -> str:
    """
    Dynamically detect operation type from function name.
    Template-agnostic - works with any operation pattern.
    
    Returns:
        Operation type string (e.g., "delete", "describe", "list")
    """
    try:
        func_name = func.__name__.lower()
        
        if 'delete' in func_name:
            return "delete"
        elif 'describe' in func_name or 'get' in func_name:
            return "describe"
        elif 'list' in func_name:
            return "list"
        elif 'create' in func_name:
            return "create"
        elif 'update' in func_name:
            return "update"
            
    except (AttributeError, TypeError):
        pass
    
    return "access"  # Generic fallback

def _get_list_command_from_resource_type(raw_resource_type: str) -> str:
    """
    Generate appropriate list command for resource type.
    Fully template-agnostic - constructs command directly from raw resource type.
    """
    # raw_resource_type is already in the correct format (e.g., "jumpstart-endpoint")
    return f"hyp list hyp-{raw_resource_type}"

def _get_available_resource_count(raw_resource_type: str, namespace: str) -> int:
    """
    Get count of available resources in namespace - template-agnostic approach.
    Maps exact resource types to their SDK classes.
    """
    try:
        # Direct mapping based on exact resource type - truly template-agnostic
        if raw_resource_type == "pytorch-job":
            from sagemaker.hyperpod.training.hyperpod_pytorch_job import HyperPodPytorchJob
            jobs = HyperPodPytorchJob.list(namespace=namespace)
            return len(jobs)
            
        elif raw_resource_type == "jumpstart-endpoint":
            from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
            endpoints = HPJumpStartEndpoint.model_construct().list(namespace=namespace) 
            return len(endpoints)
            
        elif raw_resource_type == "custom-endpoint":
            from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint
            endpoints = HPEndpoint.model_construct().list(namespace=namespace)
            return len(endpoints)
            
        # Future templates will be added here as exact matches
        # elif raw_resource_type == "llama-job":
        #     from sagemaker.hyperpod.training.hyperpod_llama_job import HyperPodLlamaJob
        #     jobs = HyperPodLlamaJob.list(namespace=namespace)
        #     return len(jobs)
            
    except Exception as e:
        logger.debug(f"Failed to get resource count for {raw_resource_type}: {e}")
    
    return -1  # Indicates count unavailable

def handle_cli_exceptions():
    """
    Template-agnostic decorator that dynamically detects resource/operation types.
    Eliminates the need for hardcoded enums and makes CLI code template-agnostic.
    
    This decorator:
    1. Dynamically detects resource type from Click command name
    2. Dynamically detects operation type from function name
    3. Applies enhanced 404 handling with contextual messages
    4. Handles all other exceptions consistently
    
    Usage:
        @handle_cli_exceptions()
        @click.command("hyp-jumpstart-endpoint")
        def js_delete(name, namespace):
            # Command logic here - no try/catch needed!
            # Resource type automatically detected as "JumpStart endpoint"
            # Operation type automatically detected as "delete"
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
                    operation_type = _detect_operation_type_from_function(func)
                    
                    try:
                        # Get available resource count for contextual message
                        available_count = _get_available_resource_count(raw_resource_type, namespace)
                        list_command = _get_list_command_from_resource_type(raw_resource_type)
                        namespace_flag = f" --namespace {namespace}" if namespace != "default" else ""
                        
                        if available_count == 0:
                            # No resources exist in namespace
                            enhanced_message = (
                                f"❓ {display_name} '{name}' not found in namespace '{namespace}'. "
                                f"No resources of this type exist in the namespace. "
                                f"Use '{list_command}' to check for available resources."
                            )
                        elif available_count > 0:
                            # Resources exist in namespace
                            enhanced_message = (
                                f"❓ {display_name} '{name}' not found in namespace '{namespace}'. "
                                f"Please check the resource name. There are {available_count} resources in this namespace. "
                                f"Use '{list_command}{namespace_flag}' to see available resources."
                            )
                        else:
                            # Count unavailable - fallback to basic contextual message
                            enhanced_message = (
                                f"❓ {display_name} '{name}' not found in namespace '{namespace}'. "
                                f"Please check the resource name and try again. "
                                f"Use '{list_command}{namespace_flag}' to see available resources."
                            )
                        
                        click.echo(enhanced_message)
                        sys.exit(1)
                        
                    except Exception:
                        # Fallback to basic message (no ❓ emoji for fallback)
                        fallback_message = (
                            f"{display_name} '{name}' not found in namespace '{namespace}'. "
                            f"Please check the resource name and namespace."
                        )
                        click.echo(fallback_message)
                        sys.exit(1)
                
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
                        # Get available resource count for contextual message
                        available_count = _get_available_resource_count(raw_resource_type, namespace)
                        list_command = _get_list_command_from_resource_type(raw_resource_type)
                        namespace_flag = f" --namespace {namespace}" if namespace != "default" else ""
                        
                        if available_count == 0:
                            enhanced_message = (
                                f"❓ {display_name} '{name}' not found in namespace '{namespace}'. "
                                f"No resources of this type exist in the namespace. "
                                f"Use '{list_command}' to check for available resources."
                            )
                        elif available_count > 0:
                            enhanced_message = (
                                f"❓ {display_name} '{name}' not found in namespace '{namespace}'. "
                                f"Please check the resource name. There are {available_count} resources in this namespace. "
                                f"Use '{list_command}{namespace_flag}' to see available resources."
                            )
                        else:
                            enhanced_message = (
                                f"❓ {display_name} '{name}' not found in namespace '{namespace}'. "
                                f"Please check the resource name and try again. "
                                f"Use '{list_command}{namespace_flag}' to see available resources."
                            )
                        
                        click.echo(enhanced_message)
                        sys.exit(1)
                        
                    except Exception:
                        # Fall through to standard handling
                        pass
                
                # For non-404 errors, use standard handling
                click.echo(str(e))
                sys.exit(1)
        
        return wrapper
    return decorator
