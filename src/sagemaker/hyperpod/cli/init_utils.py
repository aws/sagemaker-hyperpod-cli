import importlib
import json
import logging
import pkgutil
import click
from typing import Callable, Tuple, get_origin, get_args
import os
import yaml
import sys
from pathlib import Path
from sagemaker.hyperpod.cli.type_handler_utils import convert_cli_value, to_click_type, is_complex_type, DEFAULT_TYPE_HANDLER, is_undefined_value
from pydantic import ValidationError
from typing import List, Any
from sagemaker.hyperpod.cli.constants.init_constants import (
    TEMPLATES,
    CRD,
    CFN,
    SPECIAL_FIELD_HANDLERS
)

log = logging.getLogger()

def save_template(template: str, directory_path: Path, version: str = None) -> bool:
    """
    Save the appropriate template based on the template type and version.
    Template content is loaded directly from the template registry.
    """
    try:
        template_info = TEMPLATES[template]
        
        # Use provided version or get latest
        if version is None:
            version = _get_latest_version_from_registry(template)
        
        # Get template content from registry
        template_registry = template_info["template_registry"]
        template_content = template_registry.get(str(version))
        
        if not template_content:
            raise Exception(f"No template found for version {version}")
        
        if template_info["schema_type"] == CRD:
            _save_k8s_jinja(directory=str(directory_path), content=template_content)
        elif template_info["schema_type"] == CFN:
            _save_cfn_jinja(directory=str(directory_path), content=template_content)
        return True
    except Exception as e:
        click.secho(f"⚠️ Template generation failed: {e}", fg="yellow")
        return False

def _save_cfn_jinja(directory: str, content: str):
    Path(directory).mkdir(parents=True, exist_ok=True)
    path = os.path.join(directory, "cfn_params.jinja")
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path

def _save_k8s_jinja(directory: str, content: str):
    Path(directory).mkdir(parents=True, exist_ok=True)
    path = os.path.join(directory, "k8s.jinja")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _filter_cli_metadata_fields(config_data: dict) -> dict:
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


def _get_latest_version_from_registry(template: str) -> str:
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
        return _get_latest_version_from_registry(template)
    except Exception:
        raise click.ClickException(f"Could not get the latest version for template: {template}")


def _load_schema_for_version(version: str, schema_pkg: str) -> dict:
    ver_pkg = f"{schema_pkg}.v{str(version).replace('.', '_')}"
    raw = pkgutil.get_data(ver_pkg, "schema.json")
    if raw is None:
        raise click.ClickException(f"Could not load schema.json for version {version}")
    return json.loads(raw)


def _get_handler_for_field(template_name, field_name, version=None):
    """Get appropriate handler for a field using template.field mapping."""
    if template_name and field_name:
        # Try version-scoped key first, then fall back to unversioned
        if version:
            scoped_key = f"{template_name}.{version}.{field_name}"
            handler = SPECIAL_FIELD_HANDLERS.get(scoped_key)
            if handler:
                return handler
        scoped_key = f"{template_name}.{field_name}"
        handler = SPECIAL_FIELD_HANDLERS.get(scoped_key, DEFAULT_TYPE_HANDLER)
        return handler

    return DEFAULT_TYPE_HANDLER


def _get_click_option_config(handler, field_type, default=None, required=False, help_text=""):
    """Get Click option configuration for any handler."""
    # Handle PydanticUndefined for Click compatibility
    from pydantic_core import PydanticUndefined
    if default is PydanticUndefined:
        default = None

    config = {
        "multiple": handler.get('needs_multiple_option', False),
        "help": help_text,
    }

    # Add defaults and requirements
    if default is not None:
        config["default"] = default
        config["show_default"] = True
    # Always set type, callback overrides when needed
    config["type"] = to_click_type(field_type)

    # Add callback for special handlers or complex types
    if handler != DEFAULT_TYPE_HANDLER or is_complex_type(field_type):
        config["callback"] = handler['parse_strings']

    if is_complex_type(field_type):
        config["metavar"] = "JSON"

    return {k: v for k, v in config.items() if v is not None}


