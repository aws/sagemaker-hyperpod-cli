from __future__ import absolute_import
import logging
import platform
import sys
from time import perf_counter
from typing import List, Tuple
import functools
import requests
import subprocess
import re

import boto3
from hyperpod_cli.telemetry.constants import Feature, Status, Region
import importlib.metadata

SDK_VERSION = importlib.metadata.version("hyperpod")
DEFAULT_AWS_REGION = "us-west-2"
OS_NAME = platform.system() or "UnresolvedOS"
OS_VERSION = platform.release() or "UnresolvedOSVersion"
OS_NAME_VERSION = "{}/{}".format(OS_NAME, OS_VERSION)
PYTHON_VERSION = "{}.{}.{}".format(
    sys.version_info.major, sys.version_info.minor, sys.version_info.micro
)

FEATURE_TO_CODE = {
    # str(Feature.HYPERPOD): 6,  # Added to support telemetry in sagemaker-hyperpod-cli
    # str(Feature.HYPERPOD_CLI): 7,
    str(Feature.HYPERPOD_V2): 10
}

STATUS_TO_CODE = {
    str(Status.SUCCESS): 1,
    str(Status.FAILURE): 0,
}

logger = logging.getLogger(__name__)


def get_region_and_account_from_current_context() -> Tuple[str, str]:
    """
    Get region and account ID from current kubernetes context
    Returns: (region, account_id)
    """
    try:
        # Get current context
        result = subprocess.run(
            ["kubectl", "config", "current-context"], capture_output=True, text=True
        )

        if result.returncode == 0:
            context = result.stdout.strip()

            # Extract region
            region_pattern = r"([a-z]{2}-[a-z]+-\d{1})"
            region = DEFAULT_AWS_REGION
            if match := re.search(region_pattern, context):
                region = match.group(1)

            # Extract account ID (12 digits)
            account_pattern = r"(\d{12})"
            account = "unknown"
            if match := re.search(account_pattern, context):
                account = match.group(1)

            return region, account

    except Exception as e:
        logger.debug(f"Failed to get context info from kubectl: {e}")

    return DEFAULT_AWS_REGION, "unknown"


def _requests_helper(url, timeout):
    """Make a GET request to the given URL"""

    response = None
    try:
        response = requests.get(url, timeout)
    except requests.exceptions.RequestException as e:
        logger.exception("Request exception: %s", str(e))
    return response


def _construct_url(
    accountId: str,
    region: str,
    status: str,
    feature: str,
    failure_reason: str,
    failure_type: str,
    extra_info: str,
) -> str:
    """Construct the URL for the telemetry request"""

    base_url = (
        f"https://sm-pysdk-t-{region}.s3.{region}.amazonaws.com/telemetry?"
        f"x-accountId={accountId}"
        f"&x-status={status}"
        f"&x-feature={feature}"
    )
    logger.debug("Failure reason: %s", failure_reason)
    if failure_reason:
        base_url += f"&x-failureReason={failure_reason}"
        base_url += f"&x-failureType={failure_type}"
    if extra_info:
        base_url += f"&x-extra={extra_info}"
    return base_url


