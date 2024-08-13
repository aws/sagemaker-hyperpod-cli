import sys
from typing import Optional

import click

from hyperpod_cli.service.exec_command import ExecCommand
from hyperpod_cli.service.get_logs import GetLogs


@click.command()
@click.option(
    "--name",
    type=click.STRING,
    required=True,
    help="The name of the training job you want to view logs",
)
@click.option(
    "--pod",
    "-p",
    type=click.STRING,
    required=True,
    help="The name of the pod you want to view logs",
)
@click.option(
    "--namespace",
    "-n",
    type=click.STRING,
    required=False,
    help="The namespace where training job was submitted",
)
def get_log(name: str, pod: str, namespace: Optional[str]):
    """Get the log of the specified training job."""

    get_logs_service = GetLogs()

    try:
        result = get_logs_service.get_training_job_logs(name, pod, namespace=namespace)
        click.echo(result)
    except Exception as e:
        sys.exit(f"Unexpected error happens when trying to get logs for training job {name} : {e}")


def _exec_command_required_option_pod_and_all_pods():
    class OptionRequiredClass(click.Command):

        def invoke(self, ctx):
            pod = ctx.params["pod"]
            all_pods = ctx.params["all_pods"]
            if not pod and not all_pods:
                raise click.ClickException(
                    "With job-name name must specify option --pod or --all-pods"
                )
            if pod and all_pods:
                raise click.ClickException(
                    "With job-name name must specify only one option --pod or --all-pods"
                )
            super(OptionRequiredClass, self).invoke(ctx)

    return OptionRequiredClass


@click.command(
    cls=_exec_command_required_option_pod_and_all_pods(),
    context_settings={"ignore_unknown_options": True, "allow_extra_args": False},
)
@click.option(
    "--name",
    type=click.STRING,
    required=True,
    help="The name of the training job you want to view logs",
)
@click.option(
    "--namespace",
    "-n",
    type=click.STRING,
    nargs=1,
    required=False,
    help="The namespace where training job was submitted",
)
@click.option(
    "--pod",
    "-p",
    type=click.STRING,
    nargs=1,
    required=False,
    help="The name of the pod you want to view logs",
)
@click.option(
    "--all-pods",
    type=click.BOOL,
    is_flag=True,
    required=False,
    help="The name of the pod you want to view logs",
)
@click.argument("bash_command", nargs=-1, type=click.UNPROCESSED)
def exec(
    name: str,
    namespace: Optional[str],
    pod: Optional[str],
    all_pods: Optional[bool],
    bash_command: tuple,
):
    """Execute a bash command in the specified job."""
    exec_command_service = ExecCommand()

    try:
        result = exec_command_service.exec_command(name, pod, namespace, all_pods, bash_command)
        click.echo(result)
    except Exception as e:
        sys.exit(f"Unexpected error happens when trying to exec command for pod {pod} : {e}")
