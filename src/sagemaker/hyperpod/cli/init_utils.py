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
import inspect
import click
import json


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


def load_schema_for_version(version: str, schema_pkg: str) -> dict:
    ver_pkg = f"{schema_pkg}.v{version.replace('.', '_')}"
    raw = pkgutil.get_data(ver_pkg, "schema.json")
    if raw is None:
        raise click.ClickException(f"Could not load schema.json for version {version}")
    return json.loads(raw)


def generate_click_command(
    *,
    version_key_arg: str = "version",
    require_schema_fields: bool = True,
    template_arg_name: str = "template",
    auto_load_config: bool = False,
) -> Callable:
    """
    Decorator that:
      - injects --env, --dimensions, etc
      - injects --<prop> for every property in the UNION of all templates' schemas
      - at runtime, either reads the 'template' argument (init) or auto-loads from config.yaml (configure)
    """

    # build the UNION of all schema props + required flags
    union_props = {}
    union_reqs = set()
    for template, template_info in TEMPLATES.items():
        if template_info["schema_type"] == CRD:
            schema = load_schema_for_version("1.0", template_info["schema_pkg"])
            for k, spec in schema.get("properties", {}).items():
                union_props.setdefault(k, spec)
            if require_schema_fields:
                union_reqs |= set(schema.get("required", []))
        elif template_info["schema_type"] == CFN:
            cluster_template = json.loads(HpClusterStack.get_template())
            cluster_parameters = cluster_template.get("Parameters")

    def decorator(func: Callable) -> Callable:
        # JSON flag parser
        def _parse_json_flag(ctx, param, value):
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                raise click.BadParameter(f"{param.name!r} must be valid JSON: {e}")

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            # determine template, directory, namespace, version
            if auto_load_config:
                # configure path: load from existing config.yaml
                dir_path = Path('.').resolve()
                config_file = dir_path / 'config.yaml'
                if not config_file.is_file():
                    raise click.UsageError("No config.yaml found; run `hyp init` first.")
                data = yaml.safe_load(config_file.read_text()) or {}
                template = data.get('template')
                namespace = data.get('namespace', 'default')
                version = data.get(version_key_arg, '1.0')
                directory = str(dir_path)
            else:
                # init path: pull off template & directory from args/kwargs
                sig = inspect.signature(func)
                params = list(sig.parameters)
                if params[0] == template_arg_name:
                    if args:
                        template, directory, *rest = args
                    else:
                        template = kwargs.pop(template_arg_name)
                        directory = kwargs.pop('directory')
                else:
                    raise RuntimeError('generate_click_command: signature mismatch')
                namespace = kwargs.pop('namespace', None)
                version = kwargs.pop(version_key_arg, '1.0')

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
                if require_schema_fields:
                    model_obj = Model(**kwargs)
                else:
                    try:
                        model_obj = Model(**kwargs)
                    except ValidationError:
                        model_obj = Model.model_construct(**kwargs)
            elif template_info.get("schema_type") == CFN:
                model_obj = HpClusterStack(**kwargs)

            # call underlying function
            if auto_load_config:
                return func(model_config=model_obj)
            else:
                return func(template, directory, namespace, version, model_obj)

        # inject JSON flags
        for flag in ('env', 'dimensions', 'resources-limits', 'resources-requests'):
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
                'env',
                'dimensions',
                'resources_limits',
                'resources_requests',
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

            wrapped = click.option(
                f"--{name.replace('_','-')}",
                required=(name in union_reqs),
                default=spec.get('default'),
                show_default=('default' in spec),
                type=ctype,
                help=spec.get('description',''),
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
                wrapped = click.option(
                    f"--{pascal_to_kebab(cfn_param_name)}",
                    default=cfn_param_details.get('Default'),
                    show_default=('Default' in cfn_param_details),
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
            val = "" if val is None else val
            f.write(f"{key}: {val}\n\n")

    print(f"Configuration saved to: {path}")


def load_config_and_validate(dir_path: Path = None) -> Tuple[dict, str, str]:
    """
    Load config.yaml, validate it exists, and extract template and version.
    Returns (config_data, template, version)
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
    
    # For CFN templates, validate using HpClusterStack
    template_info = TEMPLATES[template]
    if template_info["schema_type"] == CFN:
        try:
            # Filter out template and namespace fields for validation
            filtered_config = {}
            for k, v in data.items():
                if k not in ('template', 'namespace') and v is not None:
                    # Convert lists to JSON strings, everything else to string
                    if isinstance(v, list):
                        filtered_config[k] = json.dumps(v)
                    else:
                        filtered_config[k] = str(v)
            click.secho(filtered_config)
            HpClusterStack(**filtered_config)
        except ValidationError as e:
            click.secho("❌  Config validation errors:", fg="red")
            for err in e.errors():
                loc = '.'.join(str(x) for x in err['loc'])
                msg = err['msg']
                click.echo(f"  – {loc}: {msg}")
            sys.exit(1)
        
    return data, template, version


def build_config_from_schema(template: str, namespace: str, version: str, model_config=None, existing_config=None) -> Tuple[dict, dict]:
    """
    Build a config dictionary and comment map from schema.
    
    Args:
        template: Template name
        namespace: Namespace value
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
                    for field, field_info in model_config.model_fields.items()}
        else:
            props = {}
        reqs = []
    else:
        schema = load_schema_for_version(version, info["schema_pkg"])
        props = schema.get("properties", {})
        reqs = schema.get("required", [])
    
    # Build config dict with defaults from schema
    full_cfg = {
        "template": template,
        "namespace": namespace,
    }
    
    # Prepare values from different sources with priority:
    # 1. model_config (user-provided values)
    # 2. existing_config (values from existing config.yaml)
    # 3. schema defaults
    values = {}
    
    # Add schema defaults first (lowest priority)
    for key, spec in props.items():
        if "default" in spec:
            values[key] = spec.get("default")
    
    # Add existing config values next (middle priority)
    if existing_config:
        for key, val in existing_config.items():
            if key not in ("template", "namespace") and key in props:
                values[key] = val
    
    # Add model_config values last (highest priority)
    if model_config:
        cfg_dict = model_config.model_dump(exclude_none=True)
        for key, val in cfg_dict.items():
            if key in props:
                values[key] = val
    
    # Build the final config with required fields first, then optional
    for key in reqs:
        if key in props:
            full_cfg[key] = values.get(key, None)
    
    for key in props:
        if key not in reqs:
            full_cfg[key] = values.get(key, None)
    
    # Build comment map with [Required] prefix for required fields
    comment_map = {}
    for key, spec in props.items():
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


def pascal_to_kebab(pascal_str):
    """Convert PascalCase string  to kebab-case"""
    result = []
    for i, char in enumerate(pascal_str):
        if char.isupper() and i > 0:
            result.append('-')
        result.append(char.lower())
    return ''.join(result)
