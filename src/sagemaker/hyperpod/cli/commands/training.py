import click
from sagemaker.hyperpod.training.hyperpod_pytorch_job import HyperPodPytorchJob, list_accelerator_partition_types
from sagemaker.hyperpod.common.config import Metadata
from sagemaker.hyperpod.cli.training_utils import generate_click_command
from hyperpod_pytorch_job_template.registry import SCHEMA_REGISTRY
from sagemaker.hyperpod.common.telemetry.telemetry_logging import (
    _hyperpod_telemetry_emitter,
)
from sagemaker.hyperpod.common.telemetry.constants import Feature
from sagemaker.hyperpod.common.cli_decorators import handle_cli_exceptions
from sagemaker.hyperpod.common.utils import display_formatted_logs


@click.command("hyp-pytorch-job")
@click.option("--version", default="1.0", help="Schema version to use")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@generate_click_command(
    schema_pkg="hyperpod_pytorch_job_template",
    registry=SCHEMA_REGISTRY,
)
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "create_pytorchjob_cli")
@handle_cli_exceptions()
def pytorch_create(version, debug, job):
    """Create a PyTorch job."""
    click.echo(f"Using version: {version}")
    # Create job
    job.create(debug=debug)


@click.command("hyp-pytorch-job")
@click.option(
    "--namespace",
    "-n",
    default="default",
    help="Optional. The namespace to list jobs from. Defaults to 'default' namespace.",
)
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "list_pytorchjobs_cli")
@handle_cli_exceptions()
def list_jobs(namespace: str):
    """List all HyperPod PyTorch jobs."""
    jobs = HyperPodPytorchJob.list(namespace=namespace)

    if not jobs:
        click.echo("No jobs found.")
        return

    # Define headers and widths
    headers = ["NAME", "NAMESPACE", "STATUS", "AGE"]
    widths = [30, 20, 15, 15]

    # Print header
    header = "".join(f"{h:<{w}}" for h, w in zip(headers, widths))
    click.echo("\n" + header)
    click.echo("-" * sum(widths))

    # Print each job
    for job in jobs:
        # Get status from conditions
        status = "Unknown"
        age = "N/A"
        if job.status and job.status.conditions:
            for condition in reversed(job.status.conditions):
                if condition.status == "True":
                    status = condition.type
                    break

            # Calculate age
            if job.status and job.status.conditions:
                # Find the 'Created' condition to get the start time
                created_condition = next(
                    (c for c in job.status.conditions if c.type == "Created"), None
                )
                if created_condition and created_condition.lastTransitionTime:
                    from datetime import datetime, timezone

                    start_time = datetime.fromisoformat(
                        created_condition.lastTransitionTime.replace("Z", "+00:00")
                    )
                    now = datetime.now(timezone.utc)
                    delta = now - start_time
                    if delta.days > 0:
                        age = f"{delta.days}d"
                    else:
                        hours = delta.seconds // 3600
                        if hours > 0:
                            age = f"{hours}h"
                        else:
                            minutes = (delta.seconds % 3600) // 60
                            age = f"{minutes}m"

        # Format row
        row = "".join(
            [
                f"{job.metadata.name:<{widths[0]}}",
                f"{job.metadata.namespace:<{widths[1]}}",
                f"{status:<{widths[2]}}",
                f"{age:<{widths[3]}}",
            ]
        )
        click.echo(row)

        click.echo()  # Add empty line at the end


