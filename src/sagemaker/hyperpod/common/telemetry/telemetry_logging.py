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
from sagemaker.telemetry.constants import Feature, Status, Region
from sagemaker.telemetry.telemetry_logging import (
    FEATURE_TO_CODE,
    STATUS_TO_CODE,
    _requests_helper,
    _construct_url,
)
import importlib.metadata

SDK_VERSION = importlib.metadata.version("sagemaker-hyperpod")
DEFAULT_AWS_REGION = "us-east-2"
OS_NAME = platform.system() or "UnresolvedOS"
OS_VERSION = platform.release() or "UnresolvedOSVersion"
OS_NAME_VERSION = "{}/{}".format(OS_NAME, OS_VERSION)
PYTHON_VERSION = "{}.{}.{}".format(
    sys.version_info.major, sys.version_info.minor, sys.version_info.micro
)

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
        logger.debug("SageMaker Python SDK telemetry not emitted!")


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
            start = perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = round(perf_counter() - start, 2)
                extra += f"&x-latency={duration}"
                _send_telemetry_request(
                    Status.SUCCESS,
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
                    Status.FAILURE,
                    [FEATURE_TO_CODE[str(feature)]],
                    None,
                    str(e),
                    type(e).__name__,
                    extra,
                )
                raise

        return wrapper

    return decorator
