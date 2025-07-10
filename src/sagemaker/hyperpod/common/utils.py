from kubernetes import client
from pydantic import ValidationError
from kubernetes.client.exceptions import ApiException
from kubernetes import config
import re
import boto3
import json
from typing import List
import logging
import os
import subprocess
import yaml
from typing import Optional
from kubernetes.config import (
    KUBE_CONFIG_DEFAULT_LOCATION,
)

EKS_ARN_PATTERN = r"arn:aws:eks:([\w-]+):\d+:cluster/([\w-]+)"

KUBE_CONFIG_PATH = os.path.expanduser(KUBE_CONFIG_DEFAULT_LOCATION)


def get_default_namespace():
    _, active_context = config.list_kube_config_contexts()

    if active_context and "context" in active_context:
        if (
            "namespace" in active_context["context"]
            and active_context["context"]["namespace"]
        ):
            return active_context["context"]["namespace"]
        else:
            return "default"
    else:
        raise Exception(
            "No active context. Please use set_cluster_context() method to set current context."
        )

def handle_exception(e: Exception, name: str, namespace: str):
    if isinstance(e, ApiException):
        if e.status == 401:
            raise Exception(f"Credentials unauthorized.") from e
        elif e.status == 403:
            raise Exception(
                f"Access denied to resource '{name}' in namespace '{namespace}'."
            ) from e
        if e.status == 404:
            raise Exception(
                f"Resource '{name}' not found in namespace '{namespace}'."
            ) from e
        elif e.status == 409:
            raise Exception(
                f"Resource '{name}' already exists in namespace '{namespace}'."
            ) from e
        elif 500 <= e.status < 600:
            raise Exception("Kubernetes API internal server error.") from e
        else:
            raise Exception(f"Unhandled Kubernetes error: {e.status} {e.reason}") from e

    if isinstance(e, ValidationError):
        raise Exception("Response did not match expected schema.") from e

    raise e


def get_eks_name_from_arn(arn: str) -> str:
    match = re.match(EKS_ARN_PATTERN, arn)

    if match:
        return match.group(2)
    else:
        raise RuntimeError("cannot get EKS cluster name")


def get_region_from_eks_arn(arn: str) -> str:
    match = re.match(EKS_ARN_PATTERN, arn)

    if match:
        return match.group(1)
    else:
        raise RuntimeError("cannot get region from EKS ARN")


def get_jumpstart_model_instance_types(model_id, region) -> List[str]:
    client = boto3.client("sagemaker", region_name=region)

    response = client.describe_hub_content(
        HubName="SageMakerPublicHub", HubContentType="Model", HubContentName=model_id
    )

    content = json.loads(response["HubContentDocument"])
    instance_types = content["SupportedInferenceInstanceTypes"]

    return instance_types


def get_cluster_instance_types(cluster, region) -> set:
    instance_types = set({})

    sagemaker_client = boto3.client("sagemaker", region_name=region)
    response = sagemaker_client.describe_cluster(ClusterName=cluster)

    for instance_group in response["InstanceGroups"]:
        instance_types.add(instance_group["InstanceType"])

    return instance_types


def setup_logging(logger, debug=False):
    """
    Configure logging with specified format and level.

    Args:
        logger: Logger instance to configure
        debug (bool): If True, sets logging level to DEBUG, otherwise INFO
    """
    logging.basicConfig()

    # Remove any existing handlers to avoid duplicate logs
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create and configure stream handler
    handler = logging.StreamHandler()

    if debug:
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    else:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(message)s")

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger


def is_eks_orchestrator(sagemaker_client, cluster_name: str):
    response = sagemaker_client.describe_cluster(ClusterName=cluster_name)
    return "Eks" in response["Orchestrator"]


def update_kube_config(
    eks_name: str,
    region: Optional[str] = None,
    config_file: Optional[str] = None,
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

    # EKS doesn't provide boto3 API for this command
    command = ["aws", "eks", "update-kubeconfig", "--name", eks_name]

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


def set_eks_context(
    context_name: str,
    namespace: Optional[str] = None,
) -> None:
    """
    Set the current context in the kubeconfig file.

    Args:
        context_name (str): The name of the context to set as current.
        namespace (str): The name of the namespace to use.
    """
    with open(KUBE_CONFIG_PATH, "r") as file:
        kubeconfig = yaml.safe_load(file)

    # Check if the context exists in the kubeconfig and update the context namespace
    # when namespace is specified in command line
    exist = False
    for context in kubeconfig["contexts"]:
        if context["name"] == context_name:
            if namespace is not None:
                context["context"]["namespace"] = namespace
            else:
                context["context"]["namespace"] = "default"
            exist = True

    if not exist:
        raise ValueError(f"Context '{context_name}' not found in kubeconfig file")

    # Set the current context
    kubeconfig["current-context"] = context_name

    # Write the updated kubeconfig back to the file
    with open(KUBE_CONFIG_PATH, "w") as file:
        yaml.safe_dump(kubeconfig, file)

    # Load the updated kubeconfig
    config.load_kube_config(config_file=KUBE_CONFIG_PATH)

def set_cluster_context(
    cluster_name: str,
    region: Optional[str] = None,
    namespace: Optional[str] = None,
):
    logger = logging.getLogger(__name__)
    logger = setup_logging(logger)

    client = boto3.client("sagemaker", region_name=region)

    response = client.describe_cluster(ClusterName=cluster_name)
    eks_cluster_arn = response["Orchestrator"]["Eks"]["ClusterArn"]
    eks_name = get_eks_name_from_arn(eks_cluster_arn)

    update_kube_config(eks_name, region)
    set_eks_context(eks_cluster_arn, namespace)

    if namespace:
        logger.info(
            f"Successfully set current context as: {cluster_name}, namespace: {namespace}"
        )
    else:
        logger.info(f"Successfully set current context as: {cluster_name}")

def get_cluster_context():
    try:
        current_context = config.list_kube_config_contexts()[1]["context"]["cluster"]
        return current_context
    except Exception as e:
        raise Exception(
            f"Failed to get current context: {e}. Check your config file at {KUBE_CONFIG_DEFAULT_LOCATION}"
        )

def list_clusters(
    region: Optional[str] = None,
):
    client = boto3.client("sagemaker", region_name=region)
    clusters = client.list_clusters()

    eks_clusters = []
    slurm_clusters = []

    for cluster in clusters["ClusterSummaries"]:
        cluster_name = cluster["ClusterName"]

        if is_eks_orchestrator(client, cluster_name):
            eks_clusters.append(cluster_name)
        else:
            slurm_clusters.append(cluster_name)

    return {"Eks": eks_clusters, "Slurm": slurm_clusters}

def get_current_cluster():
    current_context = get_cluster_context()
    region = get_region_from_eks_arn(current_context)

    hyperpod_clusters = list_clusters(region)["Eks"]
    client = boto3.client("sagemaker", region_name=region)

    for cluster_name in hyperpod_clusters:
        response = client.describe_cluster(ClusterName=cluster_name)
        if response["Orchestrator"]["Eks"]["ClusterArn"] == current_context:
            return cluster_name

    raise Exception(
        f"Failed to get current Hyperpod cluster name. Check your config file at {KUBE_CONFIG_DEFAULT_LOCATION}"
    )


def get_current_region():
    eks_arn = get_cluster_context()
    try:
        return get_region_from_eks_arn(eks_arn)
    except:
        return boto3.session.Session().region_name
