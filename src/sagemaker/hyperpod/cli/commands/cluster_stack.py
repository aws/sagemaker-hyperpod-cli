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
from sagemaker.hyperpod.cli.init_utils import _filter_cli_metadata_fields
from sagemaker.hyperpod.cli.init_utils import load_config
from sagemaker.hyperpod.cli.constants.init_constants import TEMPLATES
from pathlib import Path
from sagemaker.hyperpod.cli.cluster_stack_utils import (
    StackNotFoundError,
    delete_stack_with_confirmation
)

logger = logging.getLogger(__name__)


def get_newest_template_version() -> int:
    """Get the newest available template version.
    
    Returns:
        int: The newest template version number
        
    TODO: Implement logic to fetch the actual newest template version
    from the template registry or remote source.
    """
    # Placeholder implementation - currently returns 1 as the latest version
    return 1


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
@click.option("--template-version", type=click.INT, help="Version number of cluster creation template")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def create_cluster_stack(config_file, region, template_version, debug):
    """Create a new HyperPod cluster stack using the provided configuration.

    Creates a CloudFormation stack for a HyperPod cluster using settings from a YAML configuration file.
    The stack will provision all necessary AWS resources for the cluster.

    .. dropdown:: Usage Examples
       :open:

       .. code-block:: bash

          # Create cluster stack with config file
          hyp create hyp-cluster cluster-config.yaml my-stack-name --region us-west-2 --template-version 1

          # Create with debug logging
          hyp create hyp-cluster cluster-config.yaml my-stack-name --debug
    """
    try:
        # Validate the config file path
        if not os.path.exists(config_file):
            logger.error(f"Config file not found: {config_file}")
            return

        # Load config to get template and version
        config_dir = Path(config_file).parent
        data, template, version = load_config(config_dir)

        # Get model from registry
        registry = TEMPLATES[template]["registry"]
        model_class = registry.get(str(version))

        if model_class:
            # Filter out CLI metadata fields
            filtered_config = _filter_cli_metadata_fields(data)

            # Create model instance and domain
            model_instance = model_class(**filtered_config)
            config = model_instance.to_config(region=region)

            # Use newest template version if not provided
            if template_version is None:
                template_version = get_newest_template_version()
                logger.info(f"No template version specified, using newest version: {template_version}")

            # Create the cluster stack
            stack_id = HpClusterStack(**config).create(region, template_version)

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
@click.option("--retain-resources", help="Comma-separated list of logical resource IDs to retain during deletion (only works on DELETE_FAILED stacks). Resource names are shown in failed deletion output, or use AWS CLI: 'aws cloudformation list-stack-resources --stack-name STACK_NAME --region REGION'")
@click.option("--region", required=True, help="AWS region")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "delete_cluster_stack_cli")
def delete_cluster_stack(stack_name: str, retain_resources: str, region: str, debug: bool) -> None:
    """Delete a HyperPod cluster stack.

    Removes the specified CloudFormation stack and all associated AWS resources.
    This operation cannot be undone.

    .. dropdown:: Usage Examples
       :open:

       .. code-block:: bash

          # Delete a cluster stack
          hyp delete cluster-stack my-stack-name --region us-west-2

          # Delete with retained resources (only works on DELETE_FAILED stacks)
          hyp delete cluster-stack my-stack-name --retain-resources S3Bucket-TrainingData,EFSFileSystem-Models --region us-west-2
          hyp delete cluster-stack my-stack-name --region us-west-2

          # Delete with retained resources (only works on DELETE_FAILED stacks)
          hyp delete cluster-stack my-stack-name --retain-resources S3Bucket-TrainingData,EFSFileSystem-Models --region us-west-2
    """
    logger = setup_logging(logging.getLogger(__name__), debug)
    
    try:
        # Use the high-level orchestration function with CLI-specific callbacks
        delete_stack_with_confirmation(
            stack_name=stack_name,
            region=region,
            retain_resources_str=retain_resources or "",
            message_callback=click.echo,
            confirm_callback=lambda msg: click.confirm("Continue?", default=False),
            success_callback=lambda msg: click.echo(f"✓ {msg}")
        )

    except StackNotFoundError:
        click.secho(f"❌ Stack '{stack_name}' not found", fg='red')
    except click.ClickException:
        # Re-raise ClickException for proper CLI error handling
        raise
    except Exception as e:
        logger.error(f"Failed to delete stack: {e}")
        if debug:
            logger.exception("Detailed error information:")
        raise click.ClickException(str(e))


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
