import click
import yaml
import json
import os
import subprocess
from pydantic import BaseModel, ValidationError, Field
from typing import Optional, Union
from importlib.metadata import version, PackageNotFoundError

from sagemaker.hyperpod.cli.commands.cluster import list_cluster, set_cluster_context, get_cluster_context, \
    get_monitoring, describe_cluster
from sagemaker.hyperpod.cli.commands.cluster_stack import create_cluster_stack, describe_cluster_stack, \
    list_cluster_stacks, update_cluster, delete_cluster_stack
from sagemaker.hyperpod.cli.commands.training import (
    pytorch_create,
    list_jobs,
    pytorch_describe,
    pytorch_delete,
    pytorch_list_pods,
    pytorch_get_logs,
    pytorch_get_operator_logs,
    pytorch_exec,
    list_accelerator_partition_type,
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
from sagemaker.hyperpod.cli.commands.space import (
    space_create,
    space_list,
    space_describe,
    space_delete,
    space_update,
    space_start,
    space_stop,
    space_get_logs,
)
from sagemaker.hyperpod.cli.commands.space_template import (
    space_template_create,
    space_template_list,
    space_template_describe,
    space_template_delete,
    space_template_update,
)
from sagemaker.hyperpod.cli.commands.space_access import space_access_create

from sagemaker.hyperpod.cli.commands.init import (
    init,
    reset,
    configure,
    validate,
    _default_create
)


def get_package_version(package_name):
    try:
        return version(package_name)
    except PackageNotFoundError:
        return "Not installed"

def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    hyp_version = get_package_version("sagemaker-hyperpod")
    pytorch_template_version = get_package_version("hyperpod-pytorch-job-template")
    custom_inference_version = get_package_version("hyperpod-custom-inference-template")
    jumpstart_inference_version = get_package_version("hyperpod-jumpstart-inference-template")

    click.echo(f"hyp version: {hyp_version}")
    click.echo(f"hyperpod-pytorch-job-template version: {pytorch_template_version}")
    click.echo(f"hyperpod-custom-inference-template version: {custom_inference_version}")
    click.echo(f"hyperpod-jumpstart-inference-template version: {jumpstart_inference_version}")
    ctx.exit()


@click.group(context_settings={'max_content_width': 200})
@click.option('--version', is_flag=True, callback=print_version, expose_value=False, is_eager=True, help='Show version information')
def cli():
    pass


class CLICommand(click.Group):
    def __init__(self, *args, default_cmd: Union[str, None] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_cmd = default_cmd

    def parse_args(self, ctx, args):
        # Only inject default subcommand when:
        #  - user didn't name a subcommand, and
        #  - user didn't ask for help
        if self.default_cmd:
            # any non-flag token that is a known subcommand?
            has_subcmd = any((not a.startswith("-")) and (a in self.commands) for a in args)
            asked_for_help = any(a in ("-h", "--help") for a in args)
            if (not has_subcmd) and (not asked_for_help):
                args = [self.default_cmd] + args
        return super().parse_args(ctx, args)


@cli.group(cls=CLICommand, default_cmd='_default_create')
def create():
    """
    Create endpoints, pytorch jobs, cluster stacks, space, space access or space admin config.

    If only used as 'hyp create' without [OPTIONS] COMMAND [ARGS] during init experience,
    then it will validate configuration and render template files for deployment.
    The generated files in the run directory can be used for actual deployment
    to SageMaker HyperPod clusters or CloudFormation stacks.

    Prerequisites for directly calling 'hyp create':
    - Must be run in a directory initialized with 'hyp init'
    - config.yaml and the appropriate template file must exist
    """
    pass


@cli.group(cls=CLICommand)
def list():
    """List endpoints, pytorch jobs, cluster stacks, spaces, and space templates."""
    pass


@cli.group(cls=CLICommand)
def describe():
    """Describe endpoints, pytorch jobs or cluster stacks, spaces or space template."""
    pass

@cli.group(cls=CLICommand)
def update():
    """Update an existing HyperPod cluster configuration, space, or space template."""
    pass

@cli.group(cls=CLICommand)
def delete():
    """Delete endpoints, pytorch jobs, space, space access or space template."""
    pass


@cli.group(cls=CLICommand)
def start():
    """Start space resources."""
    pass


@cli.group(cls=CLICommand)
def stop():
    """Stop space resources."""
    pass





@cli.group(cls=CLICommand)
def list_pods():
    """List pods for endpoints or pytorch jobs."""
    pass


@cli.group(cls=CLICommand)
def get_logs():
    """Get pod logs for endpoints, pytorch jobs or spaces."""
    pass


@cli.group(cls=CLICommand)
def invoke():
    """Invoke model endpoints."""
    pass


@cli.group(cls=CLICommand)
def get_operator_logs():
    """Get operator logs for endpoints."""
    pass


@cli.group(cls=CLICommand)
def exec():
    """Execute commands in pods for endpoints or pytorch jobs."""
    pass


cli.add_command(init)
cli.add_command(reset)
cli.add_command(configure)
cli.add_command(validate)

create.add_command(pytorch_create)
create.add_command(js_create)
create.add_command(custom_create)

_default_create.hidden = True
create.add_command(_default_create)
create.add_command(space_create)
create.add_command(space_template_create)
create.add_command(space_access_create)

list.add_command(list_jobs)
list.add_command(js_list)
list.add_command(custom_list)
list.add_command(list_cluster_stacks)
list.add_command(space_list)
list.add_command(space_template_list)

describe.add_command(pytorch_describe)
describe.add_command(js_describe)
describe.add_command(custom_describe)
describe.add_command(describe_cluster_stack)

describe.add_command(describe_cluster)
describe.add_command(space_describe)
describe.add_command(space_template_describe)

update.add_command(update_cluster)
update.add_command(space_update)
update.add_command(space_template_update)

delete.add_command(pytorch_delete)
delete.add_command(js_delete)
delete.add_command(custom_delete)
delete.add_command(delete_cluster_stack)
delete.add_command(space_delete)
delete.add_command(space_template_delete)

start.add_command(space_start)

stop.add_command(space_stop)

list_pods.add_command(pytorch_list_pods)
list_pods.add_command(js_list_pods)
list_pods.add_command(custom_list_pods)

get_logs.add_command(pytorch_get_logs)
get_logs.add_command(js_get_logs)
get_logs.add_command(custom_get_logs)
get_logs.add_command(space_get_logs)



get_operator_logs.add_command(pytorch_get_operator_logs)
get_operator_logs.add_command(js_get_operator_logs)
get_operator_logs.add_command(custom_get_operator_logs)

invoke.add_command(custom_invoke)
invoke.add_command(custom_invoke, name="hyp-jumpstart-endpoint")

cli.add_command(list_cluster)
cli.add_command(set_cluster_context)
cli.add_command(get_cluster_context)
cli.add_command(get_monitoring)
# cli.add_command(create_cluster_stack) # Not supported yet
cli.add_command(list_accelerator_partition_type)

exec.add_command(pytorch_exec)

if __name__ == "__main__":
    cli()
