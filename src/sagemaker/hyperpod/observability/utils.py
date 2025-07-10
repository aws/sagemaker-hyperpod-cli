import re
from typing import Optional

import boto3
import yaml

from sagemaker.hyperpod.observability.constants import AMAZON_HYPERPOD_OBSERVABILITY, GRAFANA_DASHBOARD_UID
from sagemaker.hyperpod.observability.MonitoringConfig import MonitoringConfig
# ToDO : move below functions to SDK util method instead of importing from CLI
from sagemaker.hyperpod.cli.utils import get_eks_cluster_name, get_hyperpod_cluster_region

def is_observability_addon_enabled(eks_cluster_name):
    response = boto3.client("eks").list_addons(clusterName=eks_cluster_name, maxResults=50)
    if AMAZON_HYPERPOD_OBSERVABILITY in response.get('addons', []):
        return True
    else:
        return False

def get_grafana_ws_name_from_arn(arn: str) -> str:
    """
    Parse the Grafana workspace name from a grafana workspace ARN.

    Args:
        arn (str): The ARN of the grafana workspace.

    Returns: str: The name of the grafana workspace name if parsing is successful.
    """
    # Define the regex pattern to match the Grafana workspace ARN and capture the workspace name
    pattern = r'g-[a-z0-9]+$'
    workspace_id = re.search(pattern, arn).group(0)
    #TODO : Add exception handling here.
    return workspace_id


def build_grafana_url(grafana_workspace, region, dashboardUid):
    grafana_url = f'https://{grafana_workspace}.grafana-workspace.{region}.amazonaws.com/d/{dashboardUid}'
    return grafana_url


def get_monitoring_config() -> Optional[MonitoringConfig]:
    eks_cluster_name = get_eks_cluster_name()
    if not is_observability_addon_enabled(eks_cluster_name):
        return None
    response = boto3.client("eks").describe_addon(clusterName=eks_cluster_name, addonName=AMAZON_HYPERPOD_OBSERVABILITY)
    config_values = yaml.safe_load(response['addon']['configurationValues'])

    try:
        prometheus_url = config_values['ampWorkspace']['prometheusEndpoint']
    except KeyError:
        prometheus_url = None
    try:
        region = get_hyperpod_cluster_region()
        workspace_arn = config_values['amgWorkspace']['arn']
        grafana_url = build_grafana_url(
            get_grafana_ws_name_from_arn(workspace_arn) if workspace_arn else "default-workspace", region,
            GRAFANA_DASHBOARD_UID)
    except KeyError:
        grafana_url = None
    try:
        metrics_data = config_values['metricsProvider']
    except KeyError:
        metrics_data = None

    return MonitoringConfig(grafanaURL=grafana_url, prometheusURL=prometheus_url, availableMetrics=metrics_data)
