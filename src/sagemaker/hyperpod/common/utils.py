from kubernetes import client, __version__ as kubernetes_client_version
from pydantic import ValidationError
from kubernetes.client.exceptions import ApiException
from kubernetes import config
import re
import boto3
import json
from typing import List, Tuple, Optional
import logging
import os
import subprocess
import yaml
import click
from kubernetes.config import (
    KUBE_CONFIG_DEFAULT_LOCATION,
)
# Remove enum-based imports - now using template-agnostic approach

EKS_ARN_PATTERN = r"arn:aws:eks:([\w-]+):\d+:cluster/([\w-]+)"
CLIENT_VERSION_PATTERN = r'^\d+\.\d+\.\d+$'

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

def handle_exception(e: Exception, name: str, namespace: Optional[str],
                    operation_type: str = 'unknown', resource_type: str = 'unknown', debug: bool = False):
    """
    Handle various Kubernetes API exceptions for SDK usage (non-CLI).

    Note: CLI commands should use the @handle_cli_exceptions() decorator instead.
    This function is for SDK classes and provides basic exception handling.

    Args:
        e: The exception to handle
        name: Resource name
        namespace: Kubernetes namespace
        operation_type: Operation type (legacy parameter, kept for backward compatibility)
        resource_type: Resource type (legacy parameter, kept for backward compatibility)
        debug: If True, show full Kubernetes exception details
    """

    if isinstance(e, ApiException):
        if e.status == 401:
            raise Exception(f"Credentials unauthorized.") from e
        elif e.status == 403:
            if debug and e.body:
                # Show full Kubernetes error details in debug mode
                raise Exception(f"Kubernetes API error: {e.body}") from e
            elif namespace:
                raise Exception(
                    f"Access denied to resource '{name}' in namespace '{namespace}'."
                ) from e
            else:
                raise Exception(
                    f"Access denied to resource '{name}'."
                ) from e
        elif e.status == 404:
            if debug and e.body:
                raise Exception(f"Kubernetes API error: {e.body}") from e
            elif namespace:
                # Basic 404 for SDK usage - CLI commands get enhanced 404 via decorator
                raise Exception(
                    f"Resource '{name}' not found in namespace '{namespace}'. "
                    f"Please check the resource name and namespace."
                ) from e
            else:
                raise Exception(
                    f"Resource '{name}' not found. Please check the resource name."
                ) from e
        elif e.status == 409:
            if debug and e.body:
                raise Exception(f"Kubernetes API error: {e.body}") from e
            elif namespace:
                raise Exception(
                    f"Resource '{name}' already exists in namespace '{namespace}'."
                ) from e
            else:
                raise Exception(
                    f"Resource '{name}' already exists."
                ) from e
        elif 500 <= e.status < 600:
            if debug and e.body:
                raise Exception(f"Kubernetes API error: {e.body}") from e
            else:
                raise Exception("Kubernetes API internal server error.") from e
        else:
            if debug and e.body:
                raise Exception(f"Kubernetes API error: {e.body}") from e
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
    return response.get("Orchestrator", {}).get("Eks") is not None


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

    if not is_eks_orchestrator(client, cluster_name):
        raise ValueError(f"Cluster '{cluster_name}' is not EKS-orchestrated. HyperPod CLI only supports EKS-orchestrated clusters.")
    
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
        if not is_eks_orchestrator(client, cluster_name):
            continue
        response = client.describe_cluster(ClusterName=cluster_name)
        if response["Orchestrator"]["Eks"]["ClusterArn"] == current_context:
            return cluster_name

    raise Exception(
        f"Failed to get current Hyperpod cluster name. Check your config file at {KUBE_CONFIG_DEFAULT_LOCATION}"
    )

def get_aws_default_region():
    try:
        return boto3.Session().region_name
    except:
        raise Exception(f"Failed to get AWS region. Check your config file at ~/.aws/config")

def get_current_region():
    eks_arn = get_cluster_context()
    try:
        return get_region_from_eks_arn(eks_arn)
    except:
        return get_aws_default_region()
      
