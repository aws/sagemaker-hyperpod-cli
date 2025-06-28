import click
import logging
import os
import yaml
import shutil
import subprocess
from pathlib import Path
from sagemaker.hyperpod.training.hyperpod_pytorch_job import HyperpodPytorchJob
from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_config import (
    Container,
    HyperPodPytorchJobSpec,
    ReplicaSpec,
    Spec,
    Template,
)
import tempfile
from hyperpod_cli.constants.hp_pytorch_command_constants import HELP_TEXT, WELCOME_MESSAGE, USAGE_GUIDE_TEXT, DEFAULT_CONFIG_DIR,DEFAULT_BASE_DIR
from ruamel.yaml import YAML
import datetime
from tabulate import tabulate
from typing import List, Dict, Any, Optional, Callable, get_args, get_origin, Literal
#from datetime import datetime
from hyperpod_cli.training_utils import validate_config
#from hyperpod_cli.commands.training.generate_click_commands import generate_click_commands
from importlib.metadata import entry_points
from config_schemas.registry import SCHEMA_REGISTRY
from functools import wraps


def generate_click_commands(version: str = None) -> Callable:

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Get version from kwargs (provided by click.option)
            version = kwargs.get('version', "1.0")

            # Get the model class for the version
            Model = SCHEMA_REGISTRY.get(version)
            if not Model:
                raise click.ClickException(f"Unsupported schema version: {version}")

            # Convert kebab-case to snake_case in kwargs
            snake_kwargs = {k.replace('-', '_'): v for k, v in kwargs.items()}

            try:
                # Create and validate model instance
                config = Model(**snake_kwargs)
                return f(config=config, **kwargs)
            except Exception as e:
                raise click.ClickException(str(e))

        # Generate click options from model fields
        # Using default version for initial option generation
        default_version = "1.0"
        Model = SCHEMA_REGISTRY.get(version or default_version)
        if not Model:
            raise click.ClickException(f"Unsupported schema version: {default_version}")

        for field_name, field in Model.__fields__.items():
            if field_name == "version":
                continue
            # Determine click option type
            field_type = field.outer_type_
            if get_origin(field_type) is Literal:
                click_type = click.Choice(get_args(field_type))
            elif field_type == int:
                click_type = int
            elif field_type == float:
                click_type = float
            elif field_type == bool:
                click_type = bool
            else:
                click_type = str

            # Create click option
            option = click.option(
                f"--{field_name.replace('_', '-')}",  # Convert snake_case to kebab-case
                required=field.required,
                type=click_type,
                default=field.default if not field.required else None,
                help=field.field_info.description,
                show_default=field.default is not None
            )
            wrapped = option(wrapped)

        return wrapped

    return decorator

@click.command()
@click.option("--version", default="1.0", help="Schema version to use")
@generate_click_commands()
def hp_pytorch_job(version, config):
    """Submit a PyTorch job using a configuration file"""

    click.echo(f"Using version: {version}")
    click.echo(f"Validated config: {config.job_name}")
    try:
        config_data = {
            "job_name": config.job_name,
            "image": config.image,
            "node_count": config.node_count
        }
        # Get the handler for version 1.0.0
        handlers = entry_points(group="mycli.config_versions")
        handler = None
        for ep in handlers:
            if ep.name == version:
                handler = ep.load()
                break

        if not handler:
            raise ValueError("No compatible schema handler found")

        try:
            validated_config = handler.validate(config_data)

            # Success message with green checkmark
            click.echo(click.style("✓ Configuration validated successfully!", fg='green'))
            click.echo("\nJob Details:")
            click.echo(f"  Name: {config.job_name}")
            click.echo(f"  Image: {config.image}")
            click.echo(f"  Node Count: {config.node_count}")

            # Here submit the job
            # job = HyperpodPytorchJob.create(name=job_name, image=image, node_count=node_count)



        except ValueError as e:
            click.echo(click.style("Error: Invalid configuration", fg='red'))
            click.echo(f"Details: {str(e)}")
            raise click.Abort()
        except Exception as e:
            click.echo(click.style("Error: Validation failed", fg='red'))
            click.echo(f"Details: {str(e)}")

        click.echo(f"Creating job with name: {job_name}, image: {image}, node count: {node_count}")

        #job = HyperpodPytorchJob.create(name=job_name, image=image, node_count=node_count)
    except:
        raise click.UsageError("Failed to create job. Please check your parameters.")

