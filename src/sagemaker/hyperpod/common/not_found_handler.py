"""
404 error handler that provides contextual error messages.
Main entry point for 404 error handling with integrated message generation.
"""

import logging
from .error_context import ContextGatherer, ErrorContext
from .error_constants import ResourceType, OperationType, RESOURCE_LIST_COMMANDS, RESOURCE_DISPLAY_NAMES

logger = logging.getLogger(__name__)

class NotFoundMessageGenerator:
    """Generates contextual 404 error messages based on error context."""
    
    def __init__(self):
        # Use constants from error_constants.py
        pass
    
    def generate_message(self, context: ErrorContext) -> str:
        """Generate 404 error message based on context."""
        # Priority order for different scenarios
        
        # 1. No resources available
        if context.available_count == 0:
            return self._generate_empty_namespace_message(context)
        
        # 2. Generic case with helpful commands
        return self._generate_generic_helpful_message(context)
    
    
    def _generate_empty_namespace_message(self, context: ErrorContext) -> str:
        """Generate message when no resources exist in namespace."""
        resource_display = self._get_resource_display_name(context.resource_type)
        
        # Get resource-specific list command
        list_command = self._get_list_command(context.resource_type)
        
        return (f"❓ {resource_display} '{context.resource_name}' not found in namespace '{context.namespace}'. "
               f"No resources of this type exist in the namespace. "
               f"Use '{list_command}' to check for available resources.")
    
    def _generate_generic_helpful_message(self, context: ErrorContext) -> str:
        """Generate generic message with helpful commands."""
        resource_display = self._get_resource_display_name(context.resource_type)
        
        # Only show --namespace if it's not the default namespace
        namespace_flag = f" --namespace {context.namespace}" if context.namespace != "default" else ""
        
        # Get resource-specific list command
        list_command = self._get_list_command(context.resource_type)
        
        return (f"❓ {resource_display} '{context.resource_name}' not found in namespace '{context.namespace}'. "
               f"Please check the resource name. There are {context.available_count} resources in this namespace. "
               f"Use '{list_command}{namespace_flag}' to see available resources.")
    
    def _get_resource_display_name(self, resource_type: ResourceType) -> str:
        """Get user-friendly display name for resource type."""
        return RESOURCE_DISPLAY_NAMES.get(resource_type, 'Resource')
    
    def _get_list_command(self, resource_type: ResourceType) -> str:
        """Get appropriate list command for resource type."""
        return RESOURCE_LIST_COMMANDS.get(resource_type, 'hyp list')


class NotFoundHandler:
    """Main handler for 404 error processing."""
    
    def __init__(self, enable_context_gathering: bool = True, timeout_seconds: float = 2.0):
        self.enable_context_gathering = enable_context_gathering
        self.context_gatherer = ContextGatherer(timeout_seconds=timeout_seconds)
        self.message_generator = NotFoundMessageGenerator()
    
    def generate_404_message(self, resource_name: str, namespace: str, 
                           resource_type: ResourceType, operation_type: OperationType = OperationType.DELETE) -> str:
        """Generate 404 error message with context."""
        if not self.enable_context_gathering:
            return self._generate_fallback_message(resource_name, namespace, resource_type)
        
        try:
            # Gather context
            context = self.context_gatherer.gather_context(
                resource_name, namespace, resource_type, operation_type
            )
            
            # Generate message
            return self.message_generator.generate_message(context)
            
        except Exception as e:
            logger.debug(f"404 handling failed: {e}")
            return self._generate_fallback_message(resource_name, namespace, resource_type)
    
    def _generate_fallback_message(self, resource_name: str, namespace: str, resource_type: ResourceType) -> str:
        """Generate improved fallback message when context gathering fails."""
        resource_display = RESOURCE_DISPLAY_NAMES.get(resource_type, 'Resource')
        
        return (f"{resource_display} '{resource_name}' not found in namespace '{namespace}'. "
               f"Please check the resource name and namespace.")

# Global instance for easy usage
_handler = NotFoundHandler()

def get_404_message(resource_name: str, namespace: str, resource_type: ResourceType, 
                   operation_type: OperationType = OperationType.DELETE) -> str:
    """Convenience function for getting 404 messages."""
    return _handler.generate_404_message(resource_name, namespace, resource_type, operation_type)
