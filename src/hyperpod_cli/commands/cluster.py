import subprocess
import json
from collections import defaultdict
from typing import Any, Dict, List, Optional

import boto3
import click
from botocore.client import BaseClient
from kubernetes import client
from ratelimit import limits, sleep_and_retry
from tabulate import tabulate

from hyperpod_cli.clients.kubernetes_client import KubernetesClient
from hyperpod_cli.constants.command_constants import (
    DEEP_HEALTH_CHECK_STATUS_LABEL,
    HP_HEALTH_STATUS_LABEL,
    INSTANCE_TYPE_LABEL,
    SAGEMAKER_HYPERPOD_NAME_LABEL,
    TEMP_KUBE_CONFIG_FILE,
    Orchestrator,
    OutputFormat,
)
from hyperpod_cli.service.list_pods import ListPods
from hyperpod_cli.utils import get_name_from_arn, get_sagemaker_client, setup_logger
from hyperpod_cli.validators.cluster_validator import ClusterValidator
from hyperpod_cli.validators.validator import Validator

# Best guess of EKS describeCluster and SageMaker listCluster
# rate limit as 5tps. So Ratelimit to 4 to avoid throttling
# TODO: Need to test out the rate limit
RATE_LIMIT = 4
RATE_LIMIT_PERIOD = 1  # 1 second

logger = setup_logger(__name__)


@click.command()
@click.option(
    "--region", type=click.STRING, required=False, help="The region HyperPod EKS cluster resides"
)
@click.option(
    "--orchestrator",
    type=click.Choice([c.value for c in Orchestrator]),
    required=False,
    default=Orchestrator.EKS.value,
    help="The orchestrator for the cluster, currently only support 'eks'",
)
@click.option(
    "--output",
    type=click.Choice([c.value for c in OutputFormat]),
    required=False,
    default=OutputFormat.JSON.value,
    help="Config the output format, default is JSON. Table output format is also supported",
)
@click.option("--clusters", type=click.STRING, required=False, help="The list of clusters to show")
def list_clusters(
    region: Optional[str],
    orchestrator: Optional[str],
    output: Optional[str],
    clusters: Optional[str],
):
    """Get clusters capacity."""
    validator = ClusterValidator()
    session = boto3.Session(region_name=region) if region else boto3.Session()
    if not validator.validate_aws_credential(session):
        logger.error("Cannot list clusters capacity due to AWS credentials issue")
        return

    sm_client = get_sagemaker_client(session)

    if clusters:
        cluster_names = clusters.split(",")
    else:
        cluster_names = _get_hyperpod_clusters(sm_client)

    cluster_capacities: List[List[str]] = []

    k8s_client = KubernetesClient()
    for cluster_name in cluster_names:
        rate_limited_operation(
            cluster_name=cluster_name,
            validator=validator,
            sm_client=sm_client,
            k8s_client=k8s_client,
            region=region,
            temp_config_file=TEMP_KUBE_CONFIG_FILE,
            cluster_capacities=cluster_capacities,
        )
    headers = [
        "Cluster",
        "InstanceType",
        "TotalNodes",
        "AcceleratorDevicesAvailable",
        "NodeHealthStatus=Schedulable",
        "DeepHealthCheckStatus=Passed",
    ]
    if output == OutputFormat.TABLE.value:
        print(tabulate(cluster_capacities, headers=headers, tablefmt="presto"))
    elif output == OutputFormat.JSON.value:
        json_list = [dict(zip(headers, value)) for value in cluster_capacities]
        print(json.dumps(json_list, indent=4))


@sleep_and_retry
@limits(calls=RATE_LIMIT, period=RATE_LIMIT_PERIOD)
def rate_limited_operation(
    cluster_name: str,
    validator: ClusterValidator,
    sm_client: BaseClient,
    k8s_client: KubernetesClient,
    region: Optional[str],
    temp_config_file: str,
    cluster_capacities: List[List[str]],
) -> None:
    try:
        eks_cluster_arn = validator.validate_cluster_and_get_eks_arn(cluster_name, sm_client)
        if eks_cluster_arn is None:
            logger.warning(f"Cannot find EKS cluster behind {cluster_name}, continue...")
            return
        eks_cluster_name = get_name_from_arn(eks_cluster_arn)
        _update_kube_config(eks_cluster_name, region, temp_config_file)
        nodes = k8s_client.list_node_with_temp_config(
            temp_config_file, SAGEMAKER_HYPERPOD_NAME_LABEL
        )
        nodes_info = _aggregate_nodes_info(nodes)

        for instance_type, nodes_summary in nodes_info.items():
            cluster_capacities.append(
                [
                    cluster_name,
                    instance_type,
                    nodes_summary["total_nodes"],
                    nodes_summary["accelerator_devices_available"],
                    nodes_summary["schedulable"],
                    nodes_summary["deep_health_check_passed"],
                ]
            )
    except Exception as e:
        logger.error(f"Error processing cluster {cluster_name}: {e}, continue...")


