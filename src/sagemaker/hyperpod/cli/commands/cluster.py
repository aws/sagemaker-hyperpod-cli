# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
import logging
import subprocess
import json
import sys
import botocore.config
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import boto3
import click
from botocore.client import BaseClient
from kubernetes import client
from ratelimit import limits, sleep_and_retry
from tabulate import tabulate

from sagemaker.hyperpod.cli.clients.kubernetes_client import (
    KubernetesClient,
)
from sagemaker.hyperpod.cli.constants.command_constants import (
    AVAILABLE_ACCELERATOR_DEVICES_KEY,
    DEEP_HEALTH_CHECK_STATUS_LABEL,
    HP_HEALTH_STATUS_LABEL,
    HYPERPOD_NAMESPACE_PREFIX,
    INSTANCE_TYPE_LABEL,
    NVIDIA_GPU_RESOURCE_LIMIT_KEY,
    SAGEMAKER_HYPERPOD_NAME_LABEL,
    SAGEMAKER_MANAGED_CLUSTER_QUEUE_SUFFIX,
    SAGEMAKER_QUOTA_ALLOCATION_LABEL,
    TOTAL_ACCELERATOR_DEVICES_KEY,
    TEMP_KUBE_CONFIG_FILE,
    OutputFormat,
)
from sagemaker.hyperpod.cli.telemetry.user_agent import (
    get_user_agent_extra_suffix,
)
from sagemaker.hyperpod.cli.service.list_pods import (
    ListPods,
)
from sagemaker.hyperpod.cli.utils import (
    get_name_from_arn,
    get_sagemaker_client,
    setup_logger,
    set_logging_level,
    store_current_hyperpod_context,
)
from sagemaker.hyperpod.cli.validators.cluster_validator import (
    ClusterValidator,
)
from sagemaker.hyperpod.cli.utils import (
    get_eks_cluster_name,
)
from sagemaker.hyperpod.common.utils import get_cluster_context as get_cluster_context_util
from sagemaker.hyperpod.observability.utils import get_monitoring_config, is_observability_addon_enabled

RATE_LIMIT = 4
RATE_LIMIT_PERIOD = 1  # 1 second

logger = setup_logger(__name__)


