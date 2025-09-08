import sys
from typing import Mapping, Type, List, Dict, Any
import click
import pkgutil
import json

JUMPSTART_SCHEMA = "hyperpod_jumpstart_inference_template"
CUSTOM_SCHEMA = "hyperpod_custom_inference_template"
JUMPSTART_COMMAND = "hyp-jumpstart-endpoint"
CUSTOM_COMMAND = "hyp-custom-endpoint"
PYTORCH_SCHEMA="hyperpod_pytorch_job_template"
PYTORCH_COMMAND="hyp-pytorch-job"


def extract_version_from_args(registry: Mapping[str, Type], schema_pkg: str, default: str) -> str:
    if "--version" not in sys.argv:
        return default

    idx = sys.argv.index("--version")
    if idx + 1 >= len(sys.argv):
        return default

    requested_version = sys.argv[idx + 1]
    invoked_command = next(
        (arg for arg in sys.argv if arg.startswith('hyp-')),
        None
    )

    # Check if schema validation is needed
    needs_validation = (
        (schema_pkg == JUMPSTART_SCHEMA and invoked_command == JUMPSTART_COMMAND) or
        (schema_pkg == CUSTOM_SCHEMA and invoked_command == CUSTOM_COMMAND) or
        (schema_pkg == PYTORCH_SCHEMA and invoked_command == PYTORCH_COMMAND)
    )

    if registry is not None and requested_version not in registry:
        if needs_validation:
                raise click.ClickException(f"Unsupported schema version: {requested_version}")
        else:
            return default

    return requested_version


def get_latest_version(registry: Mapping[str, Type]) -> str:
    """
    Get the latest version from the schema registry.
    """
    if not registry:
        raise ValueError("Schema registry is empty")

    # Sort versions and return the last (highest) one
    sorted_versions = sorted(registry.keys(), key=lambda v: [int(x) for x in v.split('.')])
    return sorted_versions[-1]


def load_schema_for_version(
    version: str,
    base_package: str,
) -> dict:
    """
    Load schema.json from the top-level <base_package>.vX_Y_Z package.
    """
    ver_pkg = f"{base_package}.v{version.replace('.', '_')}"
    raw = pkgutil.get_data(ver_pkg, "schema.json")
    if raw is None:
        raise click.ClickException(
            f"Could not load schema.json for version {version} "
            f"(looked in package {ver_pkg})"
        )
    return json.loads(raw)


# Generic confirmation utilities that can be reused across commands
class GenericConfirmationHandler:
    """Generic handler for user confirmations in CLI operations."""
    
    def confirm_action(self, action_description: str, auto_confirm: bool = False) -> bool:
        """
        Generic confirmation prompt for any CLI action.
        
        Args:
            action_description: Description of what will happen
            auto_confirm: If True, skip confirmation (for testing/automation)
            
        Returns:
            True if user confirms, False otherwise
        """
        if auto_confirm:
            return True
            
        click.echo(action_description)
        return click.confirm("Continue?", default=False)
    
    def display_warning_list(self, title: str, items: Dict[str, List[str]], 
                           warning_symbol: str = "⚠") -> None:
        """
        Display a categorized list of items with a warning.
        
        Args:
            title: Main warning title
            items: Dictionary of category -> list of items
            warning_symbol: Symbol to use for warning
        """
        total_count = sum(len(item_list) for item_list in items.values())
        click.echo(f"\n{warning_symbol} {title} {total_count} resources:\n")
        
        for category, item_list in items.items():
            if item_list:
                click.echo(f"{category} ({len(item_list)}):")
                for item in item_list:
                    click.echo(f" - {item}")
                click.echo()
    
    def display_retention_info(self, retained_items: List[str]) -> None:
        """
        Display information about items that will be retained.
        
        Args:
            retained_items: List of items that will be retained
        """
        if retained_items:
            click.echo(f"\nThe following {len(retained_items)} resources will be RETAINED:")
            for item in retained_items:
                click.echo(f" ✓ {item} (retained)")


def parse_comma_separated_list(value: str) -> List[str]:
    """
    Parse a comma-separated string into a list of strings.
    Generic utility that can be reused across commands.
    
    Args:
        value: Comma-separated string like "item1,item2,item3"
        
    Returns:
        List of trimmed strings
    """
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def categorize_resources_by_type(resources: List[Dict[str, Any]], 
                                type_mappings: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Generic function to categorize resources by type.
    
    Args:
        resources: List of resource dictionaries with 'ResourceType' and 'LogicalResourceId'
        type_mappings: Dictionary mapping category names to lists of resource types
        
    Returns:
        Dictionary of category -> list of resource names
    """
    categorized = {category: [] for category in type_mappings.keys()}
    categorized["Other"] = []
    
    for resource in resources:
        resource_type = resource.get("ResourceType", "")
        logical_id = resource.get("LogicalResourceId", "")
        
        # Find which category this resource type belongs to
        category_found = False
        for category, types in type_mappings.items():
            if any(resource_type.startswith(rt) for rt in types):
                categorized[category].append(logical_id)
                category_found = True
                break
        
        if not category_found:
            categorized["Other"].append(logical_id)
    
    # Remove empty categories
    return {k: v for k, v in categorized.items() if v}
