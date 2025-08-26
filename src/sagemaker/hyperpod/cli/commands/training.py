import click
import sys
from typing import Any
from sagemaker.hyperpod.common.cli_decorators import handle_cli_exceptions
from sagemaker.hyperpod.common.lazy_loading import LazyDecorator, setup_lazy_module
from sagemaker.hyperpod.cli.command_registry import register_training_command

TRAINING_CONFIG = {
    'exports': [
        'HyperPodPytorchJob', 'Metadata', 'generate_click_command', 'SCHEMA_REGISTRY',
        '_hyperpod_telemetry_emitter', 'Feature', 'display_formatted_logs'
    ],
    'template_packages': {
        'template_package': 'hyperpod_pytorch_job_template',
        'supported_versions': ['1.0', '1.1'],
    },
    'critical_deps': ['telemetry_emitter', 'telemetry_feature', 'training_utils'],
    'lazy_imports': {
        'HyperPodPytorchJob': 'sagemaker.hyperpod.training.hyperpod_pytorch_job:HyperPodPytorchJob',
        'Metadata': 'sagemaker.hyperpod.common.config:Metadata',
        'generate_click_command': 'sagemaker.hyperpod.cli.training_utils:generate_click_command',
        'SCHEMA_REGISTRY': 'hyperpod_pytorch_job_template.registry:SCHEMA_REGISTRY',
        '_hyperpod_telemetry_emitter': 'sagemaker.hyperpod.common.telemetry.telemetry_logging:_hyperpod_telemetry_emitter',
        'Feature': 'sagemaker.hyperpod.common.telemetry.constants:Feature',
        'display_formatted_logs': 'sagemaker.hyperpod.common.utils:display_formatted_logs'
    }
}

def _setup_training_registries(deps):
    """Setup training-specific registries."""
    from sagemaker.hyperpod.common.lazy_loading import LazyRegistry
    registry = LazyRegistry(
        versions=['1.0', '1.1'],
        registry_import_path='hyperpod_pytorch_job_template.registry:SCHEMA_REGISTRY'
    )
    deps['SCHEMA_REGISTRY'] = registry
    setattr(sys.modules[__name__], 'SCHEMA_REGISTRY', registry)

TRAINING_CONFIG['extra_setup'] = _setup_training_registries
setup_lazy_module(__name__, TRAINING_CONFIG)

def _get_telemetry_emitter():
    return getattr(sys.modules[__name__], '_hyperpod_telemetry_emitter')

def _get_generate_click_command():
    return getattr(sys.modules[__name__], 'generate_click_command')


@register_training_command("hyp-pytorch-job", "create")
@click.option("--version", default="1.1", help="Schema version to use")
@click.option("--debug", default=False, help="Enable debug mode")
@LazyDecorator(_get_generate_click_command,
    schema_pkg=lambda: sys.modules[__name__]._MODULE_CONFIG["template_package"],
    registry=lambda: sys.modules[__name__].SCHEMA_REGISTRY,
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "create_pytorchjob_cli")
@handle_cli_exceptions()
def pytorch_create(version, debug, config):
    """Create a PyTorch job."""
    click.echo(f"Using version: {version}")
    job_name = config.get("name")
    namespace = config.get("namespace")
    spec = config.get("spec")
    metadata_labels = config.get("labels")
    annotations = config.get("annotations")

    # Prepare metadata
    metadata_kwargs = {"name": job_name}
    if namespace:
        metadata_kwargs["namespace"] = namespace
    if metadata_labels:
        metadata_kwargs["labels"] = metadata_labels
    if annotations:
        metadata_kwargs["annotations"] = annotations

    # Prepare job kwargs
    job_kwargs = {
        "metadata": sys.modules[__name__].Metadata(**metadata_kwargs),
        "replica_specs": spec.get("replica_specs"),
    }

    # Add nproc_per_node if present
    if "nproc_per_node" in spec:
        job_kwargs["nproc_per_node"] = spec.get("nproc_per_node")

    # Add run_policy if present
    if "run_policy" in spec:
        job_kwargs["run_policy"] = spec.get("run_policy")

    # Create job
    job = sys.modules[__name__].HyperPodPytorchJob(**job_kwargs)
    job.create(debug=debug)


@register_training_command("hyp-pytorch-job", "list")
@click.option(
    "--namespace",
    "-n",
    default="default",
    help="Optional. The namespace to list jobs from. Defaults to 'default' namespace.",
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "list_pytorchjobs_cli")
@handle_cli_exceptions()
def list_jobs(namespace: str):
    """List all HyperPod PyTorch jobs."""
    jobs = sys.modules[__name__].HyperPodPytorchJob.list(namespace=namespace)

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


@register_training_command("hyp-pytorch-job", "describe")
@click.option(
    "--job-name", required=True, help="Required. The name of the job to describe"
)
@click.option(
    "--namespace",
    "-n",
    default="default",
    help="Optional. The namespace of the job. Defaults to 'default' namespace.",
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "get_pytorchjob_cli")
@handle_cli_exceptions()
def pytorch_describe(job_name: str, namespace: str):
    """Describe a HyperPod PyTorch job."""
    job = sys.modules[__name__].HyperPodPytorchJob.get(name=job_name, namespace=namespace)

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


@register_training_command("hyp-pytorch-job", "delete")
@click.option(
    "--job-name", required=True, help="Required. The name of the job to delete"
)
@click.option(
    "--namespace",
    "-n",
    default="default",
    help="Optional. The namespace of the job. Defaults to 'default' namespace.",
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "delete_pytorchjob_cli")
@handle_cli_exceptions()
def pytorch_delete(job_name: str, namespace: str):
    """Delete a HyperPod PyTorch job."""
    job = sys.modules[__name__].HyperPodPytorchJob.get(name=job_name, namespace=namespace)
    job.delete()


@register_training_command("hyp-pytorch-job", "list-pods")
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
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "list_pods_pytorchjob_cli")
@handle_cli_exceptions()
def pytorch_list_pods(job_name: str, namespace: str):
    """List all HyperPod PyTorch pods related to the job."""
    job = sys.modules[__name__].HyperPodPytorchJob.get(name=job_name, namespace=namespace)
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


@register_training_command("hyp-pytorch-job", "get-logs")
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
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "get_pytorchjob_logs_from_pod_cli")
@handle_cli_exceptions()
def pytorch_get_logs(job_name: str, pod_name: str, namespace: str):
    """Get specific pod log for Hyperpod Pytorch job."""
    click.echo("Listing logs for pod: " + pod_name)
    job = sys.modules[__name__].HyperPodPytorchJob.get(name=job_name, namespace=namespace)
    logs = job.get_logs_from_pod(pod_name=pod_name)

    # Use common log display utility for consistent formatting across all job types
    sys.modules[__name__].display_formatted_logs(logs, title=f"Pod Logs for {pod_name}")


@register_training_command("hyp-pytorch-job", "get-operator-logs")
@click.option(
    "--since-hours",
    type=click.FLOAT,
    required=True,
    help="Required. The time frame to get logs for.",
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "get_pytorch_operator_logs")
@handle_cli_exceptions()
def pytorch_get_operator_logs(since_hours: float):
    """Get operator logs for pytorch training jobs."""
    logs = sys.modules[__name__].HyperPodPytorchJob.get_operator_logs(since_hours=since_hours)
    
    # Use common log display utility for consistent formatting across all job types
    sys.modules[__name__].display_formatted_logs(logs, title="PyTorch Operator Logs")
