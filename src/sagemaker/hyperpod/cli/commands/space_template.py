import click
import json
import yaml
from tabulate import tabulate
from sagemaker.hyperpod.space.hyperpod_space_template import HPSpaceTemplate


@click.command("hyp-space-template")
@click.option("--file", "-f", required=True, help="YAML file containing the configuration")
def space_template_create(file):
    """Create a space-template resource."""
    try:
        template = HPSpaceTemplate(file_path=file)
        template.create()
        click.echo(f"Space template '{template.name}' created successfully")
    except Exception as e:
        click.echo(f"Error creating space template: {e}", err=True)


@click.command("hyp-space-template")
@click.option("--output", "-o", type=click.Choice(["table", "json"]), default="table")
def space_template_list(output):
    """List space-template resources."""
    try:
        templates = HPSpaceTemplate.list()
        
        if output == "json":
            templates_data = [template.to_dict() for template in templates]
            click.echo(json.dumps(templates_data, indent=2))
        else:
            if templates:
                table_data = []
                for template in templates:
                    table_data.append([
                        template.name,
                        template.config_data.get("spec", {}).get("displayName", ""),
                        template.config_data.get("spec", {}).get("defaultImage", ""),
                    ])
                click.echo(tabulate(table_data, headers=["NAME", "DISPLAY_NAME", "DEFAULT_IMAGE"]))
            else:
                click.echo("No space templates found")
    except Exception as e:
        click.echo(f"Error listing space templates: {e}", err=True)


@click.command("hyp-space-template")
@click.option("--name", required=True, help="Name of the space template")
@click.option("--output", "-o", type=click.Choice(["yaml", "json"]), default="yaml")
def space_template_describe(name, output):
    """Describe a space-template resource."""
    try:
        template = HPSpaceTemplate.get(name)
        
        if output == "json":
            click.echo(json.dumps(template.to_dict(), indent=2))
        else:
            click.echo(template.to_yaml())
    except Exception as e:
        click.echo(f"Error describing space template '{name}': {e}", err=True)


@click.command("hyp-space-template")
@click.option("--name", required=True, help="Name of the space template")
def space_template_delete(name):
    """Delete a space-template resource."""
    try:
        template = HPSpaceTemplate.get(name)
        template.delete()
        click.echo(f"Space template '{name}' deleted successfully")
    except Exception as e:
        click.echo(f"Error deleting space template '{name}': {e}", err=True)


@click.command("hyp-space-template")
@click.option("--name", required=True, help="Name of the space template")
@click.option("--file", "-f", required=True, help="YAML file containing the updated template")
def space_template_update(name, file):
    """Update a space-template resource."""
    try:
        template = HPSpaceTemplate.get(name)
        template.update(file)
        click.echo(f"Space template '{name}' updated successfully")
    except Exception as e:
        click.echo(f"Error updating space template '{name}': {e}", err=True)