def _extract_telemetry_data(func_name: str, *args, **kwargs) -> str:
    """Extract comprehensive telemetry data for all CLI functions"""
    telemetry_data = []
    
    # Recipe metrics for start_job_cli
    if func_name == "start_job_cli":
        # Existing high-value parameters
        recipe = kwargs.get('recipe')
        override_parameters = kwargs.get('override_parameters')
        instance_type = kwargs.get('instance_type')
        node_count = kwargs.get('node_count')
        scheduler_type = kwargs.get('scheduler_type')
        auto_resume = kwargs.get('auto_resume')
        
        # New high-value parameters
        config_file = kwargs.get('config_file')
        job_kind = kwargs.get('job_kind')
        pull_policy = kwargs.get('pull_policy')
        restart_policy = kwargs.get('restart_policy')
        queue_name = kwargs.get('queue_name')
        priority = kwargs.get('priority')
        max_retry = kwargs.get('max_retry')
        deep_health_check_passed_nodes_only = kwargs.get('deep_health_check_passed_nodes_only')
        tasks_per_node = kwargs.get('tasks_per_node')
        persistent_volume_claims = kwargs.get('persistent_volume_claims')
        volumes = kwargs.get('volumes')
        pre_script = kwargs.get('pre_script')
        post_script = kwargs.get('post_script')
        
        # Recipe analysis
        if recipe:
            parts = recipe.split('/')
            if len(parts) >= 2:
                telemetry_data.append(f"recipe_type={parts[0]}")
                telemetry_data.append(f"model_family={parts[1]}")
            telemetry_data.append(f"recipe_name={recipe}")
            
            # Extract sequence length, GPU type, model size from recipe
            if seq_match := re.search(r'seq(\d+)k?', recipe):
                telemetry_data.append(f"sequence_length={seq_match.group(1)}k")
            if gpu_match := re.search(r'(p5x\d+|trn1x?\d*|p4)', recipe):
                telemetry_data.append(f"gpu_type={gpu_match.group(1)}")
            if model_match := re.search(r'(\d+)b', recipe):
                telemetry_data.append(f"model_size={model_match.group(1)}b")
        
        # Configuration approach
        if config_file:
            telemetry_data.append("config_approach=yaml")
        else:
            telemetry_data.append("config_approach=cli")
        
        # Job configuration
        if job_kind:
            telemetry_data.append(f"job_kind={job_kind}")
        if pull_policy:
            telemetry_data.append(f"pull_policy={pull_policy}")
        if restart_policy:
            telemetry_data.append(f"restart_policy={restart_policy}")
        if queue_name:
            telemetry_data.append(f"queue_name_provided=true")
        if priority:
            telemetry_data.append(f"priority_provided=true")
        if max_retry:
            telemetry_data.append(f"max_retry={max_retry}")
        if deep_health_check_passed_nodes_only:
            telemetry_data.append("deep_health_check=true")
        
        # Resource configuration
        if tasks_per_node:
            telemetry_data.append(f"tasks_per_node={tasks_per_node}")
        if persistent_volume_claims:
            telemetry_data.append("pvc_used=true")
        if volumes:
            telemetry_data.append("volumes_used=true")
        if pre_script:
            telemetry_data.append("pre_script_used=true")
        if post_script:
            telemetry_data.append("post_script_used=true")
        
        # Existing parameters
        if override_parameters:
            telemetry_data.append("override_used=true")
        if instance_type:
            telemetry_data.append(f"instance_type={instance_type}")
        if node_count:
            telemetry_data.append(f"node_count={node_count}")
        if scheduler_type:
            telemetry_data.append(f"scheduler_type={scheduler_type}")
        if auto_resume:
            telemetry_data.append(f"auto_resume={auto_resume}")
    
    # Cluster metrics (get_clusters_cli only - no create/delete found)
    elif func_name == "get_clusters_cli":
        clusters = kwargs.get('clusters')  # Comma-separated cluster names filter
        namespace = kwargs.get('namespace')  # List of namespaces
        
        if clusters:
            telemetry_data.append(f"clusters_filter_provided=true")
            cluster_count = len(clusters.split(',')) if isinstance(clusters, str) else len(clusters)
            telemetry_data.append(f"clusters_count={cluster_count}")
        if namespace:
            telemetry_data.append(f"namespace_provided=true")
            ns_count = len(namespace) if isinstance(namespace, (list, tuple)) else 1
            telemetry_data.append(f"namespace_count={ns_count}")
    
    # Job metrics
    elif func_name in ["list_jobs_cli", "get_job_cli", "cancel_job_cli"]:
        job_name = kwargs.get('job_name')
        namespace = kwargs.get('namespace')
        all_namespaces = kwargs.get('all_namespaces')  # list_jobs specific
        selector = kwargs.get('selector')  # list_jobs specific
        
        if job_name:
            telemetry_data.append(f"job_name_provided=true")
        if namespace:
            telemetry_data.append(f"namespace_provided=true")
        if all_namespaces:
            telemetry_data.append(f"all_namespaces=true")
        if selector:
            telemetry_data.append(f"label_selector_provided=true")
    
    # Pod metrics (list_pods_cli from job.py, get_log_cli and exec_cli from pod.py)
    elif func_name in ["list_pods_cli", "get_log_cli", "exec_cli"]:
        job_name = kwargs.get('job_name')
        namespace = kwargs.get('namespace')
        pod = kwargs.get('pod')  # get_log_cli and exec_cli specific
        all_pods = kwargs.get('all_pods')  # exec_cli specific
        
        if job_name:
            telemetry_data.append(f"job_name_provided=true")
        if namespace:
            telemetry_data.append(f"namespace_provided=true")
        if pod:
            telemetry_data.append(f"pod_name_provided=true")
        if all_pods:
            telemetry_data.append(f"all_pods_mode=true")
    
    # Job patch metrics
    elif func_name == "patch_job_cli":
        patch_type = kwargs.get('patch_type')  # First positional arg
        job_name = kwargs.get('job_name')
        namespace = kwargs.get('namespace')
        
        if patch_type:
            telemetry_data.append(f"patch_type={patch_type}")
        if job_name:
            telemetry_data.append(f"job_name_provided=true")
        if namespace:
            telemetry_data.append(f"namespace_provided=true")
    
    # Cluster connection metrics
    elif func_name == "connect_cluster_cli":
        cluster_name = kwargs.get('cluster_name')
        namespace = kwargs.get('namespace')
        
        if cluster_name:
            telemetry_data.append(f"cluster_name_provided=true")
        if namespace:
            telemetry_data.append(f"namespace_provided=true")
    
    return "&" + "&".join(telemetry_data) if telemetry_data else ""



