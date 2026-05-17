# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License.

import click
import json
import subprocess
import sys
from urllib.parse import urlparse, parse_qs

from sagemaker.hyperpod.space.hyperpod_space import HPSpace
from sagemaker.hyperpod.common.telemetry.telemetry_logging import _hyperpod_telemetry_emitter
from sagemaker.hyperpod.common.telemetry.constants import Feature
from sagemaker.hyperpod.common.cli_decorators import handle_cli_exceptions
from sagemaker.hyperpod.common.utils import _resolve_region as resolve_region


@click.command("hyp-space")
@click.option("--name", required=True, help="Name of the space to SSH into")
@click.option("--namespace", "-n", default="default", help="Kubernetes namespace")
@click.option("--region", default=None, help="AWS region (defaults to configured region)")
@click.option("--debug", is_flag=True, default=False, help="Enable debug mode")
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "ssh_space")
@handle_cli_exceptions()
def space_ssh(name, namespace, region, debug):
    """SSH into a running HyperPod space via SSM Session Manager.

    Establishes an interactive SSH session to the specified workspace
    using AWS Systems Manager Session Manager as the transport layer.
    This provides secure, auditable access without requiring inbound
    firewall rules or bastion hosts.

    Prerequisites:
        - AWS Session Manager Plugin installed
        - Space must be in 'Available' status
        - Valid AWS credentials with ssm:StartSession permission

    Example:
        hyp ssh hyp-space --name my-workspace
        hyp ssh hyp-space --name my-workspace --namespace team-ns
    """
    region = region or resolve_region()

    # Get the space and verify it's available
    space = HPSpace.get(name=name, namespace=namespace)

    if space.status:
        conditions = space.status.get("conditions", [])
        is_available = any(
            c.get("type") == "Available" and c.get("status") == "True"
            for c in conditions
        )
        if not is_available:
            raise click.ClickException(
                f"Space '{name}' is not in Available status. "
                f"Start it with: hyp start hyp-space --name {name}"
            )

    # Create a space access to get the SSM connection details
    click.echo(f"Connecting to space '{name}'...")
    access_info = space.create_space_access(connection_type="ssh-remote")
    connection_url = access_info.get("SpaceConnectionUrl", "")

    if debug:
        click.echo(f"Connection URL: {connection_url}")

    # Parse the connection URL to extract SSM target details
    ssm_target, ssm_params = _parse_ssh_connection_url(connection_url)

    if not ssm_target:
        raise click.ClickException(
            f"Could not determine SSM target from connection URL. "
            f"URL received: {connection_url}"
        )

    # Start SSM session
    _start_ssm_session(ssm_target, ssm_params, region, debug)


def _parse_ssh_connection_url(connection_url: str) -> tuple:
    """Parse the space connection URL to extract SSM target and parameters.

    The connection URL format from the WorkspaceConnection CRD contains
    the SSM managed instance ID and optional document/parameters for
    establishing the SSH session.

    Returns:
        tuple: (target_id, parameters_dict)
    """
    if not connection_url:
        return None, {}

    parsed = urlparse(connection_url)
    params = parse_qs(parsed.query)

    # The URL may contain the target directly or in query params
    # Format: ssm://<instance-id>?documentName=...&parameters=...
    # Or: https://<endpoint>/ssm?target=<instance-id>&...
    target = None
    ssm_params = {}

    if parsed.scheme == "ssm":
        target = parsed.hostname or parsed.path.strip("/")
    elif "target" in params:
        target = params["target"][0]
    elif "instanceId" in params:
        target = params["instanceId"][0]
    else:
        # Fallback: treat the path as the target
        target = parsed.path.strip("/") if parsed.path else None

    if "documentName" in params:
        ssm_params["documentName"] = params["documentName"][0]
    if "portNumber" in params:
        ssm_params["portNumber"] = params["portNumber"][0]

    return target, ssm_params


def _start_ssm_session(target: str, params: dict, region: str, debug: bool = False):
    """Start an interactive SSM session to the workspace.

    Uses the AWS Session Manager Plugin to establish a direct
    SSH-like terminal session to the managed instance backing
    the HyperPod space.
    """
    cmd = [
        "aws", "ssm", "start-session",
        "--target", target,
        "--region", region,
    ]

    if params.get("documentName"):
        cmd.extend(["--document-name", params["documentName"]])

    if params.get("portNumber"):
        cmd.extend([
            "--parameters",
            json.dumps({"portNumber": [params["portNumber"]]})
        ])

    if debug:
        click.echo(f"Running: {' '.join(cmd)}")

    click.echo(f"Starting SSH session to '{target}'...")
    click.echo("Use 'exit' or Ctrl+D to end the session.\n")

    try:
        result = subprocess.run(cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        if result.returncode != 0:
            if result.returncode == 127:
                raise click.ClickException(
                    "AWS Session Manager Plugin not found. Install it from: "
                    "https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html"
                )
            raise click.ClickException(
                f"SSM session exited with code {result.returncode}. "
                f"Ensure you have valid AWS credentials and ssm:StartSession permissions."
            )
    except FileNotFoundError:
        raise click.ClickException(
            "AWS CLI not found. Install it from: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        )
    except KeyboardInterrupt:
        click.echo("\nSession terminated.")
