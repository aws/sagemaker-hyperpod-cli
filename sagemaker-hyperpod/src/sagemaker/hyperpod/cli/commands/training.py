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
from sagemaker.hyperpod.cli.create_utils import generate_click_command
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

        click.echo("\nJobs:")
        click.echo(jobs)

    except Exception as e:
        raise click.UsageError(f"Failed to list jobs: {str(e)}")


@click.command("hp-pytorch-job")
@click.option('--job-name',  required=True,help='Job name')
@click.option('--namespace', '-n', default='default', help='Namespace')
def pytorch_describe(job_name: str, namespace: str):
    """Describe a HyperPod PyTorch job"""
    try:
        job = HyperPodPytorchJob.get(name=job_name, namespace=namespace)

        if job is None:
            raise click.UsageError(f"Job {job_name} not found in namespace {namespace}")

        # Print job details
        click.echo("\nJob Details:")
        click.echo(job.model_dump)

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


