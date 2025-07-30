"""
Command module for HyperPod cluster stack operations.
"""

import logging
import click
import json
import os

from sagemaker.hyperpod.cluster_management.hp_cluster_stack import HpClusterStack
from sagemaker.hyperpod.common.utils import setup_logging

logger = logging.getLogger(__name__)


@click.command("hyp-cluster")
@click.argument("config-file", required=True)
@click.argument("stack-name", required=True)
@click.option("--region", help="AWS region")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def create_cluster_stack(config_file, region, debug):
    """Create a new HyperPod cluster stack using the provided configuration."""
    logger = setup_logging(logging.getLogger(__name__), debug)
    create_cluster_stack_helper(config_file, region, debug)

def create_cluster_stack_helper(config_file, region = None, debug = False):
    try:
        # Validate the config file path
        if not os.path.exists(config_file):
            logger.error(f"Config file not found: {config_file}")
            return

        # Load the configuration from the YAML file
        import yaml
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)

        # Filter out template and namespace fields and convert to strings
        filtered_config = {}
        for k, v in config_data.items():
            if k not in ('template', 'namespace') and v is not None:
                # Convert lists to JSON strings, everything else to string
                if isinstance(v, list):
                    filtered_config[k] = json.dumps(v)
                else:
                    filtered_config[k] = str(v)

        # Create the HpClusterStack object
        cluster_stack = HpClusterStack(**filtered_config)

        # Log the configuration
        logger.info("Creating HyperPod cluster stack with the following configuration:")
        for key, value in filtered_config.items():
            if value is not None:
                logger.info(f"  {key}: {value}")

        # Create the cluster stack
        stack_id = cluster_stack.create(region)

        logger.info(f"Stack creation initiated successfully with ID: {stack_id}")
        logger.info("You can monitor the stack creation in the AWS CloudFormation console.")

    except Exception as e:
        logger.error(f"Failed to create cluster stack: {e}")
        if debug:
            logger.exception("Detailed error information:")
        raise click.ClickException(str(e))

@click.command("hyp-cluster")
@click.argument("stack-name", required=True)
@click.option("--debug", is_flag=True, help="Enable debug logging")
def describe(stack_name, debug):
    """Describe the status of a HyperPod cluster stack."""
    logger = setup_logging(logging.getLogger(__name__), debug)
    
    logger.info(f"Describing stack: {stack_name}")
    logger.info("This feature is not yet implemented.")
    
@click.command("hyp-cluster")
@click.argument("stack-name", required=True)
@click.option("--debug", is_flag=True, help="Enable debug logging")
def delete(stack_name, debug):
    """Delete a HyperPod cluster stack."""
    logger = setup_logging(logging.getLogger(__name__), debug)
    
    logger.info(f"Deleting stack: {stack_name}")
    logger.info("This feature is not yet implemented.")