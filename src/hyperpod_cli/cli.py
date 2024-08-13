import click

from hyperpod_cli.commands.cluster import connect_cluster, list_clusters
from hyperpod_cli.commands.job import (
    cancel_job,
    get_job,
    list_jobs,
    list_pods,
    start_job,
)
from hyperpod_cli.commands.pod import exec, get_log


@click.group()
def cli():
    pass


cli.add_command(list_clusters)
cli.add_command(connect_cluster)
cli.add_command(start_job)
cli.add_command(get_job)
cli.add_command(list_jobs)
cli.add_command(cancel_job)
cli.add_command(exec)
cli.add_command(list_pods)
cli.add_command(get_log)


if __name__ == "__main__":
    cli()
