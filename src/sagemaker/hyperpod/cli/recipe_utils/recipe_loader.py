import os
import yaml
from hyperpod_pytorch_job_template.v1_0.recipes.hf.model import HfRecipeSchema
from hyperpod_pytorch_job_template.v1_0.recipes.neuron_hf.model import (
    NeuronHfRecipeSchema,
)
from hyperpod_pytorch_job_template.v1_0.recipes.nova.model import NovaRecipeSchema
from hyperpod_pytorch_job_template.v1_0.recipes.nova_evaluation.model import (
    NovaEvaluationRecipeSchema,
)


def load_recipe(
    recipe_path: str,
) -> (
    HfRecipeSchema
    | NeuronHfRecipeSchema
    | NovaRecipeSchema
    | NovaEvaluationRecipeSchema
):
    """
    Load and validate a recipe YAML file using the RecipeSchema.

    Args:
        recipe_path: Path to the recipe YAML file

    Returns:
        RecipeSchema: Validated recipe object

    Raises:
        FileNotFoundError: If the recipe file doesn't exist
        ValueError: If the recipe file is invalid
    """
    if not os.path.exists(recipe_path):
        raise FileNotFoundError(f"Recipe file not found: {recipe_path}")

    try:
        with open(recipe_path, "r") as f:
            recipe_data = yaml.safe_load(f)

            if "run" in recipe_data and "model_type" in recipe_data["run"]:
                model_type = recipe_data["run"]["model_type"]

                if model_type == "hf":
                    return HfRecipeSchema(**recipe_data)
                elif model_type == "neuron-hf":
                    return NeuronHfRecipeSchema(**recipe_data)
                elif "nova" in model_type and "evaluation" in recipe_data:
                    return NovaEvaluationRecipeSchema(**recipe_data)
                elif "nova" in model_type:
                    return NovaRecipeSchema(**recipe_data)
                else:
                    raise Exception("Invalid model_type {model_type}")
            else:
                # there are 3 yaml without model_type
                try:
                    # recipes/training/llama/megatron_llama3_1_8b_nemo.yaml
                    return HfRecipeSchema(**recipe_data)
                except:
                    pass

                try:
                    # recipes/fine-tuning/nova/nova_premier_r5_cpu_distill.yaml
                    # recipes/fine-tuning/nova/nova_pro_r5_cpu_distill.yaml
                    return NovaRecipeSchema(**recipe_data)
                except:
                    pass

                raise Exception(
                    "Cannot validate recipe with existing templates. Check your recipe.yaml file."
                )

    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in recipe file: {e}")
    except Exception as e:
        raise ValueError(f"Error validating recipe: {e}")


def save_recipe(
    recipe: (
        HfRecipeSchema
        | NeuronHfRecipeSchema
        | NovaRecipeSchema
        | NovaEvaluationRecipeSchema
    ),
    output_path: str,
) -> None:
    """
    Save a recipe object to a YAML file.

    Args:
        recipe: schema object
        output_path: Path to save the YAML file

    Raises:
        ValueError: If the recipe can't be saved
    """
    try:
        # Convert to dict, excluding None values
        recipe_dict = recipe.model_dump(exclude_none=True)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save to YAML
        with open(output_path, "w") as f:
            yaml.dump(recipe_dict, f, default_flow_style=False)
    except Exception as e:
        raise ValueError(f"Error saving recipe: {e}")
