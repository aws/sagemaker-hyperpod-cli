import importlib
import json
import logging
import pkgutil
import click
from typing import Callable, Tuple
import os
import yaml
import sys
from pathlib import Path
import functools
from pydantic import ValidationError
from sagemaker.hyperpod.common.utils import (
    region_to_az_ids
)
from typing import List, Any
from sagemaker.hyperpod.cli.constants.init_constants import (
    TEMPLATES,
    CRD,
    CFN
)
from sagemaker.hyperpod.cluster_management.hp_cluster_stack import HpClusterStack

log = logging.getLogger()

def save_template(template: str, directory_path: Path) -> bool:
    """
    Save the appropriate k8s template based on the template type.
    """
    try:
        if TEMPLATES[template]["schema_type"] == CRD:
            save_k8s_jinja(directory=str(directory_path), content=TEMPLATES[template]["template"])
        elif TEMPLATES[template]["schema_type"] == CFN:
            save_cfn_jinja(directory=str(directory_path), content=TEMPLATES[template]["template"])
        return True
    except Exception as e:
        click.secho(f"⚠️ Template generation failed: {e}", fg="yellow")
        return False

def save_cfn_jinja(directory: str, content: str):
    Path(directory).mkdir(parents=True, exist_ok=True)
    path = os.path.join(directory, "cfn_params.jinja")
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    click.secho(f"Cloudformation Parameters Jinja template saved to: {path}")
    return path

def save_k8s_jinja(directory: str, content: str):
    Path(directory).mkdir(parents=True, exist_ok=True)
    path = os.path.join(directory, "k8s.jinja")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"K8s Jinja template saved to: {path}")
    return path


def filter_cli_metadata_fields(config_data: dict) -> dict:
    """
    Filter out CLI metadata fields that should not be passed to Pydantic models.
    
    Args:
        config_data: Configuration data dictionary
        
    Returns:
        Filtered dictionary without CLI metadata fields
    """
    return {
        k: v for k, v in config_data.items() 
        if k not in ('template', 'version') and v is not None
    }


def get_latest_version_from_registry(template: str) -> str:
    """
    Get the latest version available in the registry for a given template.
    
    Args:
        template: Template name
        
    Returns:
        Latest version string (e.g., "1.0", "2.0")
    """
    template_info = TEMPLATES.get(template)
    if not template_info:
        raise click.ClickException(f"Unknown template: {template}")
    
    if template_info.get("schema_type") == CFN:
        # CFN templates don't have versioned registries, return default
        return "1.0"
    
    registry = template_info.get("registry")
    if not registry:
        raise click.ClickException(f"No registry found for template: {template}")
    
    # Get all available versions and return the latest
    available_versions = list(registry.keys())
    if not available_versions:
        raise click.ClickException(f"No versions available in registry for template: {template}")
    
    # Sort versions to get the latest (assuming semantic versioning)
    # Convert to tuples for proper version comparison (e.g., "1.0" -> (1, 0))
    def version_key(v):
        try:
            return tuple(map(int, v.split('.')))
        except ValueError:
            # Fallback for non-numeric versions
            return (0, 0)
    
    latest_version = max(available_versions, key=version_key)
    return str(latest_version)


def get_default_version_for_template(template: str) -> str:
    """
    Get the default version for a template (latest available).
    
    Args:
        template: Template name
        
    Returns:
        Default version string
    """
    # Check if template exists first
    if template not in TEMPLATES:
        raise click.ClickException(f"Unknown template: {template}")
        
    try:
        return get_latest_version_from_registry(template)
    except Exception:
        raise click.ClickException(f"Could not get the latest version for template: {template}")


def load_schema_for_version(version: str, schema_pkg: str) -> dict:
    ver_pkg = f"{schema_pkg}.v{str(version).replace('.', '_')}"
    raw = pkgutil.get_data(ver_pkg, "schema.json")
    if raw is None:
        raise click.ClickException(f"Could not load schema.json for version {version}")
    return json.loads(raw)


