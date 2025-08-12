# Lazy imports for public API - only load when actually used
def list_clusters(region=None):
    """List HyperPod clusters."""
    from .common.utils import list_clusters as _list_clusters
    return _list_clusters(region)

def set_cluster_context(cluster_name, region=None, namespace=None):
    """Set cluster context."""
    from .common.utils import set_cluster_context as _set_cluster_context
    return _set_cluster_context(cluster_name, region, namespace)

def get_cluster_context():
    """Get current cluster context."""
    from .common.utils import get_cluster_context as _get_cluster_context
    return _get_cluster_context()

# Other utility functions can be added here as needed
# MonitoringConfig removed as it's not part of public API