def generate_click_command() -> Callable:
    """
    Decorator that:
      - injects --<prop> for every property in the current template's schema (detected from config.yaml)
      - supports both standard templates (Pydantic) and dynamic templates (.override_spec.json)
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
    
    # Load template info from config
    try:
        data, current_template, current_version = load_config(Path(".").resolve())
    except Exception:
        # If any error, return minimal decorator
        def decorator(func: Callable) -> Callable:
            return func
        return decorator
    
    # Check if this is a dynamic template
    if is_dynamic_template(current_template, Path(".").resolve()):
        return _generate_dynamic_click_command()
    
    # Handle standard templates (existing logic)
    return _generate_standard_click_command(current_template, current_version)


def _generate_dynamic_click_command() -> Callable:
    """Generate Click command for dynamic templates using .override_spec.json"""
    
    # Load dynamic schema
    override_spec = load_dynamic_schema(Path(".").resolve())
    
    def decorator(func: Callable) -> Callable:
        # Add Click options for each field in override_spec
        for key, spec in override_spec.items():
            param_type = spec.get("type", "string")
            help_text = spec.get("description", "")
            default = spec.get("default")
            required = spec.get("required", False)
            
            # Add constraints to help text
            constraints = []
            if "min" in spec:
                constraints.append(f"min: {spec['min']}")
            if "max" in spec:
                constraints.append(f"max: {spec['max']}")
            if "enum" in spec:
                constraints.append(f"allowed: {spec['enum']}")
            
            if constraints:
                help_text = f"{help_text} ({', '.join(constraints)})" if help_text else f"({', '.join(constraints)})"
            
            # Convert type
            if param_type == "integer":
                click_type = int
            elif param_type in ["number", "float"]:
                click_type = float
            elif param_type == "boolean":
                click_type = bool
            else:
                click_type = str
            
            # Convert default value - handle PydanticUndefinedType
            if is_undefined_value(default):
                default = None
            
            # Create Click option
            opt_name = f"--{key.replace('_', '-')}"
            option = click.Option(
                [opt_name], 
                type=click_type, 
                default=default,
                help=help_text,
                required=required,
                show_default=True
            )
            
            # Add to function parameters
            if not hasattr(func, '__click_params__'):
                func.__click_params__ = []
            func.__click_params__.append(option)
        
        # Create wrapper that handles dynamic template arguments
        def wrapper(*args, **kwargs):
            # For dynamic templates, filter out the dynamic options and pass them separately
            # Keep only the expected function parameters
            expected_params = {'option', 'value', 'model_config'}
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in expected_params}
            
            # Pass the dynamic options through ctx.params for the function to access
            return func(*args, option=None, value=None, model_config=None, **filtered_kwargs)
        
        # Copy function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__click_params__ = getattr(func, '__click_params__', [])
        
        return wrapper
    
    return decorator


def _generate_standard_click_command(current_template: str, current_version: str) -> Callable:
    """Generate Click command for standard templates using Pydantic schemas"""
    
    # Build schema props for current template only
    union_props = {}
    template_info = TEMPLATES[current_template]
    
    schema = _load_schema_for_version(str(current_version), template_info["schema_pkg"])
    for k, spec in schema.get("properties", {}).items():
        # Ensure description is always a string
        if 'description' in spec:
            desc = spec['description']
            if isinstance(desc, list):
                spec = spec.copy()  # Don't modify the original
                spec['description'] = ', '.join(str(item) for item in desc)
        union_props[k] = spec

    # Get the model for parameter generation
    registry = template_info['registry']
    model = registry.get(str(current_version))
    if model is None:
        raise click.ClickException(f"Unsupported schema version: {current_version}")

    def decorator(func: Callable) -> Callable:
         # Create a wrapper that converts CLI arguments to model_config
        def wrapper(*args, **kwargs):
            # Filter and convert CLI arguments 
            filtered_kwargs = {}
            for k, v in kwargs.items():
                if v is not None and k in model.model_fields:
                    field = model.model_fields[k]
                    field_type = getattr(field, 'annotation', str)
                    filtered_kwargs[k] = convert_cli_value(v, field_type)
            
            model_config = model.model_construct(**filtered_kwargs)
            return func(*args, option=None, value=None, model_config=model_config)

        # Generate Click options directly from model fields
        for field_name, field in reversed(list(model.model_fields.items())):
            if field_name == "version":
                continue

            flag_name = field_name.replace('_', '-')
            field_type = getattr(field, 'annotation', str)
            required = False  # For configure, all fields should be optional
            default = getattr(field, 'default', None)

            # Get description from union_props
            description = union_props.get(field_name, {}).get('description', '')

            # Use handler-based option config to correctly handle special types
            # (volumes, security groups, etc. need multiple=True and JSON callbacks)
            handler = _get_handler_for_field(current_template, field_name, version=current_version)
            option_kwargs = _get_click_option_config(handler, field_type, default, required, description)
            wrapper = click.option(f"--{flag_name}", **option_kwargs)(wrapper)
        
        return wrapper
    
    return decorator


def save_config_yaml(prefill: dict, comment_map: dict, directory: str):
    os.makedirs(directory, exist_ok=True)
    filename = "config.yaml"
    path = os.path.join(directory, filename)
    
    # Get model class from prefill data
    template = prefill.get('template')

    with open(path, 'w') as f:
        # Write commented template and version at the top
        f.write(f"# template: {prefill.get('template')}\n")
        f.write(f"# version: {prefill.get('version')}\n\n")
        
        for key in prefill:
            # Skip template and version as they're already written
            if key in ('template', 'version'):
                continue
                
            comment = comment_map.get(key)
            if comment:
                f.write(f"# {comment}\n")

            val = prefill.get(key)
            handler = _get_handler_for_field(template, key, version=prefill.get('version'))
            handler['write_to_yaml'](key, handler['from_dicts'](val) if val is not None else val, f)

    # Write lockfile so the template cannot be silently changed by editing config.yaml
    lockfile = os.path.join(directory, ".hyp")
    with open(lockfile, 'w') as f:
        f.write(template)


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
    config_text = config_file.read_text()
    data = yaml.safe_load(config_text) or {}
    
    # Extract template and version from comments
    template = None
    version = None
    
    for line in config_text.split('\n'):
        line = line.strip()
        if line.startswith('# template:'):
            template = line.split(':', 1)[1].strip()
        elif line.startswith('# version:'):
            version = line.split(':', 1)[1].strip()
    
    # Fallback to data if not found in comments (backward compatibility)
    if not template:
        template = data.get("template")
    if not version:
        version = data.get("version", "1.0")

    if not template or template not in TEMPLATES:
        click.secho(f"❌  Unknown template '{template}' in config.yaml", fg="red")
        sys.exit(1)

    # Check lockfile to detect if the template comment was manually changed
    lockfile = dir_path / ".hyp"
    if lockfile.is_file():
        locked_template = lockfile.read_text().strip()
        if locked_template != template:
            click.secho(
                f"❌  Template mismatch: config.yaml says '{template}' but this directory was initialized with '{locked_template}'. "
                f"Do not edit the '# template:' line in config.yaml.",
                fg="red",
            )
            sys.exit(1)

    return data, template, version


def is_dynamic_template(template: str, dir_path: Path = None) -> bool:
    """Check if template uses dynamic schema (.override_spec.json)"""
    if dir_path is None:
        dir_path = Path(".").resolve()
    
    # Check if .override_spec.json exists
    override_spec_file = dir_path / ".override_spec.json"
    return override_spec_file.exists() and template in ["hyp-recipe-job"]


def load_dynamic_schema(dir_path: Path = None) -> dict:
    """Load schema from .override_spec.json for dynamic templates"""
    if dir_path is None:
        dir_path = Path(".").resolve()
    
    override_spec_file = dir_path / ".override_spec.json"
    if not override_spec_file.exists():
        return {}
    
    with open(override_spec_file, 'r') as f:
        return json.load(f)


def load_config_and_validate(dir_path: Path = None) -> Tuple[dict, str, str]:
    """
    Load config.yaml, validate it exists, and extract template and version.
    Returns (config_data, template, version)
    Exits on validation errors - use for commands that require valid config.
    """
    data, template, version = load_config(dir_path)
    
    # Check if this is a dynamic template
    if is_dynamic_template(template, dir_path):
        # For dynamic templates, we don't use Pydantic validation
        # The validation is handled separately if needed
        return data, template, version
    
    # Standard template validation
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
        # Filter config but keep original types for validation
        filtered_config = _filter_cli_metadata_fields(config_data)

        registry = template_info["registry"]
        model = registry.get(str(version))  # Convert to string for lookup
        if model:
            # Unified handler approach
            for key in filtered_config:
                handler = _get_handler_for_field(template, key, version=version)
                filtered_config[key] = handler['from_dicts'](filtered_config[key])

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
            # Check if field_name or its parent field is in user_input_fields
            base_field = field_name.split('.')[0]  # Get 'security_group_ids' from 'security_group_ids.0'
            if field_name in user_input_fields or base_field in user_input_fields:
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

    if not version:
        raise ValueError(f"Version must be provided for template {template}")
    schema = _load_schema_for_version(version, info["schema_pkg"])
    props = schema.get("properties", {})
    reqs = schema.get("required", [])

    
    # Build config dict with template and version for comment generation
    full_cfg = {
        "template": template,
        "version": version,  
    }

    
    # Prepare values from different sources with priority:
    # 1. model_config (user-provided values)
    # 2. existing_config (values from existing config.yaml)
    # 3. schema defaults
    values = {}
    
    # Add schema defaults first (lowest priority)
    for key, spec in props.items():
        if "default" in spec and spec["default"] is not None:
            values[key] = spec.get("default")
    
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
        cfg_dict = model_config.model_dump(exclude_none=False)
        for key, val in cfg_dict.items():
            # Check if field should be included
            should_include = key in props and (not user_provided_fields or key in user_provided_fields)
            if not should_include:
                continue            

            # Unified handler approach
            handler = _get_handler_for_field(template, key, version=version)

            # Parse strings using appropriate handler
            if user_provided_fields and isinstance(val, str):
                val = handler['parse_strings'](val)

            # Always use handler logic for merging
            existing_configs = values.get(key, []) or []
            if isinstance(val, list):
                new_configs = handler['to_dicts'](val or [])
            else:
                new_configs = val  # Keep single str/bool/int as-is
            values[key] = handler['merge_dicts'](existing_configs, new_configs)
    
    # If namespace is None or not set, use get_default_namespace()
    if "namespace" in props and (values.get("namespace") is None):
        from sagemaker.hyperpod.common.utils import get_default_namespace
        default_namespace = get_default_namespace()
        if default_namespace:
            values["namespace"] = default_namespace
        else:
            values["namespace"] = "default"

    
    # Fields that should not appear in config.yaml (fixed defaults)
    # TODO: remove hardcoded exclueded fields or decouple
    excluded_fields = {'custom_bucket_name', 'github_raw_url', 'helm_repo_url', 'helm_repo_path'}
    
    # Build the final config with required fields first, then optional
    for key in reqs:
        if key in props and key not in excluded_fields:
            full_cfg[key] = values.get(key, None)
    
    for key in props:
        if key not in reqs and key not in excluded_fields:
            if props[key].get("deprecated"):
                continue
            full_cfg[key] = values.get(key, None)
    
    # Build comment map with [Required] prefix for required fields
    comment_map = {
        "template": "Template type",
        "version": "Schema version (latest available version used by default)",
    }
    for key, spec in props.items():
        if key not in excluded_fields:
            if spec.get("deprecated"):
                continue
            desc = spec.get("description", "")
            if key in reqs:
                desc = f"[Required] {desc}"
            comment_map[key] = desc
    
    return full_cfg, comment_map


def create_from_k8s_yaml(yaml_file_path: str, debug: bool = False) -> None:
    """Create HyperPod resource from K8s YAML file based on kind mapping."""
    from sagemaker.hyperpod.cli.constants.init_constants import K8S_KIND_MAPPING
    
    with open(yaml_file_path, 'r') as f:
        yaml_data = yaml.safe_load(f)
    
    kind = yaml_data.get('kind')
    if not kind or kind not in K8S_KIND_MAPPING:
        raise ValueError(f"Unsupported kind: {kind}")
    
    mapping = K8S_KIND_MAPPING[kind]
    
    # Dynamic import
    module_path, class_name = mapping["class_path"].rsplit(".", 1)
    module = importlib.import_module(module_path)
    resource_class = getattr(module, class_name)
    
    # Handle different metadata patterns
    if mapping["metadata_handling"] == "combined":
        full_data = {**yaml_data['spec'], 'metadata': yaml_data['metadata']}
        resource = resource_class.model_validate(full_data, by_name=True)
    else:
        from sagemaker.hyperpod.common.config.metadata import Metadata
        resource = resource_class.model_validate(yaml_data['spec'], by_name=True)
        resource.metadata = Metadata.model_validate(yaml_data['metadata'], by_name=True)
    
    resource.create(debug=debug)