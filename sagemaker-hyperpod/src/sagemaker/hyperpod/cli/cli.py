import click
import yaml
import json
import os
import subprocess
from pydantic import BaseModel, ValidationError, Field
from typing import Optional
from sagemaker.hyperpod.cli.commands.training import pytorch_create, list_jobs, pytorch_describe
from sagemaker.hyperpod.cli.constants.hp_pytorch_command_constants import HELP_TEXT



@click.group()
def cli():
    pass

class CLICommand(click.Group):
    def format_help(self, ctx, formatter):
        click.echo(HELP_TEXT)

@cli.group(cls=CLICommand)
def create():
    """HyperPod PyTorch commands"""
    pass

@cli.group(cls=CLICommand)
def list():
    """HyperPod PyTorch commands"""
    pass

@cli.group(cls=CLICommand)
def describe():
    """HyperPod PyTorch commands"""
    pass

create.add_command(pytorch_create)
list.add_command(list_jobs)
describe.add_command(pytorch_describe)


if __name__ == '__main__':
    cli()