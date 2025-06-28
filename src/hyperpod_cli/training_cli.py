import click
import yaml
import json
import os
import subprocess
from pydantic import BaseModel, ValidationError, Field
from typing import Optional
from hyperpod_cli.commands.training.commands import hp_pytorch_job
from hyperpod_cli.constants.hp_pytorch_command_constants import HELP_TEXT


class HPPyTorchCommandGroup(click.Group):
    def format_help(self, ctx, formatter):
        click.echo(HELP_TEXT)

class CLICreateCommand(click.Group):
    def format_help(self, ctx, formatter):
        click.echo(HELP_TEXT)

@click.group()
def cli():
    pass

@cli.group(cls=CLICreateCommand)
def create():
    """HyperPod PyTorch commands"""
    pass

create.add_command(hp_pytorch_job)




if __name__ == '__main__':
    cli()