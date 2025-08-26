"""
Command module for HyperPod cluster stack operations.
"""

import ast
import logging
import click
import json
import os
from typing import Optional

from sagemaker_core.main.resources import Cluster
from sagemaker_core.main.shapes import ClusterInstanceGroupSpecification

from tabulate import tabulate
from sagemaker.hyperpod.cluster_management.hp_cluster_stack import HpClusterStack
from sagemaker.hyperpod.common.telemetry import _hyperpod_telemetry_emitter
from sagemaker.hyperpod.common.telemetry.constants import Feature
from sagemaker.hyperpod.common.utils import setup_logging
from sagemaker.hyperpod.cli.utils import convert_datetimes

logger = logging.getLogger(__name__)


def parse_status_list(ctx, param, value):
    """Parse status list from string format like "['CREATE_COMPLETE', 'UPDATE_COMPLETE']" """
    if not value:
        return None
    
    try:
        # Handle both string representation and direct list
        if isinstance(value, str):
            # Parse string like "['item1', 'item2']" 
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return parsed
            else:
                raise click.BadParameter(f"Expected list format, got: {type(parsed).__name__}")
        return value
    except (ValueError, SyntaxError) as e:
        raise click.BadParameter(f"Invalid list format. Use: \"['STATUS1', 'STATUS2']\". Error: {e}")


@click.command("cluster-stack")
@click.argument("config-file", required=True)
@click.argument("stack-name", required=True)
@click.option("--region", help="AWS region")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def create_cluster_stack(config_file, region, debug):
    """Create a new HyperPod cluster stack using the provided configuration.

    Creates a CloudFormation stack for a HyperPod cluster using settings from a YAML configuration file.
    The stack will provision all necessary AWS resources for the cluster.

    .. dropdown:: Usage Examples
       :open:

       .. code-block:: bash

          # Create cluster stack with config file
          hyp create hyp-cluster cluster-config.yaml my-stack-name --region us-west-2

          # Create with debug logging
          hyp create hyp-cluster cluster-config.yaml my-stack-name --debug
    """
    create_cluster_stack_helper(config_file, region, debug)

def create_cluster_stack_helper(config_file: str, region: Optional[str] = None, debug: bool = False) -> None:
    """Helper function to create a HyperPod cluster stack.

    **Parameters:**

    .. list-table::
       :header-rows: 1
       :widths: 20 20 60

       * - Parameter
         - Type
         - Description
       * - config_file
         - str
         - Path to the YAML configuration file containing cluster stack settings
       * - region
         - str, optional
         - AWS region where the cluster stack will be created
       * - debug
         - bool
         - Enable debug logging for detailed error information

    **Raises:**

    ClickException: When cluster stack creation fails or configuration is invalid
    """
    try:
        # Validate the config file path
        if not os.path.exists(config_file):
            logger.error(f"Config file not found: {config_file}")
            return

        # Load the configuration from the YAML file
        import yaml
        import uuid
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)

        # Filter out template and namespace fields
        filtered_config = {}
        for k, v in config_data.items():
            if k not in ('template', 'namespace') and v is not None:
                # Append 4-digit UUID to resource_name_prefix
                if k == 'resource_name_prefix' and v:
                    v = f"{v}-{str(uuid.uuid4())[:4]}"
                filtered_config[k] = v

        # Create the HpClusterStack object
        # Ensure fixed defaults are always set
        if 'custom_bucket_name' not in filtered_config:
            filtered_config['custom_bucket_name'] = 'sagemaker-hyperpod-cluster-stack-bucket'
        if 'github_raw_url' not in filtered_config:
            filtered_config['github_raw_url'] = 'https://raw.githubusercontent.com/aws-samples/awsome-distributed-training/refs/heads/main/1.architectures/7.sagemaker-hyperpod-eks/LifecycleScripts/base-config/on_create.sh'
        if 'helm_repo_url' not in filtered_config:
            filtered_config['helm_repo_url'] = 'https://github.com/aws/sagemaker-hyperpod-cli.git'
        if 'helm_repo_path' not in filtered_config:
            filtered_config['helm_repo_path'] = 'helm_chart/HyperPodHelmChart'
        
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