def _send_telemetry_request(
    status: int,
    feature_list: List[int],
    session,
    failure_reason: str = None,
    failure_type: str = None,
    extra_info: str = None,
) -> None:
    """Make GET request to an empty object in S3 bucket"""
    try:
        region, accountId = get_region_and_account_from_current_context()

        try:
            Region(region)  # Validate the region
        except ValueError:
            logger.warning(
                "Region not found in supported regions. Telemetry request will not be emitted."
            )
            return

        url = _construct_url(
            accountId,
            region,
            str(status),
            str(
                ",".join(map(str, feature_list))
            ),  # Remove brackets and quotes to cut down on length
            failure_reason,
            failure_type,
            extra_info,
        )
        # Send the telemetry request
        logger.info("Sending telemetry request to [%s]", url)
        _requests_helper(url, 2)
        logger.info("SageMaker Python SDK telemetry successfully emitted.")
    except Exception:  # pylint: disable=W0703
        logger.warning("SageMaker Python SDK telemetry not emitted!")


def _hyperpod_telemetry_emitter(feature: str, func_name: str):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            extra = (
                f"{func_name}"
                f"&x-sdkVersion={SDK_VERSION}"
                f"&x-env={PYTHON_VERSION}"
                f"&x-sys={OS_NAME_VERSION}"
            )
            
            # Add comprehensive telemetry data for all functions
            telemetry_data = _extract_telemetry_data(func_name, *args, **kwargs)
            extra += telemetry_data
            
            start = perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = round(perf_counter() - start, 2)
                extra += f"&x-latency={duration}"
                _send_telemetry_request(
                    STATUS_TO_CODE[str(Status.SUCCESS)],
                    [FEATURE_TO_CODE[str(feature)]],
                    None,
                    None,
                    None,
                    extra,
                )
                return result
            except Exception as e:
                duration = round(perf_counter() - start, 2)
                extra += f"&x-latency={duration}"
                _send_telemetry_request(
                    STATUS_TO_CODE[str(Status.FAILURE)],
                    [FEATURE_TO_CODE[str(feature)]],
                    None,
                    str(e),
                    type(e).__name__,
                    extra,
                )
                raise

        return wrapper
    return decorator
