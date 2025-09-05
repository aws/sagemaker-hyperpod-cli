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

from hyperpod_cli.service.exec_command import (
    ExecCommand,
)
from hyperpod_cli.service.get_logs import GetLogs
from hyperpod_cli.utils import (
    setup_logger,
    set_logging_level,
)
from hyperpod_cli.telemetry import _hyperpod_telemetry_emitter
from hyperpod_cli.telemetry.constants import Feature

logger = setup_logger(__name__)


@click.command()
@click.option(
    "--job-name",
    type=click.STRING,
    required=True,
    help="Required. The name of the job to get the log for.",
)
@click.option(
    "--pod",
    "-p",
    type=click.STRING,
    required=True,
    help="Required. The name of the pod to get the log from.",
)
@click.option(
    "--namespace",
    "-n",
    type=click.STRING,
    required=False,
    help="Optional. The namespace to get the log from. If not provided, the CLI will get the log from the pod in the namespace set by the user while connecting to the cluster. If provided, and the user has access to the namespace, the CLI will get the log from the pod in the specified namespace.",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode",
)
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_V2, "get_log_cli")
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
    
    try:
        cloudwatch_link = get_logs_service.generate_cloudwatch_link(pod, namespace=namespace)
        if cloudwatch_link:
            click.echo(cloudwatch_link)
    except Exception as e:
        click.echo(f"WARNING: Failed to generate container insights cloudwatch link: {e}")

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
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": False,
    },
)
@click.option(
    "--job-name",
    type=click.STRING,
    required=True,
    help="Required. The name of the job to execute the command on.",
)
@click.option(
    "--namespace",
    "-n",
    type=click.STRING,
    nargs=1,
    required=False,
    help="Optional. The namespace to execute the command in. If not provided, the CLI will try to execute the command in the pod in the namespace set by the user while connecting to the cluster. If provided, and the user has access to the namespace, the CLI will execute the command in the pod from the specified namespace.",
)
@click.option(
    "--pod",
    "-p",
    type=click.STRING,
    nargs=1,
    required=False,
    help="Optional. The name of the pod to execute the command in. You must provide either `--pod` or `--all-pods`.",
)
@click.option(
    "--all-pods",
    type=click.BOOL,
    is_flag=True,
    required=False,
    help="Optional. If set, the command will be executed in all pods associated with the job. You must provide either `--pod` or `--all-pods`.",
)
@click.argument(
    "bash_command",
    nargs=-1,
    type=click.UNPROCESSED,
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode",
)
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_V2, "exec_cli")
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
            job_name,
            pod,
            namespace,
            all_pods,
            bash_command,
        )
        click.echo(result)
    except Exception as e:
        sys.exit(
            f"Unexpected error happens when trying to exec command for pod {pod} : {e}"
        )
