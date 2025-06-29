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
import click
import importlib.metadata

from hyperpod_cli.commands.cluster import (
    set_cluster_context,
    list_cluster,
    metrics,
    get_cluster_context,
)
from hyperpod_cli.commands.job import (
    cancel_job,
    get_job,
    list_jobs,
    list_pods,
    patch_job,
    start_job,
)
from hyperpod_cli.commands.pod import (
    exec,
    get_log,
)

HELP_TEXT = """
Find more information at: https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod.html

Basic Commands:
  * get-clusters    Get clusters information for HyperPod EKS clusters.
  * connect-cluster Creates a connection from users local terminal to the HyperPod cluster 
                    allowing user to start and preform other basic operations with training jobs.
  * start-job       Start a training job from a file on HyperPod cluster.
  * get-job         Show details of a specific training job submitted on HyperPod cluster.
  * list-jobs       List training job on a HyperPod cluster.
  * cancel-job      Cancel training job on a HyperPod cluster.
  * patch-job       Patch a job with specific operation on a HyperPod cluster.
Troubleshooting and Debugging Commands:
  * get-log         Get logs for a pod of training job running on HyperPod cluster.
  * list-pods       List all pods associated with a training job on HyperPod cluster.
  * exec            Execute a command on a pod of a training job on HyperPod cluster.

Usage:
  hyperpod [command] [options]

Use "hyperpod <command> --help" for more information about a given command.
"""

VERSION = importlib.metadata.version("hyperpod")


class HyperPodCommandGroup(click.Group):
    def format_help(self, ctx, formatter):
        click.echo(HELP_TEXT)


@click.group(cls=HyperPodCommandGroup)
@click.version_option(version=VERSION)
def cli():
    pass


cli.add_command(list_cluster)
cli.add_command(set_cluster_context)
cli.add_command(get_cluster_context)
cli.add_command(metrics)
cli.add_command(start_job)
cli.add_command(get_job)
cli.add_command(list_jobs)
cli.add_command(cancel_job)
cli.add_command(patch_job)
cli.add_command(exec)
cli.add_command(list_pods)
cli.add_command(get_log)

if __name__ == "__main__":
    cli()
