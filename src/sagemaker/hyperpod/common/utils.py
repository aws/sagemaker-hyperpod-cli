from kubernetes import client
from kubernetes import config as k8s_config
from pydantic import ValidationError
from kubernetes.client.exceptions import ApiException
from kubernetes import config
import uuid
import re
import boto3
import json
from typing import List
import logging

EKS_ARN_PATTERN = r"arn:aws:eks:([\w-]+):\d+:cluster/([\w-]+)"


def validate_cluster_connection():
    try:
        k8s_config.load_kube_config()
        v1 = client.CoreV1Api()
        return True
    except Exception as e:
        return False


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
            "No active context. Please use set_context() method to set current context."
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


def append_uuid(name: str) -> str:
    return f"{name}-{str(uuid.uuid4())[:4]}"


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
