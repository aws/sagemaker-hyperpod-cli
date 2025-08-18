"""
CLI decorators for consistent error handling across all commands.
"""

import sys
import click
import functools
import logging
from kubernetes.client.exceptions import ApiException
from .utils import handle_404
from .exceptions.error_constants import ResourceType, OperationType

logger = logging.getLogger(__name__)

def handle_cli_exceptions(resource_type=None, operation_type=None):
    """
    Decorator that applies enhanced 404 handling with explicit resource/operation types.
    Eliminates repetitive exception handling across CLI commands.
    
    This decorator:
    1. Uses explicit resource_type and operation_type parameters
    2. Applies enhanced 404 handling with contextual messages
    3. Handles all other exceptions consistently
    
    Usage:
        @handle_cli_exceptions(
            resource_type=ResourceType.HYP_JUMPSTART_ENDPOINT,
            operation_type=OperationType.DELETE
        )
        @click.command("hyp-jumpstart-endpoint")
        def js_delete(name, namespace):
            # Command logic here - no try/catch needed!
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
                    name = kwargs.get('name', 'unknown')
                    namespace = kwargs.get('namespace', 'default')
                    
                    if resource_type and operation_type:
                        try:
                            handle_404(name, namespace, resource_type, operation_type)
                        except Exception as enhanced_error:
                            click.echo(str(enhanced_error))
                            sys.exit(1)
                
                # For non-404 errors or when parameters not provided, use standard handling
                logger.debug(f"CLI command failed: {func.__name__}", exc_info=True)
                click.echo(str(e))
                sys.exit(1)
        
        return wrapper
    return decorator
