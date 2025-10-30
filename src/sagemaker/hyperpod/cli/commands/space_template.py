import click
import json
import yaml
from tabulate import tabulate
from sagemaker.hyperpod.cli.clients.kubernetes_client import KubernetesClient


@click.command("hyp-space-template")
@click.option("--file", "-f", required=True, help="YAML file containing the configuration")
def space_template_create(file):
    """Create a space-template resource."""
    k8s_client = KubernetesClient()
    
    try:
        with open(file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        k8s_client.create_space_template(config_data)
        click.echo(f"Space template '{config_data['metadata']['name']}' created successfully")
    except FileNotFoundError:
        click.echo(f"Error: File '{file}' not found", err=True)
    except yaml.YAMLError as e:
        click.echo(f"Error parsing YAML file: {e}", err=True)
    except Exception as e:
        click.echo(f"Error creating space template: {e}", err=True)


@click.command("hyp-space-template")
@click.option("--output", "-o", type=click.Choice(["table", "json"]), default="table")
def space_template_list(output):
    """List space-template resources."""
    k8s_client = KubernetesClient()
    
    try:
        resources = k8s_client.list_space_templates()
        
        if output == "json":
            click.echo(json.dumps(resources, indent=2))
        else:
            items = resources.get("items", [])
            if items:
                table_data = []
                for item in items:
                    table_data.append([
                        item["metadata"]["name"],
                    ])
                click.echo(tabulate(table_data, headers=["NAME"]))
            else:
                click.echo("No space templates found")
    except Exception as e:
        click.echo(f"Error listing space templates: {e}", err=True)


@click.command("hyp-space-template")
@click.option("--name", required=False, help="Name of the space template")
@click.option("--output", "-o", type=click.Choice(["yaml", "json"]), default="yaml")
def space_template_describe(name, output):
    """Describe a space-template resource."""
    k8s_client = KubernetesClient()
    
    try:
        resource = k8s_client.get_space_template(name)
        resource["metadata"].pop('managedFields', None)
        
        if output == "json":
            click.echo(json.dumps(resource, indent=2))
        else:
            click.echo(yaml.dump(resource, default_flow_style=False))
    except Exception as e:
        click.echo(f"Error describing space template '{name}': {e}", err=True)


@click.command("hyp-space-template")
@click.option("--name", required=False, help="Name of the space template")
def space_template_delete(name):
    """Delete a space-template resource."""
    k8s_client = KubernetesClient()
    
    try:
        k8s_client.delete_space_template(name)
        click.echo(f"Space template '{name}' deleted successfully")
    except Exception as e:
        click.echo(f"Error deleting space template '{name}': {e}", err=True)


@click.command("hyp-space-template")
@click.option("--name", required=True, help="Name of the space template")
@click.option("--file", "-f", required=True, help="YAML file containing the updated template")
def space_template_update(name, file):
    """Update a space-template resource."""
    k8s_client = KubernetesClient()
    
    try:
        with open(file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Validate that the name matches
        yaml_name = config_data.get('metadata', {}).get('name')
        if yaml_name and yaml_name != name:
            click.echo(f"Error: Name mismatch. CLI parameter '{name}' does not match YAML name '{yaml_name}'", err=True)
            return

        # Remove immutable fields from the update
        if 'metadata' in config_data:
            config_data['metadata'].pop('resourceVersion', None)
            config_data['metadata'].pop('uid', None)
            config_data['metadata'].pop('creationTimestamp', None)
            config_data['metadata'].pop('managedFields', None)
        
        k8s_client.patch_space_template(name, config_data)
        click.echo(f"Space template '{name}' updated successfully")
    except FileNotFoundError:
        click.echo(f"Error: File '{file}' not found", err=True)
    except yaml.YAMLError as e:
        click.echo(f"Error parsing YAML file: {e}", err=True)
    except Exception as e:
        click.echo(f"Error updating space template '{name}': {e}", err=True)
