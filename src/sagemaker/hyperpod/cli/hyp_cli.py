import click
import yaml
import json
import os
import subprocess
from pydantic import BaseModel, ValidationError, Field
from typing import Optional

from sagemaker.hyperpod.cli.commands.cluster import list_cluster, set_cluster_context, get_cluster_context, \
    get_monitoring
from sagemaker.hyperpod.cli.commands.training import (
    pytorch_create,
    list_jobs,
    pytorch_describe,
    pytorch_delete,
    pytorch_list_pods,
    pytorch_get_logs,
)
from sagemaker.hyperpod.cli.commands.inference import (
    js_create,
    custom_create,
    custom_invoke,
    js_list,
    custom_list,
    js_describe,
    custom_describe,
    js_delete,
    custom_delete,
    js_list_pods,
    custom_list_pods,
    js_get_logs,
    custom_get_logs,
    js_get_operator_logs,
    custom_get_operator_logs,
)


@click.group()
def cli():
    pass


class CLICommand(click.Group):
    pass


@cli.group(cls=CLICommand)
def create():
    """Create a jumpstart model endpoint, a custom model endpoint, or a pytorch job."""
    pass


@cli.group(cls=CLICommand)
def list():
    """List all jumpstart model endpoints, custom model endpoints, or pytorch jobs."""
    pass


@cli.group(cls=CLICommand)
def describe():
    """Describe a jumpstart model endpoint, a custom model endpoint, or a pytorch job."""
    pass


@cli.group(cls=CLICommand)
def delete():
    """Delete a jumpstart model endpoint, a custom model endpoint, or a pytorch job."""
    pass


@cli.group(cls=CLICommand)
def list_pods():
    """List all pods for jumpstart model endpoint, custom model endpoint or pytorch jobs."""
    pass


@cli.group(cls=CLICommand)
def get_logs():
    """Get specific pod logs for a jumpstart model endpoint, custom model endpoint or pytorch job."""
    pass


@cli.group(cls=CLICommand)
def invoke():
    """Invoke a jumpstart model endpoint or a custom model endpoint."""
    pass


@cli.group(cls=CLICommand)
def get_operator_logs():
    """Get operator logs for jumpstart model endpoint, or custom model endpoint."""
    pass


create.add_command(pytorch_create)
create.add_command(js_create)
create.add_command(custom_create)

list.add_command(list_jobs)
list.add_command(js_list)
list.add_command(custom_list)

describe.add_command(pytorch_describe)
describe.add_command(js_describe)
describe.add_command(custom_describe)

delete.add_command(pytorch_delete)
delete.add_command(js_delete)
delete.add_command(custom_delete)

list_pods.add_command(pytorch_list_pods)
list_pods.add_command(js_list_pods)
list_pods.add_command(custom_list_pods)

get_logs.add_command(pytorch_get_logs)
get_logs.add_command(js_get_logs)
get_logs.add_command(custom_get_logs)

get_operator_logs.add_command(js_get_operator_logs)
get_operator_logs.add_command(custom_get_operator_logs)

invoke.add_command(custom_invoke)
invoke.add_command(custom_invoke, name="hyp-jumpstart-endpoint")

cli.add_command(list_cluster)
cli.add_command(set_cluster_context)
cli.add_command(get_cluster_context)
cli.add_command(get_monitoring)


if __name__ == "__main__":
    cli()
