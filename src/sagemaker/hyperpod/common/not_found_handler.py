"""
404 error handler that provides contextual error messages.
Main entry point for 404 error handling with integrated message generation.
"""

import logging
from .error_context import ContextGatherer, ErrorContext

logger = logging.getLogger(__name__)

class NotFoundMessageGenerator:
    """Generates contextual 404 error messages based on error context."""
    
    def __init__(self):
        self.resource_display_names = {
            'training_job': 'Job',
            'inference_endpoint': 'Inference endpoint'
        }
        
        self.list_commands = {
            'training_job': 'hyp list hyp-pytorch-job',
            'inference_endpoint': "hyp list hyp-custom-endpoint' or 'hyp list hyp-jumpstart-endpoint"
        }
        
        # Comprehensive list commands for all resource types
        self.comprehensive_list_commands = "hyp list hyp-pytorch-job' or 'hyp list hyp-custom-endpoint' or 'hyp list hyp-jumpstart-endpoint"
    
    def generate_message(self, context: ErrorContext) -> str:
        """Generate 404 error message based on context."""
        # Priority order for different scenarios
        
        # 1. Typo detection (most actionable)
        if context.similar_names:
            return self._generate_typo_message(context)
        
        # 2. No resources available
        if context.available_count == 0:
            return self._generate_empty_namespace_message(context)
        
        # 3. Generic case with helpful commands
        return self._generate_generic_helpful_message(context)
    
    def _generate_typo_message(self, context: ErrorContext) -> str:
        """Generate message suggesting similar names (typo detection)."""
        resource_display = self._get_resource_display_name(context.resource_type)
        suggestions = "', '".join(context.similar_names)
        
        # Only show --namespace if it's not the default namespace
        namespace_flag = f" --namespace {context.namespace}" if context.namespace != "default" else ""
        
        return (f"❓ {resource_display} '{context.resource_name}' not found in namespace '{context.namespace}'. "
               f"Did you mean '{suggestions}'? "
               f"Use '{self.comprehensive_list_commands}{namespace_flag}' to see all available resources.")
    
    def _generate_empty_namespace_message(self, context: ErrorContext) -> str:
        """Generate message when no resources exist in namespace."""
        resource_display = self._get_resource_display_name(context.resource_type)
        
        return (f"❓ {resource_display} '{context.resource_name}' not found in namespace '{context.namespace}'. "
               f"No resources of this type exist in the namespace. "
               f"Use '{self.comprehensive_list_commands}' to see resources in other namespaces.")
    
    def _generate_generic_helpful_message(self, context: ErrorContext) -> str:
        """Generate generic message with helpful commands."""
        resource_display = self._get_resource_display_name(context.resource_type)
        
        # Only show --namespace if it's not the default namespace
        namespace_flag = f" --namespace {context.namespace}" if context.namespace != "default" else ""
        
        return (f"❓ {resource_display} '{context.resource_name}' not found in namespace '{context.namespace}'. "
               f"Please check the resource name. There are {context.available_count} resources in this namespace. "
               f"Use '{self.comprehensive_list_commands}{namespace_flag}' to see available resources.")
    
    def _get_resource_display_name(self, resource_type: str) -> str:
        """Get user-friendly display name for resource type."""
        return self.resource_display_names.get(resource_type, 'Resource')
    
    def _get_list_command(self, resource_type: str) -> str:
        """Get appropriate list command for resource type."""
        return self.list_commands.get(resource_type, 'hyp list')


class NotFoundHandler:
    """Main handler for 404 error processing."""
    
    def __init__(self, enable_context_gathering: bool = True, timeout_seconds: float = 2.0):
        self.enable_context_gathering = enable_context_gathering
        self.context_gatherer = ContextGatherer(timeout_seconds=timeout_seconds)
        self.message_generator = NotFoundMessageGenerator()
    
    def generate_404_message(self, resource_name: str, namespace: str, 
                           resource_type: str, operation_type: str = 'delete') -> str:
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
    
    def _generate_fallback_message(self, resource_name: str, namespace: str, resource_type: str) -> str:
        """Generate improved fallback message when context gathering fails."""
        resource_display = {
            'training_job': 'Job',
            'inference_endpoint': 'Inference endpoint'
        }.get(resource_type, 'Resource')
        
        return (f"{resource_display} '{resource_name}' not found in namespace '{namespace}'. "
               f"Please check the resource name and namespace.")

# Global instance for easy usage
_handler = NotFoundHandler()

def get_404_message(resource_name: str, namespace: str, resource_type: str, 
                   operation_type: str = 'delete') -> str:
    """Convenience function for getting 404 messages."""
    return _handler.generate_404_message(resource_name, namespace, resource_type, operation_type)
