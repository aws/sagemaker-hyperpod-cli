import click
import json
import yaml
from tabulate import tabulate
from sagemaker.hyperpod.space.hyperpod_space_template import HPSpaceTemplate
from sagemaker.hyperpod.common.cli_decorators import handle_cli_exceptions
from sagemaker.hyperpod.cli.clients.kubernetes_client import KubernetesClient


@click.command("hyp-space-template")
@click.option("--file", "-f", required=True, help="YAML file containing the configuration")
@handle_cli_exceptions()
def space_template_create(file):
    """Create a space-template resource."""
    template = HPSpaceTemplate(file_path=file)
    template.create()
    click.echo(f"Space template '{template.name}' in namespace '{template.namespace}' created successfully")


@click.command("hyp-space-template")
@click.option("--namespace", "-n", required=False, default=None, help="Kubernetes namespace")
@click.option("--all-namespaces", "-A", is_flag=True, help="List space templates across all namespaces")
@click.option("--output", "-o", type=click.Choice(["table", "json"]), default="table")
@handle_cli_exceptions()
def space_template_list(namespace, all_namespaces, output):
    """List space-template resources."""
    templates = []

    if all_namespaces:
        k8s_client = KubernetesClient()
        namespaces = k8s_client.list_namespaces()

        for ns in namespaces:
            try:
                ns_templates = HPSpaceTemplate.list(ns)
                templates.extend(ns_templates)
            except Exception as e:
                click.echo(f"Warning: Failed to list space templates in namespace '{ns}': {e}", err=True)
                continue
    else:
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
@handle_cli_exceptions()
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
@handle_cli_exceptions()
def space_template_delete(name, namespace):
    """Delete a space-template resource."""
    template = HPSpaceTemplate.get(name, namespace)
    template.delete()
    click.echo(f"Requested deletion for Space template '{name}' in namespace '{namespace}'")


@click.command("hyp-space-template")
@click.option("--name", required=True, help="Name of the space template")
@click.option("--namespace", "-n", required=False, default=None, help="Kubernetes namespace")
@click.option("--file", "-f", required=True, help="YAML file containing the updated template")
@handle_cli_exceptions()
def space_template_update(name, namespace, file):
    """Update a space-template resource."""
    template = HPSpaceTemplate.get(name, namespace)
    template.update(file)
    click.echo(f"Space template '{name}' in namespace '{namespace}' updated successfully")
