"""
CLI decorators for consistent error handling across all commands.
"""

import sys
import click
import functools
import logging
from kubernetes.client.exceptions import ApiException
from .utils import handle_404
from .error_constants import ResourceType, OperationType

logger = logging.getLogger(__name__)

def handle_cli_exceptions(func):
    """
    Decorator that provides consistent exception handling for CLI commands.
    
    Replaces the repetitive pattern:
        except Exception as e:
            click.echo(str(e))
            import sys
            sys.exit(1)
    
    Usage:
        @handle_cli_exceptions
        @click.command()
        def my_command():
            # Command logic here
            pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Clean error output - no "Error:" prefix or "Aborted!" suffix
            click.echo(str(e))
            sys.exit(1)
    
    return wrapper

def handle_cli_exceptions_with_debug(func):
    """
    Enhanced decorator that provides debug information when requested.
    
    This version logs the full exception details for debugging purposes
    while still showing clean messages to users.
    
    Usage:
        @handle_cli_exceptions_with_debug
        @click.command()
        def my_command():
            # Command logic here
            pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log full exception details for debugging
            logger.debug(f"CLI command failed: {func.__name__}", exc_info=True)
            
            # Clean error output for users
            click.echo(str(e))
            sys.exit(1)
    
    return wrapper


def smart_cli_exception_handler(func):
    """
    Smart decorator that automatically detects resource/operation types and applies
    enhanced 404 handling. Eliminates repetitive exception handling across CLI commands.
    
    This decorator:
    1. Auto-detects resource type from command name (hyp-jumpstart-endpoint, etc.)
    2. Auto-detects operation type from function name (delete, describe, etc.)
    3. Applies enhanced 404 handling with contextual messages
    4. Handles all other exceptions consistently
    
    Usage:
        @smart_cli_exception_handler
        @click.command("hyp-jumpstart-endpoint")
        def js_delete(name, namespace):
            # Command logic here - no try/catch needed!
            pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Check if this is a 404 error that can benefit from enhanced handling
            if isinstance(e, ApiException) and e.status == 404:
                # Auto-detect resource and operation types
                resource_type = _detect_resource_type(func)
                operation_type = _detect_operation_type(func)
                
                # Extract name and namespace from kwargs if available
                name = kwargs.get('name', 'unknown')
                namespace = kwargs.get('namespace', 'default')
                
                if resource_type and operation_type:
                    try:
                        handle_404(name, namespace, resource_type, operation_type)
                    except Exception as enhanced_error:
                        click.echo(str(enhanced_error))
                        sys.exit(1)
            
            # For non-404 errors or when auto-detection fails, use standard handling
            logger.debug(f"CLI command failed: {func.__name__}", exc_info=True)
            click.echo(str(e))
            sys.exit(1)
    
    return wrapper


def _detect_resource_type(func) -> ResourceType:
    """
    Auto-detect resource type from function name or click command name.
    
    Args:
        func: The decorated function
        
    Returns:
        ResourceType enum or None if not detected
    """
    try:
        # First try to get the Click command name from the decorator
        if hasattr(func, 'name'):
            command_name = func.name.lower()
            if 'jumpstart' in command_name:
                return ResourceType.HYP_JUMPSTART_ENDPOINT
            elif 'custom' in command_name:
                return ResourceType.HYP_CUSTOM_ENDPOINT
            elif 'pytorch' in command_name:
                return ResourceType.HYP_PYTORCH_JOB
        
        # Fallback to function name detection
        try:
            func_name = func.__name__.lower()
        except (AttributeError, TypeError):
            func_name = ""
        
        # Function name patterns
        if 'js_' in func_name or 'jumpstart' in func_name:
            return ResourceType.HYP_JUMPSTART_ENDPOINT
        elif 'custom' in func_name:
            return ResourceType.HYP_CUSTOM_ENDPOINT
        elif 'pytorch' in func_name or 'training' in func_name:
            return ResourceType.HYP_PYTORCH_JOB
        
        return None
        
    except Exception:
        # Handle any other exceptions during detection gracefully
        return None


def _detect_operation_type(func) -> OperationType:
    """
    Auto-detect operation type from function name.
    
    Args:
        func: The decorated function
        
    Returns:
        OperationType enum or None if not detected
    """
    try:
        func_name = func.__name__.lower()
        
        if 'delete' in func_name:
            return OperationType.DELETE
        elif 'describe' in func_name or 'get' in func_name:
            return OperationType.DESCRIBE
        elif 'list' in func_name:
            return OperationType.LIST
        
        return OperationType.GET  # Default fallback
        
    except (AttributeError, TypeError, Exception):
        # Handle any exceptions during detection gracefully
        return OperationType.GET  # Default fallback
