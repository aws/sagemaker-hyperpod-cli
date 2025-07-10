import click
import logging
import os
import yaml
import shutil
import subprocess
from pathlib import Path
from sagemaker.hyperpod.training.hyperpod_pytorch_job import HyperPodPytorchJob
from sagemaker.hyperpod.common.config import Metadata
import tempfile
from typing import List, Dict, Any, Optional, Callable, get_args, get_origin, Literal
from sagemaker.hyperpod.cli.training_utils import generate_click_command
from importlib.metadata import entry_points
from hyperpod_pytorch_job_template.registry import SCHEMA_REGISTRY


@click.command("hyp-pytorch-job")
@click.option("--version", default="1.0", help="Schema version to use")
@click.option("--debug", default=False, help="Enable debug mode")
@generate_click_command(
    schema_pkg="hyperpod_pytorch_job_template",
    registry=SCHEMA_REGISTRY,
)
def pytorch_create(version, debug, config):
    """Create a PyTorch job"""
    try:
        click.echo(f"Using version: {version}")
        job_name = config.get("name")
        namespace = config.get("namespace")
        spec = config.get("spec")

        # Prepare metadata
        metadata_kwargs = {"name": job_name}
        if namespace:
            metadata_kwargs["namespace"] = namespace

        # Prepare job kwargs
        job_kwargs = {
            "metadata": Metadata(**metadata_kwargs),
            "replica_specs": spec.get("replica_specs"),
        }

        # Add nproc_per_node if present
        if "nproc_per_node" in spec:
            job_kwargs["nproc_per_node"] = spec.get("nproc_per_node")

        # Add run_policy if present
        if "run_policy" in spec:
            job_kwargs["run_policy"] = spec.get("run_policy")

        # Create job
        job = HyperPodPytorchJob(**job_kwargs)
        job.create(debug=debug)

    except Exception as e:
        raise click.UsageError(f"Failed to create job: {str(e)}")


@click.command("hyp-pytorch-job")
@click.option(
    "--namespace",
    "-n",
    default="default",
    help="Optional. The namespace to list jobs from. Defaults to 'default' namespace.",
)
def list_jobs(namespace: str):
    """List all HyperPod PyTorch jobs"""
    try:
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

    except Exception as e:
        raise click.UsageError(f"Failed to list jobs: {str(e)}")


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
def pytorch_describe(job_name: str, namespace: str):
    """Describe a HyperPod PyTorch job"""
    try:
        job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)

        if job is None:
            raise click.UsageError(f"Job {job_name} not found in namespace {namespace}")

        # Print basic info
        click.echo("\nJob Details:")
        click.echo("=" * 80)
        click.echo(f"Name:           {job.metadata.name}")
        click.echo(f"Namespace:      {job.metadata.namespace}")

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

    except Exception as e:
        raise click.UsageError(f"Failed to describe job: {str(e)}")


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
def pytorch_delete(job_name: str, namespace: str):
    """Delete a HyperPod PyTorch job"""
    try:
        job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)
        job.delete()

        if job is None:
            raise click.UsageError(f"Job {job_name} not found in namespace {namespace}")

    except Exception as e:
        raise click.UsageError(f"Failed to describe job: {str(e)}")


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
def pytorch_list_pods(job_name: str, namespace: str):
    """List all HyperPod PyTorch pods corresponding to the job"""
    try:
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

    except Exception as e:
        raise click.UsageError(f"Failed to list jobs: {str(e)}")


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
def pytorch_get_logs(job_name: str, pod_name: str, namespace: str):
    """Get specific logs from pod corresponding to the job"""
    try:
        click.echo("Listing logs for pod: " + pod_name)
        job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)
        logs = job.get_logs_from_pod(pod_name=pod_name)

        if not logs:
            click.echo("No logs available.")
            return

        # Split logs into lines and display them
        log_lines = logs.split("\n")
        for line in log_lines:
            if line.strip():  # Skip empty lines
                # Color coding based on log level
                if "ERROR" in line.upper():
                    click.secho(line, fg="red")
                elif "WARNING" in line.upper():
                    click.secho(line, fg="yellow")
                elif "INFO" in line.upper():
                    click.secho(line, fg="green")
                else:
                    click.echo(line)

        click.echo("\nEnd of logs")
        click.echo("=" * 80)

    except Exception as e:
        raise click.UsageError(f"Failed to list jobs: {str(e)}")