@click.command()
@click.option(
    "--region",
    type=click.STRING,
    required=False,
    help="Optional. The region that the HyperPod and EKS clusters are located. If not specified, it will be set to the region from the current AWS account credentials.",
)
@click.option(
    "--output",
    type=click.Choice([c.value for c in OutputFormat]),
    required=False,
    default=OutputFormat.JSON.value,
    help="Optional. The output format. Available values are `TABLE` and `JSON`. The default value is `JSON`.",
)
@click.option(
    "--clusters",
    type=click.STRING,
    required=False,
    help="Optional. A list of HyperPod cluster names that users want to check the capacity for. This is useful for users who know some of their most commonly used clusters and want to check the capacity status of the clusters in the AWS account.",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode",
)
@click.option(
    "--namespace",
    "-n",
    type=click.STRING,
    required=False,
    multiple=True,
    help="Optional. The namespace that you want to check the capacity for. Only SageMaker managed namespaces are supported.",
)
def list_cluster(
    region: Optional[str],
    output: Optional[str],
    clusters: Optional[str],
    debug: bool,
    namespace: Optional[List]
):
    """List SageMaker Hyperpod Clusters with cluster metadata.

    Example Usage:
    1. List clusters with JSON output: hyperpod get-clusters -n hyperpod-ns-test-team

    Output:
        [
            {
                "Cluster": "hyperpod-eks-cluster-a",
                "InstanceType": "ml.g5.2xlarge",
                "TotalNodes": 2,
                "AcceleratorDevicesAvailable": 1,
                "NodeHealthStatus=Schedulable": 2,
                "DeepHealthCheckStatus=Passed": "N/A",
                "Namespaces": {
                    "hyperpod-ns-test-team": {
                        "AvailableAcceleratorDevices": 1,
                        "TotalAcceleratorDevices": 1
                    }
                }
            }
        ]

    2. List clusters with table output: hyperpod get-clusters -n hyperpod-ns-test-team --output table

    Output:
         Cluster                | InstanceType   |   TotalNodes | AcceleratorDevicesAvailable   |   NodeHealthStatus=Schedulable | DeepHealthCheckStatus=Passed | hyperpod-ns-test-teamTotalAcceleratorDevices   | hyperpod-ns-test-teamAvailableAcceleratorDevices
         -----------------------+----------------+--------------+-------------------------------+--------------------------------+------------------------------+------------------------------------------------+----------------------------------------------------
         hyperpod-eks-cluster-a | ml.g5.2xlarge  |            2 |                              1|                              2 |                          N/A | 1                                              | 1
    """
    if debug:
        set_logging_level(logger, logging.DEBUG)
    validator = ClusterValidator()

    # Make use of user_agent_extra field of the botocore_config object
    # to append SageMaker Hyperpod CLI specific user_agent suffix
    # to the current User-Agent header value from boto3
    # This config will also make sure that user_agent never fails to log the User-Agent string
    # even if boto User-Agent header format is updated in the future
    # Ref: https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html
    botocore_config = botocore.config.Config(
        user_agent_extra=get_user_agent_extra_suffix()
    )

    session = boto3.Session(region_name=region) if region else boto3.Session()
    if not validator.validate_aws_credential(session):
        logger.error("Failed to list clusters capacity due to invalid AWS credentials.")
        sys.exit(1)

    try:
        sm_client = get_sagemaker_client(session, botocore_config)
    except botocore.exceptions.NoRegionError:
        logger.error(
            f"Please ensure you have configured the AWS default region or use the '--region' argument to specify the region."
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to initialize the SageMaker client: {e}")
        sys.exit(1)

    if clusters:
        cluster_names = clusters.split(",")
    else:
        try:
            cluster_names = _get_hyperpod_clusters(sm_client)
        except Exception as e:
            logger.error(f"Failed to list HyperPod clusters due to an error: {e}")
            sys.exit(1)

    cluster_capacities: List[List[str]] = []

    counter = 0
    for cluster_name in cluster_names:
        current_cluster_capacities_size = len(cluster_capacities)
        rate_limited_operation(
            cluster_name=cluster_name,
            validator=validator,
            sm_client=sm_client,
            region=region,
            temp_config_file=TEMP_KUBE_CONFIG_FILE,
            cluster_capacities=cluster_capacities,
            namespace=namespace,
        )
        # cluster_capacities will only be updated when the cluster
        # is a valid Hyperpod EKS cluster. This check avoid
        # we skipped many Hyperpod Slurm clusters and didn't return
        # any Hyperpod EKS clusters.
        if len(cluster_capacities) > current_cluster_capacities_size:
            counter += 1
        # Currently only support list <= 50 clusters
        if counter >= 50:
            logger.debug(
                "The 'get-clusters' command has reached the maximum number of HyperPod clusters that can be listed, which is 50."
            )
            break

    headers = [
        "Cluster",
        "InstanceType",
        "TotalNodes",
        "AcceleratorDevicesAvailable",
        "NodeHealthStatus=Schedulable",
        "DeepHealthCheckStatus=Passed",
    ]

    if namespace is not None:
        for ns in namespace:
            headers.append(ns + TOTAL_ACCELERATOR_DEVICES_KEY)
            headers.append(ns + AVAILABLE_ACCELERATOR_DEVICES_KEY)
    if output == OutputFormat.TABLE.value:
        print(tabulate(cluster_capacities, headers=headers, tablefmt="presto"))
    elif output == OutputFormat.JSON.value:
        json_list = [dict(zip(headers, value)) for value in cluster_capacities]
        _restructure_output(json_list, namespace)
        print(json.dumps(json_list, indent=4))


@sleep_and_retry
@limits(calls=RATE_LIMIT, period=RATE_LIMIT_PERIOD)
def rate_limited_operation(
    cluster_name: str,
    validator: ClusterValidator,
    sm_client: BaseClient,
    region: Optional[str],
    temp_config_file: str,
    cluster_capacities: List[List[str]],
    namespace: Optional[List[str]],
) -> None:
    try:
        eks_cluster_arn = validator.validate_cluster_and_get_eks_arn(
            cluster_name, sm_client
        )
        if eks_cluster_arn is None:
            logger.warning(
                f"Cannot find EKS cluster behind {cluster_name}, continue..."
            )
            return
        eks_cluster_name = get_name_from_arn(eks_cluster_arn)
        _update_kube_config(eks_cluster_name, region, temp_config_file)
        k8s_client = KubernetesClient(is_get_capacity=True)
        nodes = k8s_client.list_node_with_temp_config(
            temp_config_file, SAGEMAKER_HYPERPOD_NAME_LABEL
        )
        nodes_info = _aggregate_nodes_info(nodes)

        ns_nominal_quota = {}
        ns_quota_usage = {}

        for ns in namespace:
            sm_managed_namespace = k8s_client.get_sagemaker_managed_namespace(ns)
            if sm_managed_namespace:
                quota_allocation_id = sm_managed_namespace.metadata.labels[SAGEMAKER_QUOTA_ALLOCATION_LABEL]
                cluster_queue_name = HYPERPOD_NAMESPACE_PREFIX + quota_allocation_id + SAGEMAKER_MANAGED_CLUSTER_QUEUE_SUFFIX
                cluster_queue = k8s_client.get_cluster_queue(cluster_queue_name)
                nominal_quota = _get_cluster_queue_nominal_quota(cluster_queue)
                quota_usage = _get_cluster_queue_quota_usage(cluster_queue)
                ns_nominal_quota[ns] = nominal_quota
                ns_quota_usage[ns] = quota_usage
            else:
                ns_nominal_quota[ns] = {}
                ns_quota_usage[ns] = {}

        for instance_type, nodes_summary in nodes_info.items():
            capacities = [
                cluster_name,
                instance_type,
                nodes_summary["total_nodes"],
                nodes_summary["accelerator_devices_available"],
                nodes_summary["schedulable"],
                nodes_summary["deep_health_check_passed"],
            ]
            for ns in namespace:
                capacities.append(ns_nominal_quota.get(ns).get(instance_type, {}).get(NVIDIA_GPU_RESOURCE_LIMIT_KEY, "N/A"))
                capacities.append(_get_available_quota(ns_nominal_quota.get(ns), ns_quota_usage.get(ns), instance_type, NVIDIA_GPU_RESOURCE_LIMIT_KEY))
            cluster_capacities.append(capacities)
    except Exception as e:
        logger.error(f"Error processing cluster {cluster_name}: {e}, continue...")


def _get_cluster_queue_nominal_quota(cluster_queue):
    nominal_quota = {}
    resource_groups = cluster_queue.get("spec", {}).get("resourceGroups", [])
    resource_group = resource_groups[0]

    for flavor in resource_group.get("flavors", []):
        flavor_name = flavor.get("name", "unknown")
        resources = flavor.get("resources", [])
        for resource in resources:
            resource_name = resource.get("name")
            quota = resource.get("nominalQuota")
            if flavor_name not in nominal_quota:
                nominal_quota[flavor_name] = {}
            if resource_name == NVIDIA_GPU_RESOURCE_LIMIT_KEY:
                quota = int(quota)
            nominal_quota[flavor_name][resource_name] = quota
    
    return nominal_quota


def _get_cluster_queue_quota_usage(cluster_queue):
    quota_usage = {}
    flavor_usage = cluster_queue.get("status", {}).get("flavorsUsage", [])

    for flavor in flavor_usage:
        flavor_name = flavor.get("name", "unknown")
        resources = flavor.get("resources", [])
        for resource in resources:
            resource_name = resource.get("name")
            usage = resource.get("total")
            if flavor_name not in quota_usage:
                quota_usage[flavor_name] = {}
            if resource_name == NVIDIA_GPU_RESOURCE_LIMIT_KEY:
                usage = int(usage)
            quota_usage[flavor_name][resource_name] = usage

    return quota_usage


def _get_available_quota(nominal, usage, flavor, resource_name):
    nominal_quota = nominal.get(flavor, {}).get(resource_name, None)
    usage_quota = usage.get(flavor, {}).get(resource_name, None)

    # Calculating available quota only supports numeric values right now.
    # Some resources need to be further processed by parsing unit like memory, e.g 10Gi
    if nominal_quota is not None and usage_quota is not None:
        return int(nominal_quota) - int(usage_quota)
    
    return "N/A"


def _get_hyperpod_clusters(sm_client: boto3.client) -> List[str]:
    cluster_names: List[str] = []
    response = sm_client.list_clusters()
    if "ClusterSummaries" in response:
        cluster_names = [
            cluster["ClusterName"] for cluster in response["ClusterSummaries"]
        ]

    return cluster_names


def _restructure_output(summary_list, namespaces):
    if not namespaces:
        return

    for node_summary in summary_list:
        node_summary["Namespaces"] = {}
        for ns in namespaces:
            available_accelerators = node_summary[ns + AVAILABLE_ACCELERATOR_DEVICES_KEY]
            total_accelerators = node_summary[ns + TOTAL_ACCELERATOR_DEVICES_KEY]
            quota_accelerator_info = {
                AVAILABLE_ACCELERATOR_DEVICES_KEY: available_accelerators,
                TOTAL_ACCELERATOR_DEVICES_KEY: total_accelerators,
            }
            node_summary["Namespaces"][ns] = quota_accelerator_info
            node_summary.pop(ns + AVAILABLE_ACCELERATOR_DEVICES_KEY, None)
            node_summary.pop(ns + TOTAL_ACCELERATOR_DEVICES_KEY, None)


def _aggregate_nodes_info(
    nodes: List[client.V1Node],
) -> Dict[str, Dict[str, Any]]:
    list_pods_service = ListPods()
    nodes_resource_allocated_dict = (
        list_pods_service.list_pods_and_get_requested_resources_group_by_node_name()
    )
    nodes_summary: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for node in nodes:
        labels = node.metadata.labels
        node_name = node.metadata.name
        logger.debug(f"node_name is {node_name} and labels are {labels}")
        instance_type = labels[INSTANCE_TYPE_LABEL]
        nodes_summary[instance_type]["total_nodes"] += 1
        if DEEP_HEALTH_CHECK_STATUS_LABEL in labels:
            if labels[DEEP_HEALTH_CHECK_STATUS_LABEL] == "Passed":
                nodes_summary[instance_type]["deep_health_check_passed"] += 1
        else:
            # Resilience feature can only be enabled at InstanceGroup level
            # So for the same instance type in one cluster, all nodes should
            # have deep_health_check_status or none of them have this label
            nodes_summary[instance_type]["deep_health_check_passed"] = "N/A"

        health_status = labels[HP_HEALTH_STATUS_LABEL]
        if health_status.startswith("Unschedulable"):
            nodes_summary[instance_type]["unschedulable"] += 1
            # Don't need to update accelerator devices information if
            # node is unscheduable
            continue
        elif health_status == "Schedulable":
            nodes_summary[instance_type]["schedulable"] += 1
        else:
            raise ValueError("Unexpected node health status")

        # Calculate accelerator devices available
        if (
            not instance_type.startswith("ml.g")
            and not instance_type.startswith("ml.p")
            and not instance_type.startswith("ml.trn")
        ):
            nodes_summary[instance_type]["accelerator_devices_available"] = "N/A"
            continue
        else:
            if not node.status:
                continue
            gpu_allocatable = node.status.allocatable.get(NVIDIA_GPU_RESOURCE_LIMIT_KEY)
            neuron_allocatable = node.status.allocatable.get(
                "aws.amazon.com/neurondevice"
            )
            nodes_summary[instance_type]["accelerator_devices_available"] += (
                int(gpu_allocatable) if gpu_allocatable else int(neuron_allocatable)
            )

        # Accelerator Devices available = Allocatable devices - Allocated devices
        if node_name in nodes_resource_allocated_dict:
            nodes_summary[instance_type]["accelerator_devices_available"] -= (
                nodes_resource_allocated_dict[node_name]
            )

    logger.debug(f"nodes_summary: {nodes_summary}")
    return nodes_summary


@click.command()
@click.option(
    "--cluster-name",
    type=click.STRING,
    required=True,
    help="Required. The HyperPod cluster name to configure with.",
)
@click.option(
    "--region",
    type=click.STRING,
    required=False,
    help="Optional. The region that the HyperPod and EKS clusters are located. If not specified, it will be set to the region from the current AWS account credentials.",
)
@click.option(
    "--namespace",
    "-n",
    type=click.STRING,
    required=False,
    help="Optional. The namespace that you want to connect to. If not specified, Hyperpod cli commands will auto discover the accessible namespace.",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode",
)
def set_cluster_context(
    cluster_name: str,
    region: Optional[str],
    debug: bool,
    namespace: str,
) -> None:
    """
    Connect to a HyperPod EKS cluster.

    Args:
        cluster_name (str): The name of the HyperPod EKS cluster to connect to.
        namespace (str): The namespace connect to. Default as 'default' namespace.
        debug (bool): Enable debug mode.
        region (Optional[str]): The AWS region where the HyperPod EKS cluster resides.
            If not provided, the default region from the AWS credentials will be used.

    Returns:
        None
    """
    if debug:
        set_logging_level(logger, logging.DEBUG)
    validator = ClusterValidator()
    botocore_config = botocore.config.Config(
        user_agent_extra=get_user_agent_extra_suffix()
    )
    session = boto3.Session(region_name=region) if region else boto3.Session()
    if not validator.validate_aws_credential(session):
        logger.error("Cannot connect to HyperPod cluster due to aws credentials error")
        sys.exit(1)

    try:
        sm_client = get_sagemaker_client(session, botocore_config)
        hp_cluster_details = sm_client.describe_cluster(ClusterName=cluster_name)
        logger.debug("Fetched hyperpod cluster details")
        store_current_hyperpod_context(hp_cluster_details)
        eks_cluster_arn = hp_cluster_details["Orchestrator"]["Eks"]["ClusterArn"]
        logger.debug(
            f"hyperpod cluster's EKS orchestrator cluster arn: {eks_cluster_arn}"
        )

        eks_name = get_name_from_arn(eks_cluster_arn)
        _update_kube_config(eks_name, region, None)
        k8s_client = KubernetesClient()
        k8s_client.set_context(eks_cluster_arn, namespace)
    except botocore.exceptions.NoRegionError:
        logger.error(
            f"Please ensure you configured AWS default region or use '--region' argument to specify the region"
        )
        sys.exit(1)
    except Exception as e:
        logger.error(
            f"Unexpected error happens when try to connect to cluster {cluster_name}. Error: {e}"
        )
        sys.exit(1)


@click.command()
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode",
)
def get_cluster_context(
    debug: bool,
) -> Tuple[Any, str]:
    """
    Get all the context related to the current set Cluster

    Args:
        debug (bool): Enable debug mode.

    Returns:
        None
    """
    if debug:
        set_logging_level(logger, logging.DEBUG)

    try:
        current_context = get_cluster_context_util()
        print(f"Cluster context:{current_context}")
    except botocore.exceptions.NoRegionError:
        logger.error(
            f"Please ensure you configured AWS default region or use '--region' argument to specify the region"
        )
        sys.exit(1)
    except Exception as e:
        logger.error(
            f"Unexpected error happens when try to fetch cluster context. Error: {e}"
        )
        sys.exit(1)