@click.command("hyp-pytorch-job")
@click.option(
    "--job-name", required=True, help="Required. The name of the job to describe"
)
@click.option(
    "--namespace",
    "-n",
    default="default",
    help="Optional. The namespace of the job. Defaults to 'default' namespace.",
)
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "get_pytorchjob_cli")
@handle_cli_exceptions()
def pytorch_describe(job_name: str, namespace: str):
    """Describe a HyperPod PyTorch job."""
    job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)

    if job is None:
        raise Exception(f"Job {job_name} not found in namespace {namespace}")

    # Print basic info
    click.echo("\nJob Details:")
    click.echo("=" * 80)
    click.echo(f"Name:           {job.metadata.name}")
    click.echo(f"Namespace:      {job.metadata.namespace}")
    click.echo(f"Labels:         {job.metadata.labels}")
    click.echo(f"Annotations:    {job.metadata.annotations}")

    # Print Spec details
    click.echo("\nSpec:")
    click.echo("-" * 80)
    click.echo(f"Processes per Node: {getattr(job, 'nprocPerNode', 'N/A')}")

    # Print Replica Specs
    for replica in job.replicaSpecs:
        click.echo(f"\nReplica Spec:")
        click.echo(f"  Name:     {getattr(replica, 'name', 'N/A')}")
        click.echo(f"  Replicas: {getattr(replica, 'replicas', 'N/A')}")
        click.echo(f"  Spares:   {getattr(replica, 'spares', 'N/A')}")

        # Container details
        if (
            hasattr(replica, "template")
            and hasattr(replica.template, "spec")
            and hasattr(replica.template.spec, "containers")
        ):
            for container in replica.template.spec.containers:
                click.echo("\n  Container:")
                click.echo(
                    f"    Name:            {getattr(container, 'name', 'N/A')}"
                )
                click.echo(
                    f"    Image:           {getattr(container, 'image', 'N/A')}"
                )
                click.echo(
                    f"    Image Pull Policy: {getattr(container, 'imagePullPolicy', 'N/A')}"
                )
                if container.resources:
                    click.echo("    Resources:")
                    if container.resources.limits:
                        click.echo(f"      Limits:   {container.resources.limits}")
                    if container.resources.requests:
                        click.echo(
                            f"      Requests: {container.resources.requests}"
                        )

    # Print Run Policy
    click.echo("\nRun Policy:")
    click.echo("-" * 80)
    if hasattr(job, "runPolicy"):
        click.echo(
            f"Clean Pod Policy:          {getattr(job.runPolicy, 'cleanPodPolicy', 'N/A')}"
        )
        click.echo(
            f"TTL Seconds After Finished: {getattr(job.runPolicy, 'ttlSecondsAfterFinished', 'N/A')}"
        )
    else:
        click.echo("Run Policy: N/A")

    # Print Status
    click.echo("\nStatus:")
    click.echo("-" * 80)
    if job.status:
        if job.status.conditions:
            click.echo("Conditions:")
            for condition in job.status.conditions:
                click.echo(
                    f"  Type:               {getattr(condition, 'type', 'N/A')}"
                )
                click.echo(
                    f"  Status:             {getattr(condition, 'status', 'N/A')}"
                )
                click.echo(
                    f"  Last Transition:    {getattr(condition, 'lastTransitionTime', 'N/A')}"
                )
                if condition.message:
                    click.echo(f"  Message:            {condition.message}")
                click.echo()
    else:
        click.echo("No status information available")


@click.command("hyp-pytorch-job")
@click.option(
    "--job-name", required=True, help="Required. The name of the job to delete"
)
@click.option(
    "--namespace",
    "-n",
    default="default",
    help="Optional. The namespace of the job. Defaults to 'default' namespace.",
)
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "delete_pytorchjob_cli")
@handle_cli_exceptions()
def pytorch_delete(job_name: str, namespace: str):
    """Delete a HyperPod PyTorch job."""
    job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)
    job.delete()


@click.command("hyp-pytorch-job")
@click.option(
    "--job-name",
    required=True,
    help="Required. Specify the job name to list its associated pods.",
)
@click.option(
    "--namespace",
    "-n",
    default="default",
    help="Optional. The namespace of the job. Defaults to 'default' namespace.",
)
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "list_pods_pytorchjob_cli")
@handle_cli_exceptions()
def pytorch_list_pods(job_name: str, namespace: str):
    """List all HyperPod PyTorch pods related to the job."""
    job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)
    pods = job.list_pods()

    if not pods:
        click.echo(f"\nNo pods found for job: {job_name}")
        return

    # Define headers and widths
    headers = ["POD NAME", "NAMESPACE"]
    widths = [50, 20]

    # Print header
    click.echo(f"\nPods for job: {job_name}")
    header = "".join(f"{h:<{w}}" for h, w in zip(headers, widths))
    click.echo("\n" + header)
    click.echo("-" * sum(widths))

    # Print each pod
    for pod in pods:
        row = "".join([f"{pod:<{widths[0]}}", f"{namespace:<{widths[1]}}"])
        click.echo(row)

    click.echo()


