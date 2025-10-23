import click
import json
from tabulate import tabulate
from sagemaker.hyperpod.cli.clients.kubernetes_client import KubernetesClient
from sagemaker.hyperpod.cli.dev_space_utils import generate_click_command
from hyperpod_dev_space_template.registry import SCHEMA_REGISTRY
from sagemaker.hyperpod.common.telemetry.telemetry_logging import (
    _hyperpod_telemetry_emitter,
)
from sagemaker.hyperpod.common.telemetry.constants import Feature


@click.command("hyp-dev-space")
@generate_click_command(
    schema_pkg="hyperpod_dev_space_template",
    registry=SCHEMA_REGISTRY,
)
def dev_space_create(version, config):
    """Create a dev-space resource."""

    try:
        name = config.get("name")
        namespace = config.get("namespace")
        dev_space_spec = config.get("dev_space_spec")

        k8s_client = KubernetesClient()
        k8s_client.create_dev_space(namespace, dev_space_spec)
        
        click.echo(f"Dev space '{name}' created successfully in namespace '{namespace}'")
    except Exception as e:
        click.echo(f"Error creating dev space: {e}", err=True)


@click.command("hyp-dev-space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
@click.option("--output", "-o", type=click.Choice(["table", "json"]), default="table")
def dev_space_list(namespace, output):
    """List dev-space resources."""
    k8s_client = KubernetesClient()
    
    try:
        resources = k8s_client.list_dev_spaces(namespace)
        
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
                click.echo("No dev spaces found")
    except Exception as e:
        click.echo(f"Error listing dev spaces: {e}", err=True)


@click.command("hyp-dev-space")
@click.option("--name", required=True, help="Name of the dev space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
@click.option("--output", "-o", type=click.Choice(["yaml", "json"]), default="yaml")
def dev_space_describe(name, namespace, output):
    """Describe a dev-space resource."""
    k8s_client = KubernetesClient()
    
    try:
        resource = k8s_client.get_dev_space(namespace, name)
        resource["metadata"].pop('managedFields', None)
        
        if output == "json":
            click.echo(json.dumps(resource, indent=2))
        else:
            import yaml
            click.echo(yaml.dump(resource, default_flow_style=False))
    except Exception as e:
        click.echo(f"Error describing dev space '{name}': {e}", err=True)


@click.command("hyp-dev-space")
@click.option("--name", required=True, help="Name of the dev space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
def dev_space_delete(name, namespace):
    """Delete a dev-space resource."""
    k8s_client = KubernetesClient()
    
    try:
        k8s_client.delete_dev_space(namespace, name)

        click.echo(f"Dev space '{name}' deleted successfully")
    except Exception as e:
        click.echo(f"Error deleting dev space '{name}': {e}", err=True)


@click.command("hyp-dev-space")
@generate_click_command(
    schema_pkg="hyperpod_dev_space_template",
    registry=SCHEMA_REGISTRY,
    is_update=True,
)
def dev_space_update(version, config):
    """Update a dev-space resource."""
    k8s_client = KubernetesClient()

    try:
        name = config["name"]
        namespace = config["namespace"]
        dev_space_spec = config.get("dev_space_spec", {})

        k8s_client.patch_dev_space(
            namespace=namespace,
            name=name,
            body=dev_space_spec
        )

        click.echo(f"Dev space '{name}' updated successfully")
    except Exception as e:
        click.echo(f"Error updating dev space '{name}': {e}", err=True)


@click.command("hyp-dev-space")
@click.option("--name", required=True, help="Name of the dev space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
def dev_space_start(name, namespace):
    """Start a dev-space resource."""
    k8s_client = KubernetesClient()
    
    try:
        # Patch the resource to set desired status to "Running"
        patch_body = {"spec": {"desiredStatus": "Running"}}
        k8s_client.patch_dev_space(
            namespace=namespace,
            name=name,
            body=patch_body
        )

        click.echo(f"Dev space '{name}' start requested")
    except Exception as e:
        click.echo(f"Error starting dev space '{name}': {e}", err=True)


@click.command("hyp-dev-space")
@click.option("--name", required=True, help="Name of the dev space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
def dev_space_stop(name, namespace):
    """Stop a dev-space resource."""
    k8s_client = KubernetesClient()
    
    try:
        # Patch the resource to set desired status to "Stopped"
        patch_body = {"spec": {"desiredStatus": "Stopped"}}
        k8s_client.patch_dev_space(
            namespace=namespace,
            name=name,
            body=patch_body
        )

        click.echo(f"Dev space '{name}' stop requested")
    except Exception as e:
        click.echo(f"Error stopping dev space '{name}': {e}", err=True)


@click.command("hyp-dev-space")
@click.option("--name", required=True, help="Name of the dev space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
def dev_space_get_logs(name, namespace):
    """Get logs for a dev-space resource."""
    k8s_client = KubernetesClient()
    
    try:
        # Get pods associated with the dev space
        pods = k8s_client.list_pods_with_labels(
            namespace=namespace,
            label_selector=f"sagemaker.aws.com/space-name={name}"
        )
        
        if not pods.items:
            click.echo(f"No pods found for dev space '{name}'")
            return
        
        # Get logs from the first pod
        pod_name = pods.items[0].metadata.name
        logs = k8s_client.get_logs_for_pod(
            pod_name=pod_name,
            namespace=namespace,
        )

        click.echo(logs)
    except Exception as e:
        click.echo(f"Error getting logs for dev space '{name}': {e}", err=True)


@click.command("hyp-dev-space")
@click.option("--name", required=True, help="Name of the dev space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
@click.option("--port", required=True, help="Mapping localhost port to pod")
def dev_space_port_forward(name, namespace, port):
    """Forward a local port to a dev-space pod."""
    k8s_client = KubernetesClient()
    
    try:
        # Get pods associated with the dev space
        pods = k8s_client.list_pods_with_labels(
            namespace=namespace,
            label_selector=f"sagemaker.aws.com/space-name={name}"
        )
        
        if not pods.items:
            click.echo(f"No pods found for dev space '{name}'")
            return
        
        # Get the first running pod
        pod_name = pods.items[0].metadata.name

        k8s_client.port_forward_dev_space(
            namespace=namespace,
            pod_name=pod_name,
            local_port=port,
        )

    except Exception as e:
        click.echo(f"Error forwarding port for dev space '{name}': {e}", err=True)