def generate_click_command(
    *,
    version_key_arg: str = "version",
    template_arg_name: str = "template",
) -> Callable:
    """
    Decorator that:
      - injects --<prop> for every property in the current template's schema (detected from config.yaml)
      - only works for configure command, returns minimal decorator for others
    """

    # Only execute full decorator logic for configure command
    is_configure_command = len(sys.argv) > 1 and sys.argv[1] == "configure"
    
    if not is_configure_command:
        # Return a minimal decorator that doesn't add any options
        def decorator(func: Callable) -> Callable:
            return func
        return decorator
        
    config_file = Path(".").resolve() / "config.yaml"
    if not config_file.is_file():
        click.secho("❌  No config.yaml found. Run 'hyp init <template>' first.", fg="red")
        sys.exit(1)
    
    _, current_template, current_version = load_config()
    
    # Build schema props for current template only
    union_props = {}
    template_info = TEMPLATES[current_template]
    
    if template_info["schema_type"] == CRD:
        schema = load_schema_for_version(str(current_version), template_info["schema_pkg"])
        for k, spec in schema.get("properties", {}).items():
            # Ensure description is always a string
            if 'description' in spec:
                desc = spec['description']
                if isinstance(desc, list):
                    spec = spec.copy()  # Don't modify the original
                    spec['description'] = ', '.join(str(item) for item in desc)
            union_props[k] = spec
    elif template_info["schema_type"] == CFN:
        json_schema = HpClusterStack.model_json_schema()
        schema_properties = json_schema.get('properties', {})
        
        for field, field_info in HpClusterStack.model_fields.items():
            prop_info = {"description": field_info.description or ""}
            
            # Get examples from JSON schema if available
            if field in schema_properties and 'examples' in schema_properties[field]:
                prop_info["examples"] = schema_properties[field]['examples']
            
            union_props[field] = prop_info

    # build required flags for current template
    union_reqs = set()

    def decorator(func: Callable) -> Callable:
        # Initialize cluster_parameters only if current template is CFN
        cluster_parameters = {}
        if template_info["schema_type"] == CFN:
            try:
                cluster_template = json.loads(HpClusterStack.get_template())
                cluster_parameters = cluster_template.get("Parameters", {})
            except Exception:
                # If template can't be fetched, use empty dict
                pass
            
        # JSON flag parser
        def _parse_json_flag(ctx, param, value):
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Try to fix unquoted list items: [python, train.py] -> ["python", "train.py"]
                if value.strip().startswith('[') and value.strip().endswith(']'):
                    try:
                        # Remove brackets and split by comma
                        inner = value.strip()[1:-1]
                        items = [item.strip().strip('"').strip("'") for item in inner.split(',')]
                        return items
                    except:
                        pass
                raise click.BadParameter(f"{param.name!r} must be valid JSON or a list like [item1, item2]")


        # Volume flag parser
        def _parse_volume_flag(ctx, param, value):
            if not value:
                return None
            
            # Handle multiple volume flags
            if not isinstance(value, (list, tuple)):
                value = [value]
            
            from hyperpod_pytorch_job_template.v1_0.model import VolumeConfig
            volumes = []
            
            for vol_str in value:
                # Parse volume string: name=model-data,type=hostPath,mount_path=/data,path=/data
                vol_dict = {}
                for pair in vol_str.split(','):
                    if '=' in pair:
                        key, val = pair.split('=', 1)
                        key = key.strip()
                        val = val.strip()
                        
                        # Convert read_only to boolean
                        if key == 'read_only':
                            vol_dict[key] = val.lower() in ('true', '1', 'yes', 'on')
                        else:
                            vol_dict[key] = val
                
                try:
                    volumes.append(VolumeConfig(**vol_dict))
                except Exception as e:
                    raise click.BadParameter(f"Invalid volume configuration '{vol_str}': {e}")
            
            return volumes

        @functools.wraps(func)
        def wrapped(*args, **kwargs):

            # configure path: load from existing config.yaml
            dir_path = Path('.').resolve()
            config_file = dir_path / 'config.yaml'
            if not config_file.is_file():
                raise click.UsageError("No config.yaml found; run `hyp init` first.")
            data = yaml.safe_load(config_file.read_text()) or {}
            template = data.get('template')
            version = data.get(version_key_arg, '1.0')
            
            # Extract user version and config version
            user_version = kwargs.pop(version_key_arg, None)
            config_version = data.get(version_key_arg)
            
            # Ensure config_version is always a string (YAML might load it as float)
            if config_version is not None:
                config_version = str(config_version)

            # Configure/Reset/Validate commands: Config file version is PRIMARY source of truth
            # Priority: config file version > 1.0 (backward compatibility) > user --version flag (rare override)
            if config_version is not None:
                version = config_version
            elif user_version is not None:
                # Rare case: user explicitly overrides with --version flag
                version = user_version
            else:
                # Config file has no version - default to 1.0 for backward compatibility
                raise click.ClickException(f"Could not get the latest version for template: {template}")


            # lookup registry & schema_pkg
            template_info = TEMPLATES.get(template)
            if not template_info:
                raise click.ClickException(f"Unknown template: {template}")
            if template_info.get("schema_type") == CRD:
                registry = template_info['registry']

                Model = registry.get(version)
                if Model is None:
                    raise click.ClickException(f"Unsupported schema version: {version}")

                # build Pydantic model (bypass validation on configure)
                filtered_kwargs = filter_cli_metadata_fields(kwargs)
                model_obj = Model.model_construct(**filtered_kwargs)
            elif template_info.get("schema_type") == CFN:
                model_obj = HpClusterStack(**kwargs)

            # call underlying function
            return func(model_config=model_obj)

        # inject JSON flags with proper field names - only if they exist in template properties
        for flag in ('env', 'args', 'command', 'label-selector', 'dimensions', 'resources-limits', 'resources-requests', 'tags'):
            flag_name = flag.replace('-', '_')
            if flag_name in union_props:
                wrapped = click.option(
                    f"--{flag}",
                    callback=_parse_json_flag,
                    metavar="JSON",
                    help=f"JSON object for {flag.replace('-', ' ')}",
                )(wrapped)


        # inject every union schema property
        for name, spec in reversed(list(union_props.items())):
            if name in (
                template_arg_name,
                'directory',
                version_key_arg,
                'args', # Skip since handled by JSON flag
                'command', # Skip since handled by JSON flag
                'label_selector', # Skip since handled by --label-selector JSON flag
                'dimensions',
                'resources_limits',
                'resources_requests',
                'tags',
                'custom_bucket_name', # Fixed default, not configurable
                'github_raw_url', # Fixed default, not configurable
                'helm_repo_url', # Fixed default, not configurable
                'helm_repo_path', # Fixed default, not configurable
            ):
                continue

            # infer click type
            if 'enum' in spec:
                ctype = click.Choice(spec['enum'])
            elif spec.get('type') == 'integer':
                ctype = int
            elif spec.get('type') == 'number':
                ctype = float
            elif spec.get('type') == 'boolean':
                ctype = bool
            else:
                ctype = str

            # Get help text and ensure it's a string
            help_text = spec.get('description', '')
            if isinstance(help_text, list):
                help_text = ', '.join(str(item) for item in help_text)

            # Special handling for volume parameter
            if name == 'volume':
                wrapped = click.option(
                    f"--{name.replace('_','-')}",
                    multiple=True,
                    callback=_parse_volume_flag,
                    help=help_text,
                )(wrapped)
            else:
                wrapped = click.option(
                    f"--{name.replace('_','-')}",
                    required=(name in union_reqs),
                    default=spec.get('default'),
                    show_default=('default' in spec),
                    type=ctype,
                    help=help_text,
                )(wrapped)

        for cfn_param_name, cfn_param_details in cluster_parameters.items():
            # Convert CloudFormation type to Click type
            cfn_type = cfn_param_details.get('Type', 'String')
            if cfn_type == 'Number':
                click_type = float
            elif cfn_type == 'Integer':
                click_type = int
            else:
                click_type = str

            # Special handling for tags parameter
            if cfn_param_name == 'Tags':
                wrapped = click.option(
                    f"--{pascal_to_kebab(cfn_param_name)}",
                    callback=_parse_json_flag,
                    metavar="JSON",
                    help=cfn_param_details.get('Description', ''),
                )(wrapped)
            else:
                cfn_default = cfn_param_details.get('Default')
                wrapped = click.option(
                    f"--{pascal_to_kebab(cfn_param_name)}",
                    default=cfn_default,
                    show_default=cfn_default,

                    type=click_type,
                    help=cfn_param_details.get('Description', ''),

                )(wrapped)

        return wrapped

    return decorator


