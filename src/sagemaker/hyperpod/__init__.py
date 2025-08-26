# Lazy loading implementation to avoid importing heavy dependencies until needed
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # Type hints for IDE support without runtime imports
    from .observability.MonitoringConfig import MonitoringConfig

# Define what should be available when someone does "from sagemaker.hyperpod import *"
__all__ = [
    # Common utilities (lazy loaded)
    'get_default_namespace',
    'handle_exception', 
    'get_eks_name_from_arn',
    'get_region_from_eks_arn',
    'get_jumpstart_model_instance_types',
    'get_cluster_instance_types',
    'setup_logging',
    'is_eks_orchestrator',
    'update_kube_config',
    'set_eks_context',
    'set_cluster_context',
    'get_cluster_context',
    'list_clusters',
    'get_current_cluster',
    'get_current_region',
    'parse_client_kubernetes_version',
    'is_kubernetes_version_compatible',
    'display_formatted_logs',
    'verify_kubernetes_version_compatibility',
    # Observability 
    'MonitoringConfig',
    # Constants
    'EKS_ARN_PATTERN',
    'CLIENT_VERSION_PATTERN',
    'KUBE_CONFIG_PATH'
]

def __getattr__(name: str) -> Any:
    """Lazy loading implementation for module-level imports"""
    
    # Lazy load from common.utils
    if name in [
        'get_default_namespace', 'handle_exception', 'get_eks_name_from_arn',
        'get_region_from_eks_arn', 'get_jumpstart_model_instance_types',
        'get_cluster_instance_types', 'setup_logging', 'is_eks_orchestrator',
        'update_kube_config', 'set_eks_context', 'set_cluster_context',
        'get_cluster_context', 'list_clusters', 'get_current_cluster',
        'get_current_region', 'parse_client_kubernetes_version',
        'is_kubernetes_version_compatible', 'display_formatted_logs',
        'verify_kubernetes_version_compatibility', 'EKS_ARN_PATTERN',
        'CLIENT_VERSION_PATTERN', 'KUBE_CONFIG_PATH'
    ]:
        from .common import utils
        attr = getattr(utils, name)
        # Cache the imported attribute for future access
        setattr(sys.modules[__name__], name, attr)
        return attr
    
    # Lazy load MonitoringConfig
    if name == 'MonitoringConfig':
        from .observability.MonitoringConfig import MonitoringConfig
        # Cache the imported class for future access
        setattr(sys.modules[__name__], name, MonitoringConfig)
        return MonitoringConfig
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
