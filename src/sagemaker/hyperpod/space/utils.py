"""Utility functions for space operations."""

import re
from typing import Dict, Any, Set
from pydantic import BaseModel


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_model_fields(model_class: BaseModel) -> Set[str]:
    """Get all field names from a Pydantic model."""
    return set(model_class.model_fields.keys())


def map_kubernetes_response_to_model(k8s_data: Dict[str, Any], model_class: BaseModel) -> Dict[str, Any]:
    """
    Map Kubernetes API response to model-compatible format.
    
    Args:
        k8s_data: Raw Kubernetes API response data
        model_class: Pydantic model class to map to
        
    Returns:
        Dict with fields mapped and filtered for the model
    """
    model_fields = get_model_fields(model_class)
    mapped_data = {}
    
    # Extract metadata fields
    if 'metadata' in k8s_data:
        metadata = k8s_data['metadata']
        if 'name' in metadata and 'name' in model_fields:
            mapped_data['name'] = metadata['name']
        if 'namespace' in metadata and 'namespace' in model_fields:
            mapped_data['namespace'] = metadata['namespace']
    
    # Extract and map spec fields
    if 'spec' in k8s_data:
        spec = k8s_data['spec']
        for k8s_field, value in spec.items():
            snake_field = camel_to_snake(k8s_field)
            if snake_field in model_fields:
                mapped_data[snake_field] = value
    
    # Extract and map status fields
    if 'status' in k8s_data:
        status = k8s_data['status']
        for k8s_field, value in status.items():
            snake_field = camel_to_snake(k8s_field)
            if snake_field in model_fields:
                mapped_data[snake_field] = value
    
    return mapped_data
