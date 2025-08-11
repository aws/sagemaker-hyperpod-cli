import os
import yaml
from typing import Dict, Any, Optional

from sagemaker.hyperpod.cli.recipe_utils.recipe_schema import RecipeSchema


# from recipe_schema import RecipeSchema


def load_recipe(recipe_path: str) -> RecipeSchema:
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
        with open(recipe_path, 'r') as f:
            recipe_data = yaml.safe_load(f)
        
        # Validate and return the recipe
        return RecipeSchema(**recipe_data)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in recipe file: {e}")
    except Exception as e:
        raise ValueError(f"Error validating recipe: {e}")


def save_recipe(recipe: RecipeSchema, output_path: str) -> None:
    """
    Save a recipe object to a YAML file.
    
    Args:
        recipe: RecipeSchema object
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
        with open(output_path, 'w') as f:
            yaml.dump(recipe_dict, f, default_flow_style=False)
    except Exception as e:
        raise ValueError(f"Error saving recipe: {e}")