def create_boto3_client(service_name: str, region_name: Optional[str] = None, **kwargs):
    """Create a boto3 client with smart region handling.

    Args:
        service_name (str): AWS service name (e.g., 'sagemaker', 'eks')
        region_name (Optional[str]): AWS region. If None, uses AWS default
        **kwargs: Additional boto3 client parameters

    Returns:
        boto3 client instance
    """
    return boto3.client(service_name, region_name=region_name or boto3.session.Session().region_name, **kwargs)

def region_to_az_ids(region_code: str):
    """
    Map AWS region code to all availability zone IDs.
    Reference: https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-availability-zones.html
    """
    ec2_client = create_boto3_client('ec2', region_name=region_code)
    try:
        response = ec2_client.describe_availability_zones(
            Filters=[
                {'Name': 'region-name', 'Values': [region_code]},
                {'Name': 'zone-type', 'Values': ['availability-zone']}
            ]
        )
    except Exception as e:
        raise Exception(f"Failed to call describe_availability_zones for region: {region_code}", e)

    if (not response) or ('AvailabilityZones' not in response):
        raise Exception(f"Failed to get Availability Zones for region: {region_code}")

    if len(response['AvailabilityZones']) == 0:
        raise Exception(f"No Availability Zones found for region: {region_code}")

    zone_ids = []
    for az in response['AvailabilityZones']:
        if 'ZoneId' in az:
            zone_ids.append(az['ZoneId'])

    if not zone_ids:
        raise Exception(f"No Zone IDs found for region: {region_code}")

    return zone_ids
    
  
def parse_client_kubernetes_version(version_str: str) -> Tuple[int, int]:
    """Parse major and minor version from client library version string.

    Handles both old versioning scheme (v12 and before) and new homogenized scheme.
    Old scheme: v12.0.0 corresponds to Kubernetes v1.16
    New scheme: v17.0.0 corresponds to Kubernetes v1.17

    Args:
        version_str (str): Client library version string (e.g., '12.0.0', '17.0.0', 'v12.0.0')

    Returns:
        Tuple[int, int]: Major and minor version numbers as (1, minor)
    """
    if not version_str:
        logger = logging.getLogger(__name__)
        logger.debug(f"Empty version string provided, Using default version 0.0")
        return 0, 0

    # Remove suffix (like '+snapshot') if present
    version_str = version_str.split('+')[0]

    # Remove 'v' prefix if present
    if version_str.startswith('v'):
        version_str = version_str[1:]

    # Client library version format (x.y.z)
    if re.match(CLIENT_VERSION_PATTERN, version_str):
        major = int(version_str.split('.')[0])

        # Old client versioning scheme (v12 and before)
        if major <= 12:
            # Currently maps to Kubernetes v1.x
            # This mapping assumes Kubernetes major version is 1
            # If Kubernetes moves to v2.x in the future, this mapping would need to be updated
            return 1, major + 4

        # New homogenized scheme (v17 and above)
        # Currently maps to Kubernetes v1.x
        # This mapping assumes Kubernetes major version is 1
        # If Kubernetes moves to v2.x in the future, this mapping would need to be updated
        return 1, major

    # If we get here, parsing failed
    logger = logging.getLogger(__name__)
    logger.warning(f"Failed to parse client version from string: '{version_str}'. Using default version 0.0.")
    return 0, 0



def is_kubernetes_version_compatible(client_version: Tuple[int, int], server_version: Tuple[int, int]) -> bool:
    """
    Check if Kubernetes client and server versions are compatible.

    Args:
        client_version (Tuple[int, int]): Client major and minor version
        server_version (Tuple[int, int]): Server major and minor version

    Returns:
        bool: True if versions are compatible, False otherwise
    """
    # Check for default versions (0.0) which indicate parsing failures
    if client_version == (0, 0) or server_version == (0, 0):
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Version compatibility check using default version(s): client={client_version}, server={server_version}. "
            f"\nThis may indicate a version parsing issue. Please check your Kubernetes configuration."
        )
        return True

    if client_version[0] != server_version[0]:
        return False

    """
        Client version should not be more than 3 minor versions behind the server and not more than 
        1 minor version ahead of the server
    """
    client_minor = client_version[1]
    server_minor = server_version[1]

    if server_minor - client_minor > 3:
        return False

    if client_minor - server_minor > 1:
        return False

    return True


