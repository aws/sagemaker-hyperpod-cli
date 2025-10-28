import click
import json
from tabulate import tabulate
from sagemaker.hyperpod.cli.clients.kubernetes_client import KubernetesClient
from sagemaker.hyperpod.cli.space_utils import generate_click_command
from hyperpod_space_template.registry import SCHEMA_REGISTRY
from sagemaker.hyperpod.common.telemetry.telemetry_logging import (
    _hyperpod_telemetry_emitter,
)
from sagemaker.hyperpod.common.telemetry.constants import Feature


@click.command("hyp-space")
@generate_click_command(
    schema_pkg="hyperpod_space_template",
    registry=SCHEMA_REGISTRY,
)
def space_create(version, config):
    """Create a space resource."""

    try:
        name = config.get("name")
        namespace = config.get("namespace")
        space_spec = config.get("space_spec")

        k8s_client = KubernetesClient()
        k8s_client.create_space(namespace, space_spec)
        
        click.echo(f"Dev space '{name}' created successfully in namespace '{namespace}'")
    except Exception as e:
        click.echo(f"Error creating space: {e}", err=True)


@click.command("hyp-space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
@click.option("--output", "-o", type=click.Choice(["table", "json"]), default="table")
def space_list(namespace, output):
    """List space resources."""
    k8s_client = KubernetesClient()
    
    try:
        resources = k8s_client.list_spaces(namespace)
        
        if output == "json":
            click.echo(json.dumps(resources, indent=2))
        else:
            items = resources.get("items", [])
            if items:
                table_data = []
                for item in items:
                    table_data.append([
                        item["metadata"]["name"],
                        item["metadata"]["namespace"],
                        item.get("status", {}).get("phase", "Unknown")
                    ])
                click.echo(tabulate(table_data, headers=["NAME", "NAMESPACE", "STATUS"]))
            else:
                click.echo("No spaces found")
    except Exception as e:
        click.echo(f"Error listing spaces: {e}", err=True)


@click.command("hyp-space")
@click.option("--name", required=True, help="Name of the space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
@click.option("--output", "-o", type=click.Choice(["yaml", "json"]), default="yaml")
def space_describe(name, namespace, output):
    """Describe a space resource."""
    k8s_client = KubernetesClient()
    
    try:
        resource = k8s_client.get_space(namespace, name)
        resource["metadata"].pop('managedFields', None)
        
        if output == "json":
            click.echo(json.dumps(resource, indent=2))
        else:
            import yaml
            click.echo(yaml.dump(resource, default_flow_style=False))
    except Exception as e:
        click.echo(f"Error describing space '{name}': {e}", err=True)


@click.command("hyp-space")
@click.option("--name", required=True, help="Name of the space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
def space_delete(name, namespace):
    """Delete a space resource."""
    k8s_client = KubernetesClient()
    
    try:
        k8s_client.delete_space(namespace, name)

        click.echo(f"Dev space '{name}' deleted successfully")
    except Exception as e:
        click.echo(f"Error deleting space '{name}': {e}", err=True)


@click.command("hyp-space")
@generate_click_command(
    schema_pkg="hyperpod_space_template",
    registry=SCHEMA_REGISTRY,
    is_update=True,
)
def space_update(version, config):
    """Update a space resource."""
    k8s_client = KubernetesClient()

    try:
        name = config["name"]
        namespace = config["namespace"]
        space_spec = config.get("space_spec", {})

        k8s_client.patch_space(
            namespace=namespace,
            name=name,
            body=space_spec
        )

        click.echo(f"Dev space '{name}' updated successfully")
    except Exception as e:
        click.echo(f"Error updating space '{name}': {e}", err=True)


@click.command("hyp-space")
@click.option("--name", required=True, help="Name of the space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
def space_start(name, namespace):
    """Start a space resource."""
    k8s_client = KubernetesClient()
    
    try:
        # Patch the resource to set desired status to "Running"
        patch_body = {"spec": {"desiredStatus": "Running"}}
        k8s_client.patch_space(
            namespace=namespace,
            name=name,
            body=patch_body
        )

        click.echo(f"Dev space '{name}' start requested")
    except Exception as e:
        click.echo(f"Error starting space '{name}': {e}", err=True)


@click.command("hyp-space")
@click.option("--name", required=True, help="Name of the space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
def space_stop(name, namespace):
    """Stop a space resource."""
    k8s_client = KubernetesClient()
    
    try:
        # Patch the resource to set desired status to "Stopped"
        patch_body = {"spec": {"desiredStatus": "Stopped"}}
        k8s_client.patch_space(
            namespace=namespace,
            name=name,
            body=patch_body
        )

        click.echo(f"Dev space '{name}' stop requested")
    except Exception as e:
        click.echo(f"Error stopping space '{name}': {e}", err=True)


@click.command("hyp-space")
@click.option("--name", required=True, help="Name of the space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
def space_get_logs(name, namespace):
    """Get logs for a space resource."""
    k8s_client = KubernetesClient()
    
    try:
        # Get pods associated with the space
        pods = k8s_client.list_pods_with_labels(
            namespace=namespace,
            label_selector=f"sagemaker.aws.com/space-name={name}"
        )
        
        if not pods.items:
            click.echo(f"No pods found for space '{name}'")
            return
        
        # Get logs from the first pod
        pod_name = pods.items[0].metadata.name
        logs = k8s_client.get_logs_for_pod(
            pod_name=pod_name,
            namespace=namespace,
        )

        click.echo(logs)
    except Exception as e:
        click.echo(f"Error getting logs for space '{name}': {e}", err=True)



