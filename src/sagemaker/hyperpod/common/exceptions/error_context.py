"""
Error context system for enhanced 404 error handling.
Provides contextual information to generate better error messages.
"""

from dataclasses import dataclass
from typing import List
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from .error_constants import ResourceType, OperationType

logger = logging.getLogger(__name__)

@dataclass
class ErrorContext:
    """Context information for generating enhanced 404 error messages."""
    resource_name: str
    namespace: str
    resource_type: ResourceType
    operation_type: OperationType = OperationType.DELETE
    
    # Context for better error messages
    available_count: int = 0

class ContextGatherer:
    """Responsible for gathering contextual information about 404 errors."""
    
    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout_seconds = timeout_seconds
    
    def gather_context(self, resource_name: str, namespace: str, resource_type: ResourceType, 
                      operation_type: OperationType = OperationType.DELETE) -> ErrorContext:
        """Gather contextual information with timeout protection."""
        context = ErrorContext(
            resource_name=resource_name,
            namespace=namespace, 
            resource_type=resource_type,
            operation_type=operation_type
        )
        
        try:
            # Use ThreadPoolExecutor for timeout protection
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._gather_resource_count, context)
                try:
                    future.result(timeout=self.timeout_seconds)
                except FutureTimeoutError:
                    logger.debug(f"Context gathering timed out after {self.timeout_seconds}s")
                    # Continue with empty context
                
        except Exception as e:
            logger.debug(f"Context gathering failed: {e}")
            # Graceful fallback with empty context
        
        return context
    
    def _gather_resource_count(self, context: ErrorContext) -> None:
        """Gather resource count for better error messages."""
        try:
            available_names = self._get_available_resource_names(
                context.namespace, context.resource_type
            )
            context.available_count = len(available_names)
        except Exception as e:
            logger.debug(f"Failed to gather resource count: {e}")
    
    def _get_available_resource_names(self, namespace: str, resource_type: ResourceType) -> List[str]:
        """Get list of available resource names in the namespace."""
        if resource_type == ResourceType.HYP_PYTORCH_JOB:
            from sagemaker.hyperpod.training.hyperpod_pytorch_job import HyperPodPytorchJob
            available_jobs = HyperPodPytorchJob.list(namespace=namespace)
            return [job.metadata.name for job in available_jobs]
            
        elif resource_type == ResourceType.HYP_JUMPSTART_ENDPOINT:
            try:
                from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
                jumpstart_endpoints = HPJumpStartEndpoint.list(namespace=namespace)
                return [ep.metadata.name for ep in jumpstart_endpoints]
            except Exception as e:
                logger.debug(f"Failed to list jumpstart endpoints: {e}")
                return []
            
        elif resource_type == ResourceType.HYP_CUSTOM_ENDPOINT:
            try:
                from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint
                custom_endpoints = HPEndpoint.list(namespace=namespace)
                return [ep.metadata.name for ep in custom_endpoints]
            except Exception as e:
                logger.debug(f"Failed to list custom endpoints: {e}")
                return []
        
        return []