def display_formatted_logs(logs: str, title: str = "Logs") -> None:
    """
    Display logs with consistent formatting and color coding across all job types.

    Args:
        logs: Raw log content as string
        title: Title to display before logs (default: "Logs")
    """
    if not logs:
        click.echo("No logs available.")
        return

    click.echo(f"\n{title}:")
    click.echo("=" * 80)

    # Split logs into lines and display them with color coding
    log_lines = logs.split("\n")
    for line in log_lines:
        if line.strip():  # Skip empty lines
            # Color coding based on log level keywords
            line_upper = line.upper()
            if any(keyword in line_upper for keyword in ["ERROR", "FATAL", "EXCEPTION"]):
                click.secho(line, fg="red")
            elif any(keyword in line_upper for keyword in ["WARNING", "WARN"]):
                click.secho(line, fg="yellow")
            elif any(keyword in line_upper for keyword in ["INFO", "SUCCESS"]):
                click.secho(line, fg="green")
            elif any(keyword in line_upper for keyword in ["DEBUG", "TRACE"]):
                click.secho(line, fg="blue")
            else:
                click.echo(line)

    click.echo("\nEnd of logs")
    click.echo("=" * 80)


def verify_kubernetes_version_compatibility(logger) -> bool:
    """
    Verify compatibility between Kubernetes client and server versions.

    This function checks if the current Kubernetes client version is compatible with
    the server version. It handles both minimum compatibility versions specified by
    the server and the standard Kubernetes support policy (within 3 minor versions behind
    and not more than 1 minor version ahead).

    Ref link: https://github.com/kubernetes-client/python#compatibility

    Args:
        logger: Logger instance for outputting messages.

    Returns:
        bool: True if versions are compatible, False otherwise
    """

    try:
        version_api = client.VersionApi()
        server_version_info = version_api.get_code()

        server_version_str = f"{server_version_info.major}.{server_version_info.minor}"
        client_version = parse_client_kubernetes_version(kubernetes_client_version)
        client_version_str = f"{client_version[0]}.{client_version[1]}"

        # Debug output of server version info
        logger.debug(f"Server version info: {server_version_info}")
        logger.debug(f"Client version: {kubernetes_client_version}, parsed as {client_version_str}")

        # Check if server provides minimum compatibility versions (these are optional strings)
        has_min_compatibility = False
        is_compatible = True

        try:
            if hasattr(server_version_info, 'min_compatibility_major') and server_version_info.min_compatibility_major is not None and \
               hasattr(server_version_info, 'min_compatibility_minor') and server_version_info.min_compatibility_minor is not None:
                min_major = int(server_version_info.min_compatibility_major)
                min_minor = int(server_version_info.min_compatibility_minor)
                has_min_compatibility = True

                # Check if client version is below minimum compatibility
                if client_version[0] < min_major or (client_version[0] == min_major and client_version[1] < min_minor):
                    click.secho(
                        f"\nWARNING: Kubernetes client version {client_version_str} is incompatible with server {server_version_str}. "
                        f"Server requires minimum client version {min_major}.{min_minor}. "
                        f"\nPlease update Kubernetes Python Client: pip install --upgrade kubernetes>={min_major}.{min_minor}.0",
                        fg="yellow"
                    )
                    is_compatible = False
        except (ValueError, TypeError, AttributeError) as e:
            logger.debug(f"Could not parse minimum compatibility version: {e}")
            has_min_compatibility = False

        if not has_min_compatibility:
            # Fall back to standard compatibility check if min versions not provided
            server_version_parsed = (int(server_version_info.major), int(server_version_info.minor))
            if not is_kubernetes_version_compatible(client_version, server_version_parsed):
                click.secho(
                    f"\nWARNING: Kubernetes client version {client_version_str} is incompatible with server {server_version_str}. "
                    f"Client must be within 3 minor versions behind and not more than 1 ahead of server. "
                    f"\nPlease update Kubernetes Python Client: pip install --upgrade kubernetes",
                    fg="yellow"
                )
                is_compatible = False

        return is_compatible
    except Exception as e:
        logger.warning(f"Failed to verify Kubernetes version compatibility: {e}")
        return True  # Be lenient if we can't check compatibility
