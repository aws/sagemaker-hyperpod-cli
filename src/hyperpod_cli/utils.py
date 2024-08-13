import logging
import re

import boto3
import botocore

log_level = logging.INFO


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


def setup_logger(name: str) -> logging.Logger:
    """
    Set up a logger with a console handler and a formatter.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The configured logger instance.
    """
    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)  # Set the log level to DEBUG

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)  # Set the log level for the handler

    # Create a formatter and set it for the handler
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(console_handler)

    return logger


def get_sagemaker_client(session: boto3.Session) -> botocore.client.BaseClient:
    # TODO: change to use public endpoint when release
    return session.client(
        service_name="sagemaker-dev",
        endpoint_url="https://api.sagemaker.alpha.us-west-2.ml-platform.aws.a2z.com",
    )