def _get_hyperpod_clusters(sm_client: boto3.client) -> List[str]:
    cluster_names: List[str] = []
    try:
        response = sm_client.list_clusters()
        if 'ClusterSummaries' in response:
            cluster_names = [cluster["ClusterName"] for cluster in response["ClusterSummaries"]]
    except Exception as e:
        logger.error(f"Failed to list HyperPod clusters with error: {e}")

    return cluster_names


def _aggregate_nodes_info(nodes: List[client.V1Node]) -> Dict[str, Dict[str, Any]]:
    list_pods_service = ListPods()
    nodes_resource_allocated_dict = (
        list_pods_service.list_pods_and_get_requested_resources_group_by_node_name()
    )
    nodes_summary: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for node in nodes:
        labels = node.metadata.labels
        node_name = node.metadata.name
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
            gpu_allocatable = node.status.allocatable.get("nvidia.com/gpu")
            neuron_allocatable = node.status.allocatable.get("aws.amazon.com/neurondevice")
            nodes_summary[instance_type]["accelerator_devices_available"] += int(gpu_allocatable) if gpu_allocatable else int(neuron_allocatable)

        # Accelerator Devices available = Allocatable devices - Allocated devices
        if node_name in nodes_resource_allocated_dict:
            nodes_summary[instance_type][
                "accelerator_devices_available"
            ] -= nodes_resource_allocated_dict[node_name]

    logger.debug(f"nodes_summary: {nodes_summary}")
    return nodes_summary


@click.command()
@click.option(
    "--name",
    type=click.STRING,
    required=True,
    help="The name of the HyperPod EKS cluster you want to connect " "to.",
)
@click.option(
    "--region", type=click.STRING, required=False, help="The region HyperPod EKS cluster resides"
)
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    help="The namespace connect to",
    default="default",
)
def connect_cluster(
    name: str,
    region: Optional[str],
    namespace: str = "default",
) -> None:
    """
    Connect to a HyperPod EKS cluster.

    Args:
        name (str): The name of the HyperPod EKS cluster to connect to.
        namespace (str): The namespace connect to. Default as 'default' namespace.
        region (Optional[str]): The AWS region where the HyperPod EKS cluster resides.
            If not provided, the default region from the AWS credentials will be used.

    Returns:
        None
    """
    validator = Validator()
    session = boto3.Session(region_name=region) if region else boto3.Session()
    if not validator.validate_aws_credential(session):
        logger.error("Cannot connect to HyperPod cluster due to aws credentials error")
        return

    try:
        sm_client = get_sagemaker_client(session)
        hp_cluster_details = sm_client.describe_cluster(ClusterName=name)
        logger.debug("Fetched hyperpod cluster details")
        eks_cluster_arn = hp_cluster_details["Orchestrator"]["Eks"]["ClusterArn"]
        logger.debug(f"hyperpod cluster's EKS orchestrator cluster arn: {eks_cluster_arn}")

        k8s_client = KubernetesClient()
        if not k8s_client.context_exists(eks_cluster_arn):
            logger.debug("Context not exists, updating kubeconfig")
            eks_name = get_name_from_arn(eks_cluster_arn)
            _update_kube_config(eks_name, region, None)

        k8s_client.set_context(eks_cluster_arn, namespace)
        click.echo(f"Connect to HyperPod Cluster {name} in {namespace} namespace succeeded")
    except Exception as e:
        click.echo(f"Unexpected error happens when try to connect to cluster {name}. Error: {e}")


def _update_kube_config(eks_name: str, region: Optional[str], config_file: Optional[str]) -> None:
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

    try:
        # Execute the command to update kubeconfig
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to update kubeconfig: {e}")
