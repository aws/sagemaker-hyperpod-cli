# Lazy loading implementation to avoid importing heavy dependencies until needed
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Type hints for IDE support without runtime imports
    from .observability.MonitoringConfig import MonitoringConfig

from .common.lazy_loading import setup_lazy_module

HYPERPOD_CONFIG = {
    'exports': [
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
    ],
    'lazy_imports': {
        # Common utilities
        'get_default_namespace': 'sagemaker.hyperpod.common.utils:get_default_namespace',
        'handle_exception': 'sagemaker.hyperpod.common.utils:handle_exception',
        'get_eks_name_from_arn': 'sagemaker.hyperpod.common.utils:get_eks_name_from_arn',
        'get_region_from_eks_arn': 'sagemaker.hyperpod.common.utils:get_region_from_eks_arn',
        'get_jumpstart_model_instance_types': 'sagemaker.hyperpod.common.utils:get_jumpstart_model_instance_types',
        'get_cluster_instance_types': 'sagemaker.hyperpod.common.utils:get_cluster_instance_types',
        'setup_logging': 'sagemaker.hyperpod.common.utils:setup_logging',
        'is_eks_orchestrator': 'sagemaker.hyperpod.common.utils:is_eks_orchestrator',
        'update_kube_config': 'sagemaker.hyperpod.common.utils:update_kube_config',
        'set_eks_context': 'sagemaker.hyperpod.common.utils:set_eks_context',
        'set_cluster_context': 'sagemaker.hyperpod.common.utils:set_cluster_context',
        'get_cluster_context': 'sagemaker.hyperpod.common.utils:get_cluster_context',
        'list_clusters': 'sagemaker.hyperpod.common.utils:list_clusters',
        'get_current_cluster': 'sagemaker.hyperpod.common.utils:get_current_cluster',
        'get_current_region': 'sagemaker.hyperpod.common.utils:get_current_region',
        'parse_client_kubernetes_version': 'sagemaker.hyperpod.common.utils:parse_client_kubernetes_version',
        'is_kubernetes_version_compatible': 'sagemaker.hyperpod.common.utils:is_kubernetes_version_compatible',
        'display_formatted_logs': 'sagemaker.hyperpod.common.utils:display_formatted_logs',
        'verify_kubernetes_version_compatibility': 'sagemaker.hyperpod.common.utils:verify_kubernetes_version_compatibility',
        # Observability
        'MonitoringConfig': 'sagemaker.hyperpod.observability.MonitoringConfig:MonitoringConfig',
        # Constants
        'EKS_ARN_PATTERN': 'sagemaker.hyperpod.common.utils:EKS_ARN_PATTERN',
        'CLIENT_VERSION_PATTERN': 'sagemaker.hyperpod.common.utils:CLIENT_VERSION_PATTERN',
        'KUBE_CONFIG_PATH': 'sagemaker.hyperpod.common.utils:KUBE_CONFIG_PATH'
    }
}

setup_lazy_module(__name__, HYPERPOD_CONFIG)
