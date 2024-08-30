# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
import sys
import logging
from typing import Optional

import click

from hyperpod_cli.service.exec_command import ExecCommand
from hyperpod_cli.service.get_logs import GetLogs
from hyperpod_cli.utils import setup_logger, set_logging_level

logger = setup_logger(__name__)


@click.command()
@click.option(
    "--job-name",
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
@click.option("--debug", is_flag=True, help="Enable debug mode")
def get_log(
    job_name: str,
    pod: str,
    namespace: Optional[str],
    debug: bool,
):
    """Get the log of the specified training job."""
    if debug:
        set_logging_level(logger, logging.DEBUG)

    get_logs_service = GetLogs()

    try:
        logger.debug("Getting logs for the training job")
        result = get_logs_service.get_training_job_logs(
            job_name, pod, namespace=namespace
        )
        click.echo(result)
    except Exception as e:
        sys.exit(
            f"Unexpected error happens when trying to get logs for training job {job_name} : {e}"
        )


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
    "--job-name",
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
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.argument("bash_command", nargs=-1, type=click.UNPROCESSED)
def exec(
    job_name: str,
    namespace: Optional[str],
    pod: Optional[str],
    all_pods: Optional[bool],
    debug: bool,
    bash_command: tuple,
):
    """Execute a bash command in the specified job."""
    if debug:
        set_logging_level(logger, logging.DEBUG)

    exec_command_service = ExecCommand()

    try:
        logger.debug("Executing command for the training job")
        result = exec_command_service.exec_command(
            job_name, pod, namespace, all_pods, bash_command
        )
        click.echo(result)
    except Exception as e:
        sys.exit(
            f"Unexpected error happens when trying to exec command for pod {pod} : {e}"
        )
