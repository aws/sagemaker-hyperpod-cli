import click
import json
import yaml
from tabulate import tabulate
from sagemaker.hyperpod.space.hyperpod_space_template import HPSpaceTemplate


@click.command("hyp-space-template")
@click.option("--file", "-f", required=True, help="YAML file containing the configuration")
def space_template_create(file):
    """Create a space-template resource."""
    template = HPSpaceTemplate(file_path=file)
    template.create()
    click.echo(f"Space template '{template.name}' in namespace '{template.namespace}' created successfully")


@click.command("hyp-space-template")
@click.option("--namespace", "-n", required=False, default=None, help="Kubernetes namespace")
@click.option("--output", "-o", type=click.Choice(["table", "json"]), default="table")
def space_template_list(namespace, output):
    """List space-template resources."""
    templates = HPSpaceTemplate.list(namespace)
    
    if output == "json":
        templates_data = [template.to_dict() for template in templates]
        click.echo(json.dumps(templates_data, indent=2))
    else:
        if templates:
            table_data = []
            for template in templates:
                table_data.append([
                    template.namespace,
                    template.name,
                    template.config_data.get("spec", {}).get("displayName", ""),
                    template.config_data.get("spec", {}).get("defaultImage", ""),
                ])
            click.echo(tabulate(table_data, headers=["NAMESPACE", "NAME", "DISPLAY_NAME", "DEFAULT_IMAGE"]))
        else:
            click.echo("No space templates found")


@click.command("hyp-space-template")
@click.option("--name", required=True, help="Name of the space template")
@click.option("--namespace", "-n", required=False, default=None, help="Kubernetes namespace")
@click.option("--output", "-o", type=click.Choice(["yaml", "json"]), default="yaml")
def space_template_describe(name, namespace, output):
    """Describe a space-template resource."""
    template = HPSpaceTemplate.get(name, namespace)
    
    if output == "json":
        click.echo(json.dumps(template.to_dict(), indent=2))
    else:
        click.echo(template.to_yaml())


@click.command("hyp-space-template")
@click.option("--name", required=True, help="Name of the space template")
@click.option("--namespace", "-n", required=False, default=None, help="Kubernetes namespace")
def space_template_delete(name, namespace):
    """Delete a space-template resource."""
    template = HPSpaceTemplate.get(name, namespace)
    template.delete()
    click.echo(f"Requested deletion for Space template '{name}' in namespace '{namespace}'")


@click.command("hyp-space-template")
@click.option("--name", required=True, help="Name of the space template")
@click.option("--namespace", "-n", required=False, default=None, help="Kubernetes namespace")
@click.option("--file", "-f", required=True, help="YAML file containing the updated template")
def space_template_update(name, namespace, file):
    """Update a space-template resource."""
    template = HPSpaceTemplate.get(name, namespace)
    template.update(file)
    click.echo(f"Space template '{name}' in namespace '{namespace}' updated successfully")