def save_config_yaml(prefill: dict, comment_map: dict, directory: str):
    os.makedirs(directory, exist_ok=True)
    filename = "config.yaml"
    path = os.path.join(directory, filename)
    
    with open(path, 'w') as f:
        for key in prefill:
            comment = comment_map.get(key)
            if comment:
                f.write(f"# {comment}\n")

            val = prefill.get(key)
            
            # Handle nested structures like volumes
            if key == 'volume' and isinstance(val, list) and val:
                f.write(f"{key}:\n")
                for vol in val:
                    f.write(f"  - name: {vol.get('name', '')}\n")
                    f.write(f"    type: {vol.get('type', '')}\n") 
                    f.write(f"    mount_path: {vol.get('mount_path', '')}\n")
                    if vol.get('path'):
                        f.write(f"    path: {vol.get('path')}\n")
                    if vol.get('claim_name'):
                        f.write(f"    claim_name: {vol.get('claim_name')}\n")
                    if vol.get('read_only') is not None:
                        f.write(f"    read_only: {vol.get('read_only')}\n")
                f.write("\n")
            elif isinstance(val, list):
                # Handle arrays in YAML format
                if val:
                    f.write(f"{key}:\n")
                    for item in val:
                        f.write(f"  - {item}\n")
                else:
                    f.write(f"{key}: []\n")
                f.write("\n")
            else:
                # Handle simple values
                val = "" if val is None else val
                f.write(f"{key}: {val}\n\n")

    print(f"Configuration saved to: {path}")