@click.command("cluster-stack")
@click.argument("stack-name", required=True)
@click.option("--region", help="AWS region")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "describe_cluster_stack_cli")
def describe_cluster_stack(stack_name: str, debug: bool, region: str) -> None:
    """Describe the status of a HyperPod cluster stack.

    Shows detailed information about a CloudFormation stack including its current status,
    resources, and configuration parameters.

    .. dropdown:: Usage Examples
       :open:

       .. code-block:: bash

          # Describe a cluster stack
          hyp describe hyp-cluster my-stack-name

          # Describe with specific region
          hyp describe hyp-cluster my-stack-name --region us-west-2
    """
    logger = setup_logging(logging.getLogger(__name__), debug)
    
    try:
        stack_info = HpClusterStack.describe(stack_name=stack_name, region=region)
        
        if not stack_info or 'Stacks' not in stack_info or not stack_info['Stacks']:
            click.secho(f"❌ Stack '{stack_name}' not found", fg='red')
            return

        stack = stack_info['Stacks'][0]

        logger.debug(f"Describing stack name: {stack_name}\ninfo: {json.dumps(stack_info, indent=2, default=str)}")

        click.echo(f"📋 Stack Details for: {stack_name}")

        # Highlight stack status
        stack_status = stack.get('StackStatus', 'UNKNOWN')
        click.echo(f"Status: ", nl=False)
        click.secho(stack_status)

        table_data = []
        for key, value in stack.items():
            if isinstance(value, (dict, list)):
                formatted_value = json.dumps(value, indent=2, default=str)
            else:
                formatted_value = str(value)
            table_data.append([key, formatted_value])

        # Calculate column widths
        max_field_width = max(len(str(row[0])) for row in table_data)
        max_value_width = max(len(str(row[1]).split('\n')[0]) for row in table_data)  # First line only for width calc

        # Add headers with matching separators (presto format adds spaces around |)
        field_header = "Field".ljust(max_field_width)
        value_header = "Value".ljust(max_value_width)
        click.echo(f" {field_header} | {value_header} ")
        click.echo(f"-{'-' * max_field_width}-+-{'-' * max_value_width}-")

        click.echo(tabulate(table_data, tablefmt="presto"))

    except Exception as e:
        logger.error(f"Failed to describe stack: {e}")
        if debug:
            logger.exception("Detailed error information:")

        if "does not exist" in str(e):
            click.echo(f"❌ Stack '{stack_name}' not found")
        elif "AccessDenied" in str(e):
            click.echo("❌ Access denied. Check AWS permissions")
        else:
            click.echo(f"❌ Error describing stack: {e}")

        raise click.ClickException(str(e))

@click.command("cluster-stack")
@click.option("--region", help="AWS region")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.option("--status", 
              callback=parse_status_list,
              help="Filter by stack status. Format: \"['CREATE_COMPLETE', 'UPDATE_COMPLETE']\"")
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "list_cluster_stack_cli")
def list_cluster_stacks(region, debug, status):
    """List all HyperPod cluster stacks.

    Displays a summary of all CloudFormation stacks related to HyperPod clusters
    in the specified region or default region.

    .. dropdown:: Usage Examples
       :open:

       .. code-block:: bash

          # List all cluster stacks
          hyp list hyp-cluster

          # List stacks in specific region
          hyp list hyp-cluster --region us-east-1
    """
    logger = setup_logging(logging.getLogger(__name__), debug)

    try:
        stacks_info = HpClusterStack.list(region=region, stack_status_filter=status)

        if not stacks_info or 'StackSummaries' not in stacks_info:
            click.secho("No stacks found", fg='yellow')
            return

        stack_summaries = stacks_info['StackSummaries']

        # Convert datetimes for display
        stack_summaries = [convert_datetimes(stack) for stack in stack_summaries]

        logger.debug(f"Listing stacks in region: {region or 'default'}")

        click.echo(f"📋 HyperPod Cluster Stacks ({len(stack_summaries)} found)")

        if stack_summaries:
            for i, stack in enumerate(stack_summaries, 1):
                try:
                    click.echo(f"\n[{i}] Stack Details:")

                    table_data = []
                    for key, value in stack.items():
                        table_data.append([key, str(value)])

                    click.echo(tabulate(table_data, headers=["Field", "Value"], tablefmt="presto"))
                except Exception as e:
                    logger.error(f"Error processing stack {i}: {e}")
                    click.echo(f"❌ Error processing stack {i}: {stack.get('StackName', 'Unknown')}")
                    continue
        else:
            click.echo("No stacks found")

    except Exception as e:
        logger.error(f"Failed to list stacks: {e}")
        if debug:
            logger.exception("Detailed error information:")

        if "AccessDenied" in str(e) or "Insufficient permissions" in str(e):
            click.secho("❌ Access denied. Check AWS permissions", fg='red')
        else:
            click.secho(f"❌ Error listing stacks: {e}", fg='red')

        raise click.ClickException(str(e))
    
