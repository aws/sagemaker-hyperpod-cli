import click
import json
import yaml
from tabulate import tabulate
from sagemaker.hyperpod.space.hyperpod_space import HPSpace
from sagemaker.hyperpod.cli.space_utils import generate_click_command
from hyperpod_space_template.registry import SCHEMA_REGISTRY
from hyperpod_space_template.v1_0.model import SpaceConfig
from sagemaker.hyperpod.common.telemetry.telemetry_logging import (
    _hyperpod_telemetry_emitter,
)
from sagemaker.hyperpod.common.telemetry.constants import Feature
from sagemaker.hyperpod.cli.constants.space_constants import DEFAULT_SPACE_PORT
from sagemaker.hyperpod.common.cli_decorators import handle_cli_exceptions


@click.command("hyp-space")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@generate_click_command(
    schema_pkg="hyperpod_space_template",
    registry=SCHEMA_REGISTRY,
)
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "create_space")
@handle_cli_exceptions()
def space_create(version, debug, config):
    """Create a space resource."""
    space_config = SpaceConfig(**config)
    space = HPSpace(config=space_config)
    space.create(debug=debug)
    click.echo(f"Space '{space_config.name}' created successfully in namespace '{space_config.namespace}'")


@click.command("hyp-space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
@click.option("--output", "-o", type=click.Choice(["table", "json"]), default="table")
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "list_spaces")
@handle_cli_exceptions()
def space_list(namespace, output):
    """List space resources."""
    spaces = HPSpace.list(namespace=namespace)
    
    if output == "json":
        spaces_data = []
        for space in spaces:
            space_dict = space.config.model_dump()
            spaces_data.append(space_dict)
        click.echo(json.dumps(spaces_data, indent=2))
    else:
        if spaces:
            table_data = []
            for space in spaces:
                # Extract status conditions from raw resource
                available = ""
                progressing = ""
                degraded = ""
                
                if space.status and 'conditions' in space.status:
                    conditions = {c['type']: c['status'] for c in space.status['conditions']}
                    available = conditions.get('Available', '')
                    progressing = conditions.get('Progressing', '')
                    degraded = conditions.get('Degraded', '')
                
                table_data.append([
                    space.config.name,
                    namespace,
                    available,
                    progressing,
                    degraded
                ])
            click.echo(tabulate(table_data, headers=["NAME", "NAMESPACE", "AVAILABLE", "PROGRESSING", "DEGRADED"]))
        else:
            click.echo("No spaces found")


@click.command("hyp-space")
@click.option("--name", required=True, help="Name of the space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
@click.option("--output", "-o", type=click.Choice(["yaml", "json"]), default="yaml")
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "describe_space")
@handle_cli_exceptions()
def space_describe(name, namespace, output):
    """Describe a space resource."""
    current_space = HPSpace.get(name=name, namespace=namespace)
    
    # Combine config and raw resource data
    current_space.raw_resource.get('metadata', {}).pop('managedFields', None)
    
    if output == "json":
        click.echo(json.dumps(current_space.raw_resource, indent=2))
    else:
        click.echo(yaml.dump(current_space.raw_resource, default_flow_style=False))


@click.command("hyp-space")
@click.option("--name", required=True, help="Name of the space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "delete_space")
@handle_cli_exceptions()
def space_delete(name, namespace):
    """Delete a space resource."""
    current_space = HPSpace.get(name=name, namespace=namespace)
    current_space.delete()
    click.echo(f"Requested deletion for Space '{name}' in namespace '{namespace}'")


@click.command("hyp-space")
@generate_click_command(
    schema_pkg="hyperpod_space_template",
    registry=SCHEMA_REGISTRY,
    is_update=True,
)
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "update_space")
@handle_cli_exceptions()
def space_update(version, config):
    """Update a space resource."""
    current_space = HPSpace.get(name=config['name'], namespace=config['namespace'])
    if not config.get("display_name"):
        config["display_name"] = current_space.config.display_name

    current_space.update(**config)
    click.echo(f"Space '{current_space.config.name}' updated successfully in namespace '{config['namespace']}'")


@click.command("hyp-space")
@click.option("--name", required=True, help="Name of the space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "start_space")
@handle_cli_exceptions()
def space_start(name, namespace):
    """Start a space resource."""
    current_space = HPSpace.get(name=name, namespace=namespace)
    current_space.start()
    click.echo(f"Space '{name}' start requested")


@click.command("hyp-space")
@click.option("--name", required=True, help="Name of the space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "stop_space")
@handle_cli_exceptions()
def space_stop(name, namespace):
    """Stop a space resource."""
    current_space = HPSpace.get(name=name, namespace=namespace)
    current_space.stop()
    click.echo(f"Space '{name}' stop requested")


@click.command("hyp-space")
@click.option("--name", required=True, help="Name of the space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
@click.option("--pod-name", required=False, help="Name of the pod to get logs from")
@click.option("--container", required=False, help="Name of the container to get logs from")
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "get_logs_for_space")
@handle_cli_exceptions()
def space_get_logs(name, namespace, pod_name, container):
    """Get logs for a space resource."""
    current_space = HPSpace.get(name=name, namespace=namespace)
    logs = current_space.get_logs(pod_name=pod_name, container=container)
    click.echo(logs)


@click.command("hyp-space")
@click.option("--name", required=True, help="Name of the space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
@click.option("--local-port", required=False, default=DEFAULT_SPACE_PORT, help="Localhost port that is mapped to the space")
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "portforward_for_space")
@handle_cli_exceptions()
def space_portforward(name, namespace, local_port):
    """Port forward to localhost for a space resource."""
    # Validate input port
    try:
        local_port = int(local_port)
    except ValueError:
        raise ValueError("Port values must be valid integers")

    if not (1 <= local_port <= 65535):
        raise ValueError(f"Port must be between 1 and 65535, got {local_port}")

    current_space = HPSpace.get(name=name, namespace=namespace)
    click.echo(f"Forwarding from local port {local_port} to space `{name}` in namespace `{namespace}`.")
    click.echo(f"Please access the service via `http://localhost:{local_port}`. Press Ctrl+C to stop.")
    current_space.portforward_space(local_port)
