"""
Command module for HyperPod cluster stack operations.
"""

import logging
import click
import json
import os

from sagemaker_core.main.resources import Cluster
from sagemaker_core.main.shapes import ClusterInstanceGroupSpecification
from tabulate import tabulate
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
def describe_cluster_stack(stack_name, debug):
    """Describe the status of a HyperPod cluster stack."""
    logger = setup_logging(logging.getLogger(__name__), debug)
    
    try:
        stack_info = HpClusterStack.describe(stack_name=stack_name)
        
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
    
@click.command("hyp-cluster")
@click.option("--region", help="AWS region")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def list_cluster_stacks(region, debug):
    """List all HyperPod cluster stacks."""
    logger = setup_logging(logging.getLogger(__name__), debug)
    
    try:
        stacks_info = HpClusterStack.list(region=region)
        
        if not stacks_info or 'StackSummaries' not in stacks_info:
            click.secho("No stacks found", fg='yellow')
            return
            
        stack_summaries = stacks_info['StackSummaries']
        
        logger.debug(f"Listing stacks in region: {region or 'default'}\ninfo: {json.dumps(stack_summaries, indent=2, default=str)}")
        
        click.echo(f"📋 HyperPod Cluster Stacks ({len(stack_summaries)} found)")
        
        if stack_summaries:
            for i, stack in enumerate(stack_summaries, 1):
                click.echo(f"\n[{i}] Stack Details:")
                
                table_data = []
                for key, value in stack.items():
                    value_str = str(value)
                    
                    if key in ['CreationTime', 'DeletionTime'] and value:
                        # Format timestamps
                        formatted_value = value_str.split('.')[0].replace('+00:00', '')
                    elif isinstance(value, dict):
                        # Format dict values compactly
                        formatted_value = json.dumps(value, separators=(',', ':'))
                    else:
                        formatted_value = value_str
                    
                    table_data.append([key, formatted_value])
                
                click.echo(tabulate(table_data, headers=["Field", "Value"], tablefmt="presto"))
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
    
@click.command("hyp-cluster")
@click.argument("stack-name", required=True)
@click.option("--debug", is_flag=True, help="Enable debug logging")
def delete(stack_name, debug):
    """Delete a HyperPod cluster stack."""
    logger = setup_logging(logging.getLogger(__name__), debug)
    
    logger.info(f"Deleting stack: {stack_name}")
    logger.info("This feature is not yet implemented.")


@click.command("hyp-cluster")
@click.option("--cluster-name", required=True, help="The name of the cluster to update")
@click.option("--instance-groups", help="Instance Groups")
@click.option("--node-recovery", help="Node Recovery")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def update_cluster(cluster_name,
                   instance_groups,
                   node_recovery,
                   debug):
    logger = setup_logging(logging.getLogger(__name__), debug)
    cluster = Cluster.get(cluster_name=cluster_name)
    
    # Convert instance_groups to list of ClusterInstanceGroupSpecification
    if instance_groups:
        if isinstance(instance_groups, str):
            instance_groups = json.loads(instance_groups)
        instance_groups = [ClusterInstanceGroupSpecification(**ig) for ig in instance_groups]
    
    cluster.update(instance_groups=instance_groups, node_recovery=node_recovery)
    logger.info("Cluster has been updated")
    click.secho(f"Cluster {cluster_name} has been updated")

