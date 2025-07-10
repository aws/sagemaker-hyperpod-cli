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
import re
import json

import boto3
import botocore
from botocore.config import Config

from sagemaker.hyperpod.cli.constants.command_constants import (
    GENERATED_LAUNCHER_CONFIG_FILE_PATH,
    HYPERPOD_CLUSTER_CONTEXT_FILE_NAME,
)


def get_name_from_arn(arn: str) -> str:
    """
    Parse the EKS cluster name from an EKS ARN.

    Args:
        arn (str): The ARN of the EKS cluster.

    Returns: str: The name of the EKS cluster if parsing is
    successful, otherwise raise RuntimeError.
    """
    # Define the regex pattern to match the EKS ARN and capture the cluster name
    pattern = r"arn:aws:eks:[\w-]+:\d+:cluster/([\w-]+)"
    match = re.match(pattern, arn)

    if match:
        return match.group(1)
    else:
        raise RuntimeError("cannot get EKS cluster name")


def setup_logger(
    name: str,
    logging_level: int = logging.ERROR,
) -> logging.Logger:
    """
    Set up a logger with a console handler and a formatter.

    Args:
        name (str): The name of the logger.
        logging_level (int): The logging level.

    Returns:
        logging.Logger: The configured logger instance.
    """
    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(logging_level)  # Set the log level to ERROR

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging_level)  # Set the log level for the handler

    # Create a formatter and set it for the handler
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(console_handler)

    return logger


def set_logging_level(
    logger: logging.Logger,
    logging_level: int,
):
    logger.setLevel(logging_level)
    logger.handlers[0].setLevel(logging_level)


def get_sagemaker_client(
    session: boto3.Session, config: Config = None
) -> botocore.client.BaseClient:
    return session.client(
        service_name="sagemaker",
        config=config,
    )


def store_current_hyperpod_context(data):
    with open(
        GENERATED_LAUNCHER_CONFIG_FILE_PATH + HYPERPOD_CLUSTER_CONTEXT_FILE_NAME,
        "w",
    ) as hyperpod_current_context:
        hyperpod_current_context.write(json.dumps(data, indent=4, default=str))


def _retrieve_current_hyperpod_context():
    with open(
        GENERATED_LAUNCHER_CONFIG_FILE_PATH + HYPERPOD_CLUSTER_CONTEXT_FILE_NAME,
        "r",
    ) as file:
        return json.load(file)


def _validate_link(console_url):
    pattern = "https:\/\/([a-z0-9-]+).console.aws.amazon.com\/sagemaker\/home\?region=([a-z0-9-]+)#\/cluster-management\/([a-zA-Z0-9-]+)"
    match = re.match(pattern, console_url)
    if match:
        return True
    else:
        return False


def validate_region_and_cluster_name(region, cluster_name):
    output = False
    region_char_list = region.split("-")

    if len(region_char_list) != 3:
        return False

    region_prefix_match = re.match("[a-z]+", region_char_list[0])
    region_match = re.match("[a-z]+", region_char_list[1])
    region_suffix_match = re.match("[0-9]+", region_char_list[2])

    region_prefix_length = len(region_char_list[0])
    region_length = len(region_char_list[1])
    region_suffix_length = len(region_char_list[2])

    cluster_name_match = re.match("[a-zA-Z0-9-]+", cluster_name)

    if (
        region_prefix_match
        and region_match
        and region_suffix_match
        and region_prefix_length == 2
        and region_suffix_length == 1
        and region_length >= 4
        and region_length < 10
        and cluster_name_match
        and len(cluster_name) >= 1
        and len(cluster_name) <= 63
    ):
        output = True
    return output


def get_cluster_console_url():
    hyperpod_context_cluster = _retrieve_current_hyperpod_context()
    console_url = None
    if (
        hyperpod_context_cluster
        and hyperpod_context_cluster.get("ClusterArn")
        and hyperpod_context_cluster.get("ClusterName")
    ):
        region = hyperpod_context_cluster.get("ClusterArn").split(":")[3]
        cluster_name = hyperpod_context_cluster.get("ClusterName")

        console_url = (
            f"https://{region}.console.aws.amazon.com/sagemaker/"
            f"home?region={region}#/cluster-management/{cluster_name}"
        )
        if _validate_link(console_url) and validate_region_and_cluster_name(region, cluster_name):
            return console_url
    return None

def get_eks_cluster_name():
    hyperpod_context_cluster = _retrieve_current_hyperpod_context()
    eks_cluster_arn = hyperpod_context_cluster.get("Orchestrator", {}).get("Eks", {}).get("ClusterArn", '')
    return eks_cluster_arn.split('cluster/')[-1]

def get_hyperpod_cluster_region():
    hyperpod_context_cluster = _retrieve_current_hyperpod_context()
    return hyperpod_context_cluster.get("ClusterArn").split(":")[3]