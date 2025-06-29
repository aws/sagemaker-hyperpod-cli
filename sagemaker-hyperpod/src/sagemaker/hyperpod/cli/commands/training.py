import click
import logging
import os
import yaml
import shutil
import subprocess
from pathlib import Path
from sagemaker.hyperpod.training.hyperpod_pytorch_job import HyperPodPytorchJob
from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_config import (
    Container,
    _HyperPodPytorchJob,
    ReplicaSpec,
    Spec,
    Template,
)
import tempfile
from sagemaker.hyperpod.cli.constants.hp_pytorch_command_constants import HELP_TEXT
from ruamel.yaml import YAML
from typing import List, Dict, Any, Optional, Callable, get_args, get_origin, Literal
from sagemaker.hyperpod.cli.training_utils import generate_click_command
from importlib.metadata import entry_points
from hyperpod_pytorchjob_config_schemas.registry import SCHEMA_REGISTRY




@click.command("hp-pytorch-job")
@click.option("--version", default="1.0", help="Schema version to use")
@generate_click_command(schema_pkg="hyperpod_pytorchjob_config_schemas", registry=SCHEMA_REGISTRY,)
def pytorch_create(version, config):
    """Submit a PyTorch job using a configuration file"""
    try:
        click.echo(f"Using version: {version}")
        job_name = config.get('name')
        namespace = config.get("namespace")
        spec = config.get("spec")
        # Create job with or without namespace
        if namespace is None:
            job = HyperPodPytorchJob(
                name=job_name,
                spec=spec
            )
        else:
            job = HyperPodPytorchJob(
                name=job_name,
                namespace=namespace,
                spec=spec
            )

        job.create()


    except Exception as e:
        raise click.UsageError(f"Failed to create job: {str(e)}")


@click.command("hp-pytorch-job")
@click.option('--namespace', '-n', default='default', help='Namespace')
def list_jobs(namespace: str):
    """List all HyperPod PyTorch jobs"""
    try:
        jobs = HyperPodPytorchJob.list(namespace=namespace)

        if not jobs:
            click.echo("No jobs found.")
            return

        # Define headers and widths
        headers = ['NAME', 'NAMESPACE', 'STATUS', 'AGE']
        widths = [30, 20, 15, 15]

        # Print header
        header = ''.join(f"{h:<{w}}" for h, w in zip(headers, widths))
        click.echo("\n" + header)
        click.echo("-" * sum(widths))

        # Print each job
        for job in jobs:
            # Get status from conditions
            status = "Unknown"
            if job.status and job.status.conditions:
                for condition in reversed(job.status.conditions):
                    if condition.status == "True":
                        status = condition.type
                        break

                # Calculate age
                age = "N/A"
                if job.status and job.status.conditions:
                    # Find the 'Created' condition to get the start time
                    created_condition = next((c for c in job.status.conditions if c.type == 'Created'), None)
                    if created_condition and created_condition.lastTransitionTime:
                        from datetime import datetime, timezone
                        start_time = datetime.fromisoformat(created_condition.lastTransitionTime.replace('Z', '+00:00'))
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
                row = ''.join([
                    f"{job.name:<{widths[0]}}",
                    f"{job.namespace:<{widths[1]}}",
                    f"{status:<{widths[2]}}",
                    f"{age:<{widths[3]}}"
                ])
                click.echo(row)

            click.echo()  # Add empty line at the end

    except Exception as e:
        raise click.UsageError(f"Failed to list jobs: {str(e)}")