@click.command()
@click.option("--grafana", is_flag=True, help="Returns Grafana Dashboard URL")
@click.option("--prometheus", is_flag=True, help="Returns Prometheus Workspace URL")
@click.option("--list", is_flag=True, help="Returns list of available metrics")
def get_monitoring(grafana: bool, prometheus: bool, list: bool) -> None:
    """Get monitoring configurations for Hyperpod cluster"""
    try:
        if not any([grafana, prometheus, list]):
            print("Error: Please select at least one option")
            print("Usage : hyp get-monitoring --grafana/--prometheus/--list/--help")
            return
        if not is_observability_addon_enabled(get_eks_cluster_name()):
            print("Observability addon is not enabled for this cluster")
            sys.exit(1)
        monitor_config = get_monitoring_config()
        if prometheus:
            print(f"Prometheus workspace URL: {monitor_config.prometheusURL}")
        if grafana:
            print(f"Grafana dashboard URL: {monitor_config.grafanaURL}")
        if list:
            metrics_data = monitor_config.availableMetrics
            print(tabulate([[k, v.get('level', v.get('enabled'))] for k, v in metrics_data.items()],
                           headers=['Metric', 'Level/Enabled'], tablefmt='presto'))
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        sys.exit(1)



def _update_kube_config(
    eks_name: str,
    region: Optional[str],
    config_file: Optional[str],
) -> None:
    """
    Update the local kubeconfig with the specified EKS cluster details.

    Args:
        eks_name (str): The name of the EKS cluster to update in the kubeconfig.
        region (Optional[str]): The AWS region where the EKS cluster resides.
            If not provided, the default region from the AWS credentials will be used.
        config_file (Optional[str]): The path to the kubeconfig file.

    Raises:
        RuntimeError: If the `aws eks update-kubeconfig` command fails to execute.
    """

    # Construct the kubeconfig update command
    # EKS doesn't provide boto3 API for this command
    command = [
        "aws",
        "eks",
        "update-kubeconfig",
        "--name",
        eks_name,
    ]

    if region:
        command.extend(["--region", region])

    if config_file:
        command.extend(["--kubeconfig", config_file])

    # Validate command components
    if not all(isinstance(arg, str) and arg.strip() for arg in command):
        raise ValueError("Invalid command arguments")

    try:
        # Execute the command to update kubeconfig
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to update kubeconfig: {e}")
    except (OSError, ValueError) as e:
        raise RuntimeError(f"Invalid command execution: {e}")
