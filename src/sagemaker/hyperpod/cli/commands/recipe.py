import json
import os
import yaml
import click
import re
from pathlib import Path
from typing import Optional, Dict, Any

from hyperpod_pytorch_job_template.v1_0 import PyTorchJobConfig
from omegaconf import OmegaConf

# from sagemaker.hyperpod.cli.recipe_utils.pytorch_schema import PytorchJobSchema
from sagemaker.hyperpod.cli.recipe_utils.recipe_finder import load_recipes, get_unique_values, filter_recipes, \
    print_recipe_table
from sagemaker.hyperpod.cli.recipe_utils.recipe_loader import load_recipe


def replace_hydra_placeholders(config: Dict[str, Any], base_config: Dict[str, Any]) -> Dict[str, Any]:
    """Replace Hydra interpolation placeholders in the config."""

    def _replace_in_value(value, config_dict):
        if isinstance(value, str):
            # Replace ${recipes.X.Y.Z} with the actual value from config_dict
            pattern = r'\$\{recipes\.(\w+(?:\.\w+)*)\}'
            matches = re.findall(pattern, value)

            for match in matches:
                keys = match.split('.')
                replacement = config_dict
                try:
                    for key in keys:
                        replacement = replacement[key]

                    # Replace the placeholder with the actual value
                    value = value.replace(f"${{recipes.{match}}}", str(replacement))
                except (KeyError, TypeError):
                    # Keep the placeholder if the key doesn't exist
                    pass

            # Replace ${base_results_dir} with the value from base_config
            if "${base_results_dir}" in value:
                base_results_dir = base_config.get("base_results_dir", "./results")
                value = value.replace("${base_results_dir}", str(base_results_dir))

        return value

    def _process_dict(d, config_dict):
        result = {}
        for k, v in d.items():
            if isinstance(v, dict):
                result[k] = _process_dict(v, config_dict)
            elif isinstance(v, list):
                result[k] = [_replace_in_value(item, config_dict) if not isinstance(item, dict) else _process_dict(item,
                                                                                                                   config_dict)
                             for item in v]
            else:
                result[k] = _replace_in_value(v, config_dict)
        return result

    return _process_dict(config, config)


def transform_config(original_config):
    # Create the new configuration structure
    new_config = {
        "job_name": None,
        "image": "pytorch/pytorch:latest",  # default value
        "command": None,
        # "environment": json.dumps(original_config['base_config']['env_vars']),
        "environment": original_config['base_config']['env_vars'],
        "pull_policy": original_config['k8s_config']['pullPolicy'],
        "instance_type": original_config['base_config']['instance_type'],
        "tasks_per_node": None,
        "label_selector": original_config['k8s_config']['label_selector'],
        "deep_health_check_passed_nodes_only": None,
        "scheduler_type": "kueue",
        "queue_name": None,
        "priority": None,
        "max_retry": None,
        # Below input's init experience in progress.
        # "volumes": original_config['k8s_config']['volumes'],
        # "persistent_volume_claims": original_config['k8s_config']['persistent_volume_claims']
    }
    return new_config


