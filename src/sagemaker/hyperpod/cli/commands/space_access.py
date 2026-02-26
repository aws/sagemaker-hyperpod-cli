import click
from sagemaker.hyperpod.space.hyperpod_space import HPSpace
from sagemaker.hyperpod.common.telemetry.telemetry_logging import (
    _hyperpod_telemetry_emitter,
)
from sagemaker.hyperpod.common.telemetry.constants import Feature
from sagemaker.hyperpod.common.cli_decorators import handle_cli_exceptions


@click.command("hyp-space-access")
@click.option("--name", required=True, help="Name of the space")
@click.option("--namespace", "-n", required=False, default="default", help="Kubernetes namespace")
@click.option("--connection-type", "-t",
    required=False,
    default="vscode-remote",
    help="Remote access type supported values: [vscode-remote, web-ui] [default: vscode-remote]"
)
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "create_space_access")
@handle_cli_exceptions()
def space_access_create(name, namespace, connection_type):
    """Create a space access resource."""
    space = HPSpace.get(name=name, namespace=namespace)
    response = space.create_space_access(connection_type=connection_type)
    click.echo(response)