@click.command("hp-pytorch-job")
@click.option('--job-name', required=True, help='Job name')
@click.option('--namespace', '-n', default='default', help='Namespace')
def pytorch_describe(job_name: str, namespace: str):
    """Describe a HyperPod PyTorch job"""
    try:
        job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)

        if job is None:
            raise click.UsageError(f"Job {job_name} not found in namespace {namespace}")

        # Print basic info
        click.echo("\nJob Details:")
        click.echo("=" * 80)
        click.echo(f"Name:           {job.name}")
        click.echo(f"Namespace:      {job.namespace}")
        click.echo(f"API Version:    {job.apiVersion}")
        click.echo(f"Kind:           {job.kind}")

        # Print Spec details
        click.echo("\nSpec:")
        click.echo("-" * 80)
        click.echo(f"Processes per Node: {job.spec.nprocPerNode}")

        # Print Replica Specs
        for replica in job.spec.replicaSpecs:
            click.echo(f"\nReplica Spec:")
            click.echo(f"  Name:     {replica.name}")
            click.echo(f"  Replicas: {replica.replicas}")
            click.echo(f"  Spares:   {replica.spares}")

            # Container details
            for container in replica.template.spec.containers:
                click.echo("\n  Container:")
                click.echo(f"    Name:            {container.name}")
                click.echo(f"    Image:           {container.image}")
                click.echo(f"    Image Pull Policy: {container.imagePullPolicy}")
                if container.resources:
                    click.echo("    Resources:")
                    if container.resources.limits:
                        click.echo(f"      Limits:   {container.resources.limits}")
                    if container.resources.requests:
                        click.echo(f"      Requests: {container.resources.requests}")

        # Print Run Policy
        click.echo("\nRun Policy:")
        click.echo("-" * 80)
        click.echo(f"Clean Pod Policy:          {job.spec.runPolicy.cleanPodPolicy}")
        click.echo(f"TTL Seconds After Finished: {job.spec.runPolicy.ttlSecondsAfterFinished}")

        # Print Status
        click.echo("\nStatus:")
        click.echo("-" * 80)
        if job.status:
            if job.status.conditions:
                click.echo("Conditions:")
                for condition in job.status.conditions:
                    click.echo(f"  Type:               {condition.type}")
                    click.echo(f"  Status:             {condition.status}")
                    click.echo(f"  Last Transition:    {condition.lastTransitionTime}")
                    if condition.message:
                        click.echo(f"  Message:            {condition.message}")
                    click.echo()


    except Exception as e:
        raise click.UsageError(f"Failed to describe job: {str(e)}")

@click.command("hp-pytorch-job")
@click.option('--job-name',  required=True,help='Job name')
@click.option('--namespace', '-n', default='default', help='Namespace')
def pytorch_delete(job_name: str, namespace: str):
    """Describe a HyperPod PyTorch job"""
    try:
        job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)
        job.delete()

        if job is None:
            raise click.UsageError(f"Job {job_name} not found in namespace {namespace}")


    except Exception as e:
        raise click.UsageError(f"Failed to describe job: {str(e)}")


@click.command("hp-pytorch-job")
@click.option('--job-name', required=True, help='Job name')
@click.option('--namespace', '-n', default='default', help='Namespace')
def pytorch_list_pods(job_name: str, namespace: str):
    """List all HyperPod PyTorch pods corresponding to the job"""
    try:
        job = HyperPodPytorchJob.get(job_name=job_name, namespace=namespace)
        job.list_pods()
        click.echo("Listing pods for job: " + job_name)

        # if not jobs:
        #     click.echo("No jobs found.")
        #     return
        #
        # click.echo("\nJobs:")
        # click.echo(jobs)

    except Exception as e:
        raise click.UsageError(f"Failed to list jobs: {str(e)}")

@click.command("hp-pytorch-job")
@click.option('--pod-name', required=True, help='Job name')
@click.option('--namespace', '-n', default='default', help='Namespace')
def pytorch_get_logs(pod_name: str,namespace: str):
    """List all HyperPod PyTorch pods corresponding to the job"""
    try:
        #jobs = HyperPodPytorchJob.list(namespace=namespace)
        click.echo("Listing logs for pod: " + pod_name)

        # if not jobs:
        #     click.echo("No jobs found.")
        #     return
        #
        # click.echo("\nJobs:")
        # click.echo(jobs)

    except Exception as e:
        raise click.UsageError(f"Failed to list jobs: {str(e)}")