@click.command("cluster-stack")
@click.argument("stack-name", required=True)
@click.option("--debug", is_flag=True, help="Enable debug logging")
def delete(stack_name: str, debug: bool) -> None:
    """Delete a HyperPod cluster stack.

    Removes the specified CloudFormation stack and all associated AWS resources.
    This operation cannot be undone.

    .. dropdown:: Usage Examples
       :open:

       .. code-block:: bash

          # Delete a cluster stack
          hyp delete hyp-cluster my-stack-name
    """
    logger = setup_logging(logging.getLogger(__name__), debug)
    
    logger.info(f"Deleting stack: {stack_name}")
    logger.info("This feature is not yet implemented.")

@click.command("cluster")
@click.option("--cluster-name", required=True, help="The name of the cluster to update")
@click.option("--instance-groups", help="Instance Groups JSON string")
@click.option("--instance-groups-to-delete", help="Instance Groups to delete JSON string")
@click.option("--region", help="Region")
@click.option("--node-recovery", help="Node Recovery (Automatic or None)")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "update_cluster_cli")
def update_cluster(
            cluster_name: str,
            instance_groups: Optional[str],
            instance_groups_to_delete: Optional[str],
            region: Optional[str],
            node_recovery: Optional[str],
            debug: bool) -> None:
    """Update an existing HyperPod cluster configuration.

    Modifies cluster settings such as instance groups and node recovery policies.
    At least one update parameter must be provided.

    .. dropdown:: Usage Examples
       :open:

       .. code-block:: bash

          # Update cluster with new instance groups
          hyp update hyp-cluster --cluster-name my-cluster --instance-groups '{"group1": {...}}'

          # Update node recovery setting
          hyp update hyp-cluster --cluster-name my-cluster --node-recovery Automatic
    """
    """Update an existing HyperPod cluster configuration."""
    logger = setup_logging(logging.getLogger(__name__), debug)
    
    # Validate that at least one parameter is provided
    if not any([instance_groups, instance_groups_to_delete, node_recovery]):
        raise click.ClickException("At least one of --instance-groups, --instance-groups-to-delete, or --node-recovery must be provided")
    
    cluster = Cluster.get(cluster_name=cluster_name, region=region)
    
    # Prepare update parameters
    update_params = {}
    
    # Convert instance_groups to list of ClusterInstanceGroupSpecification
    if instance_groups:
        if isinstance(instance_groups, str):
            instance_groups = json.loads(instance_groups)
        update_params['instance_groups'] = [ClusterInstanceGroupSpecification(**ig) for ig in instance_groups]
    
    # Convert instance_groups_to_delete to list of strings
    if instance_groups_to_delete:
        if isinstance(instance_groups_to_delete, str):
            instance_groups_to_delete = json.loads(instance_groups_to_delete)
        update_params['instance_groups_to_delete'] = instance_groups_to_delete
    
    # Add node_recovery if provided
    if node_recovery:
        update_params['node_recovery'] = node_recovery

    click.secho(f"Update Params: {update_params}")
    cluster.update(**update_params)

    logger.info("Cluster has been updated")
    click.secho(f"Cluster {cluster_name} has been updated")