def update_field_in_config(dir_path: str, field_name: str, value):
    """Update specific field in config.yaml file while preserving format."""
    config_path = os.path.join(dir_path, "config.yaml")
    
    with open(config_path, 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{field_name}:"):
            lines[i] = f"{field_name}: {value}\n"
            break
    
    with open(config_path, 'w') as f:
        f.writelines(lines)

def update_list_field_in_config(dir_path: str, field_name: str, values: List[Any]):
    """Update specific field in config.yaml file if the field is a list"""
    config_path = os.path.join(dir_path, "config.yaml")
    
    with open(config_path, 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{field_name}:"):
            # Replace the field line and any subsequent list items
            lines[i] = f"{field_name}:\n"
            # Remove any existing list items for this field
            j = i + 1
            while j < len(lines) and (lines[j].startswith('  - ') or lines[j].strip() == ''):
                j += 1

            # Remove the old list items
            del lines[i+1:j]

            # Insert new list items
            for k, value in enumerate(values):
                lines.insert(i + 1 + k, f"  - {value}\n")

            # Add a newline after the list
            lines.insert(i + 1 + len(values), "\n")
            break
    
    with open(config_path, 'w') as f:
        f.writelines(lines)

def add_default_az_ids_to_config(dir_path: str, region: str):
    # update availability zone id
    config_path = dir_path / 'config.yaml'
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f) or {}

    # populdate availability_zone_ids
    if not config_data.get('availability_zone_ids'):
        try:
            all_az_ids = region_to_az_ids(region)

            # default to first two AZ IDs in the region
            az_ids = all_az_ids[:2]

            update_list_field_in_config(dir_path, 'availability_zone_ids', az_ids)
            click.secho(f"No availability_zone_ids provided. Using default AZ Id: {az_ids}.", fg="yellow")
        except Exception as e:
            raise Exception(f"Failed to find default availability_zone_ids for region {region}. Please provide one in config.yaml. Error details: {e}")

    # populate fsx_availability_zone_id
    if not config_data.get('fsx_availability_zone_id'):
        try:
            # default to first az_id
            update_field_in_config(dir_path, 'fsx_availability_zone_id', all_az_ids[0])
            click.secho(f"No fsx_availability_zone_id provided. Using default AZ Id: {all_az_ids[0]}.", fg="yellow")
        except Exception as e:
            raise Exception(f"Failed to find default fsx_availability_zone_id for region {region}. Please provide one in config.yaml. Error details: {e}")

def load_config(dir_path: Path = None) -> Tuple[dict, str, str]:
    """
    Base function to load and parse config.yaml file.
    Returns (config_data, template, version)
    
    Args:
        dir_path: Directory path to look for config.yaml (defaults to current directory)
        
    Returns:
        Tuple of (config_data, template, version)
        
    Raises:
        SystemExit: If config.yaml not found or template is unknown
    """
    if dir_path is None:
        dir_path = Path(".").resolve()
    
    config_file = dir_path / "config.yaml"
    if not config_file.is_file():
        click.secho("❌  No config.yaml found in the current directory.", fg="red")
        sys.exit(1)

    # Load existing config
    data = yaml.safe_load(config_file.read_text()) or {}
    template = data.get("template")
    version = data.get("version", "1.0")

    if template not in TEMPLATES:
        click.secho(f"❌  Unknown template '{template}' in config.yaml", fg="red")
        sys.exit(1)
        
    return data, template, version


def load_config_and_validate(dir_path: Path = None) -> Tuple[dict, str, str]:
    """
    Load config.yaml, validate it exists, and extract template and version.
    Returns (config_data, template, version)
    Exits on validation errors - use for commands that require valid config.
    """
    data, template, version = load_config(dir_path)
    validation_errors = validate_config_against_model(data, template, version)
    
    is_valid = display_validation_results(
        validation_errors, 
        success_message="config.yaml is valid!",
        error_prefix="Config validation errors:"
    )
    
    if not is_valid:
        sys.exit(1)

    return data, template, version


def validate_config_against_model(config_data: dict, template: str, version: str) -> list:
    """
    Validate config data against the appropriate Pydantic model.
    Returns list of validation error strings, empty if no errors.
    
    Args:
        config_data: Configuration data to validate
        template: Template name
        version: Schema version
        
    Returns:
        List of validation error strings
    """
    template_info = TEMPLATES[template]
    validation_errors = []
    
    try:
        # For CFN templates, filter config but keep original types for validation
        filtered_config = {
            k: v for k, v in config_data.items() 
            if k not in ('template', 'version') and v is not None
        }
        if template_info["schema_type"] == CFN:
            HpClusterStack(**filtered_config)
        else:
            registry = template_info["registry"]
            model = registry.get(str(version))  # Convert to string for lookup
            if model:
                
                # Special handling for JSON fields that might be passed as strings
                for key in ('args', 'environment'):
                    if key in filtered_config and isinstance(filtered_config[key], str):
                        val = filtered_config[key].strip()
                        # Try to parse as JSON if it looks like JSON
                        if val.startswith('[') or val.startswith('{'):
                            try:
                                filtered_config[key] = json.loads(val)
                            except json.JSONDecodeError:
                                # If JSON parsing fails, keep as string and let validation handle it
                                pass
                
                # Special handling for nested structures like volumes
                if 'volume' in filtered_config and filtered_config['volume']:
                    # Convert YAML volume structure back to VolumeConfig objects for validation
                    from hyperpod_pytorch_job_template.v1_0.model import VolumeConfig
                    volume_configs = []
                    for vol_dict in filtered_config['volume']:
                        if isinstance(vol_dict, dict):
                            volume_configs.append(VolumeConfig(**vol_dict))
                    filtered_config['volume'] = volume_configs
                
                model(**filtered_config)
                
    except ValidationError as e:
        for err in e.errors():
            loc = '.'.join(str(x) for x in err['loc'])
            msg = err['msg']
            validation_errors.append(f"{loc}: {msg}")
        
    return validation_errors


def filter_validation_errors_for_user_input(validation_errors: list, user_input_fields: set) -> list:
    """
    Filter validation errors to only include those related to user input fields.
    
    Args:
        validation_errors: List of validation error strings in format "field: message"
        user_input_fields: Set of field names that user provided
        
    Returns:
        List of validation errors related only to user input fields
    """
    user_input_errors = []
    for error in validation_errors:
        # Extract field name from error string (format: "field: message")
        if ':' in error:
            field_name = error.split(':', 1)[0].strip()
            if field_name in user_input_fields:
                user_input_errors.append(error)
    return user_input_errors


def display_validation_results(validation_errors: list, success_message: str = "Configuration is valid!", 
                             error_prefix: str = "Validation errors:") -> bool:
    """
    Display validation results to the user.
    
    Args:
        validation_errors: List of validation error strings
        success_message: Message to show when validation passes
        error_prefix: Prefix for error messages
        
    Returns:
        True if validation passed, False if there were errors
    """
    if validation_errors:
        click.secho(f"❌  {error_prefix}", fg="red")
        for error in validation_errors:
            click.echo(f"  – {error}")
        return False
    else:
        click.secho(f"✔️  {success_message}", fg="green")
        return True


def build_config_from_schema(template: str, version: str, model_config=None, existing_config=None, user_provided_fields=None) -> Tuple[dict, dict]:

    """
    Build a config dictionary and comment map from schema.
    
    Args:
        template: Template name
        version: Schema version
        model_config: Optional Pydantic model with user-provided values
        existing_config: Optional existing config to merge with
        
    Returns:
        Tuple of (full_config, comment_map)
    """
    # Load schema and pull out properties + required list
    info = TEMPLATES[template]
    
    if info["schema_type"] == CFN:
        # For CFN templates, use model fields instead of schema
        if model_config:
            props = {field: {"description": field_info.description or ""} 
                    for field, field_info in model_config.__class__.model_fields.items()}
        else:
            props = {}
        # For CFN templates, always get fields from HpClusterStack model
        # Use JSON schema to get examples
        json_schema = HpClusterStack.model_json_schema()
        schema_properties = json_schema.get('properties', {})
        
        props = {}
        for field, field_info in HpClusterStack.model_fields.items():
            prop_info = {"description": field_info.description or ""}
            
            # Add default from model field if available
            if hasattr(field_info, 'default') and field_info.default is not None:
                # Handle different types of defaults
                if hasattr(field_info.default, '__call__'):
                    # For callable defaults, call them to get the actual value
                    try:
                        prop_info["default"] = field_info.default()
                    except:
                        # If calling fails, use the raw default
                        prop_info["default"] = field_info.default
                else:
                    prop_info["default"] = field_info.default
            
            # Get examples from JSON schema if available
            if field in schema_properties and 'examples' in schema_properties[field]:
                prop_info["examples"] = schema_properties[field]['examples']
            
            props[field] = prop_info
        reqs = []
    else:
        # For CRD templates, use the provided version (should always be provided)
        # Don't fallback to latest version here - version should come from caller
        if not version:
            raise ValueError(f"Version must be provided for template {template}")
        schema = load_schema_for_version(version, info["schema_pkg"])
        props = schema.get("properties", {})
        reqs = schema.get("required", [])
    
    # Build config dict with defaults from schema
    full_cfg = {
        "template": template,
        "version": version,  
    }

    
    # Prepare values from different sources with priority:
    # 1. model_config (user-provided values)
    # 2. existing_config (values from existing config.yaml)
    # 3. examples from schema (for reset command)
    # 4. schema defaults
    values = {}
    
    # Add schema defaults first (lowest priority)
    for key, spec in props.items():
        if "default" in spec and spec["default"] is not None:
            values[key] = spec.get("default")

    # Add examples next (for reset command when no existing config, or init command with no user input)
    # Use examples if no model_config and no existing_config (reset command)
    # OR if model_config exists but has no user data and no existing_config (init with no args)
    model_has_user_data = model_config and bool(model_config.model_dump(exclude_none=True))
    use_examples = (not model_config and not existing_config) or (not model_has_user_data and not existing_config)
    
    if use_examples:
        for key, spec in props.items():
            if "examples" in spec and spec["examples"]:
                # Use the first example if it's a list, otherwise use the examples directly
                examples = spec["examples"]
                if isinstance(examples, list) and examples:
                    example_value = examples[0]  # Use first example
                else:
                    example_value = examples
                
                # Special handling for tags: skip if example is empty array
                if key == "tags" and example_value == []:
                    continue
                
                values[key] = example_value
    
    # Add existing config values next (middle priority)
    if existing_config:
        for key, val in existing_config.items():
            # Skip template and version as they're handled separately
            if key in ("template", "version"):

                continue
            if key in props:
                values[key] = val
    
    # Add model_config values last (highest priority)
    if model_config:
        # Only use fields that were actually provided by the user
        if user_provided_fields:
            cfg_dict = model_config.model_dump(exclude_none=True)
            for key, val in cfg_dict.items():
                if key in props and key in user_provided_fields:
                    # Special handling for JSON fields that might be passed as strings
                    if key in ('args', 'environment', 'env', 'command', 'label_selector', 'dimensions', 'resources_limits', 'resources_requests', 'tags') and isinstance(val, str):
                        # Try to parse as JSON if it looks like JSON
                        val_stripped = val.strip()
                        if val_stripped.startswith('[') or val_stripped.startswith('{'):
                            try:
                                val = json.loads(val_stripped)
                            except json.JSONDecodeError:
                                # Try to fix unquoted list items: [python, train.py] -> ["python", "train.py"]
                                if val_stripped.startswith('[') and val_stripped.endswith(']'):
                                    try:
                                        inner = val_stripped[1:-1]
                                        val = [item.strip().strip('"').strip("'") for item in inner.split(',')]
                                    except:
                                        pass
                    
                    # Special handling for nested structures like volumes
                    if key == 'volume' and val:
                        # Get existing volumes from config
                        existing_volumes = values.get('volume', []) or []
                        
                        # Convert new volumes to dict format
                        new_volumes = []
                        for vol in val:
                            if hasattr(vol, 'name'):  # VolumeConfig object
                                vol_dict = {
                                    'name': vol.name,
                                    'type': vol.type,
                                    'mount_path': vol.mount_path
                                }
                                if vol.path:
                                    vol_dict['path'] = vol.path
                                if vol.claim_name:
                                    vol_dict['claim_name'] = vol.claim_name
                                if vol.read_only is not None:
                                    vol_dict['read_only'] = vol.read_only
                            else:  # Already a dict
                                vol_dict = vol
                            new_volumes.append(vol_dict)
                        
                        # Merge: update existing volumes by name or add new ones
                        merged_volumes = existing_volumes.copy()
                        for new_vol in new_volumes:
                            # Find if volume with same name exists
                            updated = False
                            for i, existing_vol in enumerate(merged_volumes):
                                if existing_vol.get('name') == new_vol.get('name'):
                                    merged_volumes[i] = new_vol  # Update existing
                                    updated = True
                                    break
                            if not updated:
                                merged_volumes.append(new_vol)  # Add new
                        
                        values[key] = merged_volumes
                    else:
                        values[key] = val
        else:
            # For init command, use all model_config values
            cfg_dict = model_config.model_dump(exclude_none=True)
            for key, val in cfg_dict.items():
                if key in props:
                    # Special handling for nested structures like volumes
                    if key == 'volume' and val:
                        # Get existing volumes from config
                        existing_volumes = values.get('volume', []) or []
                        
                        # Convert new volumes to dict format
                        new_volumes = []
                        for vol in val:
                            if hasattr(vol, 'name'):  # VolumeConfig object
                                vol_dict = {
                                    'name': vol.name,
                                    'type': vol.type,
                                    'mount_path': vol.mount_path
                                }
                                if vol.path:
                                    vol_dict['path'] = vol.path
                                if vol.claim_name:
                                    vol_dict['claim_name'] = vol.claim_name
                                if vol.read_only is not None:
                                    vol_dict['read_only'] = vol.read_only
                            else:  # Already a dict
                                vol_dict = vol
                            new_volumes.append(vol_dict)
                        
                        # Merge: update existing volumes by name or add new ones
                        merged_volumes = existing_volumes.copy()
                        for new_vol in new_volumes:
                            # Find if volume with same name exists
                            updated = False
                            for i, existing_vol in enumerate(merged_volumes):
                                if existing_vol.get('name') == new_vol.get('name'):
                                    merged_volumes[i] = new_vol  # Update existing
                                    updated = True
                                    break
                            if not updated:
                                merged_volumes.append(new_vol)  # Add new
                        
                        values[key] = merged_volumes
                    else:
                        values[key] = val
    
    # Fields that should not appear in config.yaml (fixed defaults)
    excluded_fields = {'custom_bucket_name', 'github_raw_url', 'helm_repo_url', 'helm_repo_path'}
    
    # Build the final config with required fields first, then optional
    for key in reqs:
        if key in props and key not in excluded_fields:
            full_cfg[key] = values.get(key, None)
    
    for key in props:
        if key not in reqs and key not in excluded_fields:
            full_cfg[key] = values.get(key, None)
    
    # Build comment map with [Required] prefix for required fields
    comment_map = {
        "template": "Template type",
        "version": "Schema version (latest available version used by default)",
    }
    for key, spec in props.items():
        if key not in excluded_fields:
            desc = spec.get("description", "")
            if key in reqs:
                desc = f"[Required] {desc}"
            comment_map[key] = desc
    
    return full_cfg, comment_map


def pascal_to_kebab(pascal_str):
    """Convert PascalCase to CLI kebab-case format"""
    result = []
    for i, char in enumerate(pascal_str):
        if char.isupper() and i > 0:
            result.append('-')
        result.append(char.lower())
    return ''.join(result)