@click.command("hyp-pytorch-job")
@click.option(
    "--job-name",
    required=True,
    help="Required. Specify the job name for pod log retrieval.",
)
@click.option(
    "--pod-name", required=True, help="Required. The name of the pod to get logs from."
)
@click.option(
    "--namespace",
    "-n",
    default="default",
    help="Optional. The namespace of the job. Defaults to 'default' namespace.",
)
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "get_pytorchjob_logs_from_pod_cli")
@handle_cli_exceptions()
def pytorch_get_logs(job_name: str, pod_name: str, namespace: str):
    """Get specific pod log for Hyperpod Pytorch job."""
    click.echo("Listing logs for pod: " + pod_name)
    job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)
    logs = job.get_logs_from_pod(pod_name=pod_name)

    # Use common log display utility for consistent formatting across all job types
    display_formatted_logs(logs, title=f"Pod Logs for {pod_name}")


@click.command("hyp-pytorch-job")
@click.option(
    "--since-hours",
    type=click.FLOAT,
    required=True,
    help="Required. The time frame to get logs for.",
)
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "get_pytorch_operator_logs")
@handle_cli_exceptions()
def pytorch_get_operator_logs(since_hours: float):
    """Get operator logs for pytorch training jobs."""
    logs = HyperPodPytorchJob.get_operator_logs(since_hours=since_hours)

    # Use common log display utility for consistent formatting across all job types
    display_formatted_logs(logs, title="PyTorch Operator Logs")


@click.command("hyp-pytorch-job",
               help="""Execute commands in pods associated with a HyperPod PyTorch job.

Usage Format:
  hyp exec --job-name <job-name> [-p <pod-name>] [--all-pods] -- <command>""")
@click.option("--job-name", required=True, help="Required. The name of the job to execute the command within.")
@click.option("--pod", "-p", help="The name of the pod to execute the command in. (Required: specify either --pod or --all-pods)")
@click.option("--all-pods", is_flag=True, help="Execute command in all pods associated with the job. (Required: specify either --pod or --all-pods)")
@click.option("--namespace", "-n", default="default", help="Optional. The namespace of the job.")
@click.option("--container", help="Optional. The container name to execute the command in.")
@click.argument("command", nargs=-1, required=True)
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "exec_pytorchjob_cli")
def pytorch_exec(job_name: str, pod: str, all_pods: bool, namespace: str, container: str, command: tuple):
    """Execute commands in pods associated with a HyperPod PyTorch job."""
    if (all_pods and pod) or not (all_pods or pod):
        raise click.UsageError("Must specify exactly one of the following: --all-pods, --pod")

    try:
        job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)
        output = job.exec_command(list(command), pod, all_pods, container)
        if output:
            click.echo(output)
        else:
            click.echo("Command executed successfully (no output)")
    except ValueError as e:
        # User input validation errors
        raise click.UsageError(str(e))
    except Exception as e:
        # Other errors (API, network, etc.)
        raise click.UsageError(f"Failed to execute command: {str(e)}")

@click.command("list-accelerator-partition-type")
@click.option(
    "--instance-type",
    required=True,
    help="The instance type to list accelerator partition types for."
)
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "list_accelerator_partition_types_cli")
@handle_cli_exceptions()
def list_accelerator_partition_type(instance_type: str):
    """List available accelerator partition types for an instance type."""
    try:
        partition_types = list_accelerator_partition_types(instance_type)
        for partition_type in partition_types:
            click.echo(partition_type)
    except (ValueError, RuntimeError) as e:
        raise click.UsageError(str(e))
    except Exception as e:
        raise click.UsageError(f"Failed to execute command: {str(e)}")
