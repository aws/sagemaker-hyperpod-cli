"""
Error context system for enhanced 404 error handling.
Provides contextual information to generate better error messages.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import difflib
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

logger = logging.getLogger(__name__)

@dataclass
class ErrorContext:
    """Context information for generating enhanced 404 error messages."""
    resource_name: str
    namespace: str
    resource_type: str  # 'training_job', 'inference_endpoint'
    operation_type: str = 'delete'
    
    # Context for better error messages
    similar_names: List[str] = field(default_factory=list)
    other_namespaces: List[str] = field(default_factory=list)
    recent_completions: List[str] = field(default_factory=list)
    available_count: int = 0

class ContextGatherer:
    """Responsible for gathering contextual information about 404 errors."""
    
    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout_seconds = timeout_seconds
    
    def gather_context(self, resource_name: str, namespace: str, resource_type: str, 
                      operation_type: str = 'delete') -> ErrorContext:
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
                future = executor.submit(self._gather_similar_names, context)
                try:
                    future.result(timeout=self.timeout_seconds)
                except FutureTimeoutError:
                    logger.debug(f"Context gathering timed out after {self.timeout_seconds}s")
                    # Continue with empty context
                
        except Exception as e:
            logger.debug(f"Context gathering failed: {e}")
            # Graceful fallback with empty context
        
        return context
    
    def _gather_similar_names(self, context: ErrorContext) -> None:
        """Gather similar resource names for typo detection."""
        try:
            available_names = self._get_available_resource_names(
                context.namespace, context.resource_type
            )
            context.available_count = len(available_names)
            context.similar_names = self._find_similar_names(
                context.resource_name, available_names
            )
        except Exception as e:
            logger.debug(f"Failed to gather similar names: {e}")
    
    def _get_available_resource_names(self, namespace: str, resource_type: str) -> List[str]:
        """Get list of available resource names in the namespace."""
        if resource_type == 'training_job':
            from sagemaker.hyperpod.training.hyperpod_pytorch_job import HyperPodPytorchJob
            available_jobs = HyperPodPytorchJob.list(namespace=namespace)
            return [job.metadata.name for job in available_jobs]
            
        elif resource_type == 'inference_endpoint':
            # Try both jumpstart and custom endpoints
            all_endpoints = []
            
            try:
                from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
                jumpstart_endpoints = HPJumpStartEndpoint.list(namespace=namespace)
                all_endpoints.extend([ep.metadata.name for ep in jumpstart_endpoints])
            except Exception as e:
                logger.debug(f"Failed to list jumpstart endpoints: {e}")
            
            try:
                from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint
                custom_endpoints = HPEndpoint.list(namespace=namespace)
                all_endpoints.extend([ep.metadata.name for ep in custom_endpoints])
            except Exception as e:
                logger.debug(f"Failed to list custom endpoints: {e}")
            
            return all_endpoints
        
        return []
    
    def _find_similar_names(self, target_name: str, available_names: List[str]) -> List[str]:
        """Find names similar to target using multiple similarity metrics."""
        similar = []
        target_lower = target_name.lower()
        
        for name in available_names:
            name_lower = name.lower()
            
            # Multiple similarity checks
            similarity_ratio = difflib.SequenceMatcher(None, target_lower, name_lower).ratio()
            
            if (similarity_ratio > 0.6 or  # Edit distance similarity
                target_lower in name_lower or name_lower in target_lower or  # Substring
                self._has_similar_words(target_lower, name_lower)):  # Word similarity
                similar.append(name)
        
        return similar[:3]  # Max 3 suggestions
    
    def _has_similar_words(self, target: str, candidate: str) -> bool:
        """Check if names have similar words (for compound names)."""
        target_words = set(target.replace('-', ' ').replace('_', ' ').split())
        candidate_words = set(candidate.replace('-', ' ').replace('_', ' ').split())
        
        if not target_words or not candidate_words:
            return False
            
        # Check if they share significant words
        common_words = target_words.intersection(candidate_words)
        return len(common_words) >= min(len(target_words), len(candidate_words)) * 0.5