@click.command()
@click.argument("directory", type=click.Path(file_okay=False), default=".")
@click.option('--from-recipe', required=True, help='Recipe path relative to recipes_collection')
def recipe_init(directory: str, from_recipe: str):
    """Initialize a directory with config yaml based on a recipe."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)

        # Get base paths
        base_dir = Path(__file__).parent.parent / "sagemaker_hyperpod_recipes" / "recipes_collection"
        print(f"base_dir:{base_dir}")
        recipes_dir = base_dir

        # Load base config files
        config_path = recipes_dir / "config.yaml"
        k8s_path = recipes_dir / "cluster" / "k8s.yaml"
        print(f"K8sPath: {k8s_path}")

        # Determine recipe path
        recipe_path = recipes_dir / "recipes" / from_recipe
        if not recipe_path.exists():
            raise FileNotFoundError(f"Recipe not found: {recipe_path}")

        # Load YAML files
        with open(config_path, 'r') as f:
            base_config = yaml.safe_load(f)

        with open(k8s_path, 'r') as f:
            k8s_config = yaml.safe_load(f)

        with open(recipe_path, 'r') as f:
            recipe_config = yaml.safe_load(f)

        # Update base config
        base_config['cluster_type'] = 'k8s'
        base_config['defaults'][1] = {'cluster': 'k8s'}
        base_config['defaults'][2] = {'recipes': from_recipe}
        base_config['training_config'] = from_recipe

        # Replace Hydra placeholders in recipe config
        recipe_config = replace_hydra_placeholders(recipe_config, base_config)

        # Create combined config
        combined_config = {
            'base_config': base_config,
            'k8s_config': k8s_config,
        }
        combined_config_old = {
            **base_config,
            'cluster': k8s_config,
            'recipes': recipe_config
        }
        # temporary config, to-be-removed post-development
        output_path = Path(directory) / "config_old.yaml"
        with open(output_path, 'w') as f:
            yaml.dump(combined_config_old, f, default_flow_style=False)

        # Write combined config to file
        trans_config = transform_config(combined_config)
        output_path = Path(directory) / "config.yaml"
        with open(output_path, 'w') as f:
            yaml.dump(trans_config, f, default_flow_style=False)

        output_path = Path(directory) / "recipe.yaml"
        conf = OmegaConf.create(recipe_config)
        conf = OmegaConf.to_container(conf, resolve=True)
        with open(output_path, 'w') as f:
            yaml.dump(conf, f, default_flow_style=False)
        click.echo(f"Successfully initialized configs : recipe.yaml and config.yaml")

    except Exception as e:
        click.echo(f"Error initializing config: {str(e)}", err=True)
        raise


@click.command()
@click.argument('overrides', nargs=-1, required=True)
@click.option('--config-file', default='recipe.yaml', help='Path to config file to modify')
def recipe_configure(overrides, config_file):
    """Configure recipe parameters with overrides in format key=value."""
    from hyperpod_cli.sagemaker_hyperpod_recipes.recipe_schema import RecipeSchema

    try:
        # Load existing config
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        # Apply overrides
        for param in overrides:
            if '=' not in param:
                click.echo(f"Invalid override format: {param}. Use key=value format.", err=True)
                continue

            key, value = param.split('=', 1)
            keys = key.split('.')

            # Validate key exists in schema
            if not _validate_schema_key(keys):
                click.echo(f"Warning: {key} is not defined in RecipeSchema", err=True)
                return

            # Navigate to the nested key
            current = config
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]

            # Convert value to appropriate type
            try:
                if value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif '.' in value and value.replace('.', '').isdigit():
                    value = float(value)
                elif value.lower() == 'null':
                    value = None
            except:
                pass  # Keep as string if conversion fails

            current[keys[-1]] = value
            click.echo(f"Set {key} = {value}")

        # Validate final config against schema
        try:
            RecipeSchema(**config)
            click.echo("✅ Configuration validated against schema")
        except Exception as e:
            click.echo(f"⚠️  Schema validation warning: {e}")

        # Write updated config
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        click.echo(f"Configuration updated in {config_file}")

    except FileNotFoundError:
        click.echo(f"Config file not found: {config_file}", err=True)
    except Exception as e:
        click.echo(f"Error configuring: {str(e)}", err=True)


def _validate_schema_key(keys):
    """Validate if key path exists in RecipeSchema."""
    from hyperpod_cli.sagemaker_hyperpod_recipes.recipe_schema import RecipeSchema

    current_model = RecipeSchema
    for key in keys:
        if hasattr(current_model, '__fields__') and key in current_model.__fields__:
            field_info = current_model.__fields__[key]
            # Handle different Pydantic versions
            field_type = getattr(field_info, 'type_', getattr(field_info, 'annotation', None))
            
            # Handle Optional types
            if hasattr(field_type, '__origin__'):
                field_type = field_type.__args__[0]
            
            # If it's a nested model, continue validation
            if hasattr(field_type, '__fields__'):
                current_model = field_type
            else:
                return True
        else:
            return False
    return True


@click.command()
def recipe_validate():
    click.echo("Validating recipe.yaml")
    recipe_path = "recipe.yaml"
    try:
        recipe = load_recipe(str(recipe_path))
        print(f"✅ Successfully validated recipe: {recipe_path}")
    except Exception as e:
        print(f"❌ Failed to validate recipe {recipe_path}: {e}")

    click.echo("Validating config.yaml")
    config_path = "config.yaml"
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        config = PyTorchJobConfig(**config_data)
        print(f"✅ Successfully validated config: {config_path}")
    except Exception as e:
        print(f"❌ Failed to validate config {config_path}: {e}")

import subprocess
import os
from sagemaker.hyperpod.cli.utils import setup_logger

logger = setup_logger(__name__)
@click.command()
def recipe_submit():
    main_func_path = Path(__file__).parent.parent / "sagemaker_hyperpod_recipes" / "main.py"
    cmd = [
        'python',
        str(main_func_path),
        'config_old.yaml'
    ]
    print(f"cmd:{cmd}")
    subprocess.run(cmd, check=True)



@click.command()
@click.option("--source", help="Filter by source (e.g., 'Hugging Face', 'Megatron')")
@click.option("--model", help="Filter by model (e.g., 'Llama 3', 'Mistral')")
@click.option("--size", help="Filter by model size (e.g., '7b', '70b')")
@click.option("--min-seq-length", type=int, help="Minimum sequence length")
@click.option("--max-seq-length", type=int, help="Maximum sequence length")
@click.option("--min-nodes", type=int, help="Minimum number of nodes")
@click.option("--max-nodes", type=int, help="Maximum number of nodes")
@click.option("--instance", help="Filter by instance type (e.g., 'ml.p5.48xlarge')")
@click.option("--accelerator", help="Filter by accelerator (e.g., 'GPU H100', 'TRN')")
@click.option("--task", help="Filter by task (pre-training, fine-tuning, evaluation)")
@click.option("--method", help="Filter by fine-tuning method (e.g., 'LoRA', 'Full')")
@click.option("--json", is_flag=True, help="Output in JSON format")
@click.option("--list-values", help="List all unique values for a specific attribute")
@click.option("--count", is_flag=True, help="Show only the count of matching recipes")
def find_recipe(**kwargs):
    """Find HyperPod recipes based on criteria."""
    recipes = load_recipes()

    # If list-values is specified, print unique values and exit
    if kwargs.get("list_values"):
        attr = kwargs["list_values"]
        values = get_unique_values(recipes, attr)
        click.echo(f"Available {attr} values:")
        for value in values:
            click.echo(f"  - {value}")
        return

    # Filter recipes based on provided arguments
    filtered_recipes = filter_recipes(
        recipes,
        source=kwargs.get("source"),
        model=kwargs.get("model"),
        size=kwargs.get("size"),
        min_seq_length=kwargs.get("min_seq_length"),
        max_seq_length=kwargs.get("max_seq_length"),
        min_nodes=kwargs.get("min_nodes"),
        max_nodes=kwargs.get("max_nodes"),
        instance=kwargs.get("instance"),
        accelerator=kwargs.get("accelerator"),
        task=kwargs.get("task"),
        method=kwargs.get("method")
    )

    # Output results
    if kwargs.get("count"):
        click.echo(f"Found {len(filtered_recipes)} recipes matching your criteria.")
    elif kwargs.get("json"):
        result = []
        for recipe in filtered_recipes:
            r = {attr: getattr(recipe, attr) for attr in dir(recipe)
                 if not attr.startswith('_') and not callable(getattr(recipe, attr))}
            result.append(r)
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        print_recipe_table(filtered_recipes)
        click.echo(f"\nFound {len(filtered_recipes)} recipes matching your criteria.")


if __name__ == '__main__':
    init()