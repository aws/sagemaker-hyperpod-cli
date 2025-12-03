import json
import pkgutil
import click
from typing import Callable, Optional, Mapping, Type, Dict, Any
from pydantic import ValidationError
import sys
from sagemaker.hyperpod.cli.common_utils import extract_version_from_args, get_latest_version, load_schema_for_version


def generate_click_command(
    *,
    schema_pkg: str = "hyperpod_pytorch_job_template",
    registry: Mapping[str, Type] = None,
) -> Callable:
    """
    Decorator factory that:
      1) Injects click.options from the JSON Schema under `schema_pkg`
      2) At runtime, pops `version`, builds the flat model from `registry`, calls .to_domain()
      3) Finally invokes your handler as `func(version, domain_config)`
    - `schema_pkg`: the importable package root to read schema.json from
    - `registry`: a dict mapping version → flat‐model class, e.g. hyperpod_pytorch_job_template.registry.SCHEMA_REGISTRY
    """
    if registry is None:
        raise ValueError("You must pass a registry mapping version→Model")

    default_version = get_latest_version(registry)
    version = extract_version_from_args(registry, schema_pkg, default_version)

    def decorator(func: Callable) -> Callable:
        # Parser for the single JSON‐dict env var flag
        def _parse_json_flag(ctx, param, value):
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                raise click.BadParameter(f"{param.name!r} must be valid JSON: {e}")

        # Parser for list flags
        def _parse_list_flag(ctx, param, value):
            if value is None:
                return None
            # Remove brackets and split by comma
            value = value.strip("[]")
            items = [item.strip() for item in value.split(",") if item.strip()]

            # Convert to integers for elastic_replica_discrete_values
            if param and hasattr(param, 'name') and param.name == 'elastic_replica_discrete_values':
                try:
                    return [int(item) for item in items]
                except ValueError as e:
                    raise click.BadParameter(f"elastic-replica-discrete-values must contain only integers: {e}")

            return items

        def _parse_volume_param(ctx, param, value):
            """Parse volume parameters from command line format to dictionary format."""
            if not value:
                return None
            
            volumes = []
            for i, v in enumerate(value):
                try:
                    # Split by comma and then by equals, with validation
                    parts = {}
                    for item in v.split(','):
                        if '=' not in item:
                            raise click.UsageError(f"Invalid volume format in volume {i+1}: '{item}' should be key=value")
                        key, val = item.split('=', 1)  # Split only on first '=' to handle values with '='
                        parts[key.strip()] = val.strip()
                    
                    volumes.append(parts)
                except Exception as e:
                    raise click.UsageError(f"Error parsing volume {i+1}: {str(e)}")
            
            # Note: Detailed validation will be handled by schema validation
            return volumes
    
        # 1) the wrapper click will call
        def wrapped_func(*args, **kwargs):
            # extract version
            pop_version = kwargs.pop("version", default_version)
            debug = kwargs.pop("debug", False)

            # look up the model class
            Model = registry.get(version)
            if Model is None:
                raise click.ClickException(f"Unsupported schema version: {version}")

            # Filter out None values to avoid passing them to the model
            filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}

            try:
                flat = Model(**filtered_kwargs)
                domain = flat.to_domain()
            except ValidationError as e:
                error_messages = []
                for err in e.errors():
                    loc = ".".join(str(x) for x in err["loc"])
                    msg = err["msg"]
                    error_messages.append(f"  – {loc}: {msg}")
                
                raise click.UsageError(
                    f"❌ Configuration validation errors:\n" + "\n".join(error_messages)
                )

            # call your handler
            return func(version, debug, domain)

        # 2) inject click options from JSON Schema
        excluded_props = set(["version"])
        
        wrapped_func = click.option(
            "--environment",
            callback=_parse_json_flag,
            type=str,
            default=None,
            help=(
                "JSON object of environment variables, e.g. "
                '\'{"VAR1":"foo","VAR2":"bar"}\''
            ),
            metavar="JSON",
        )(wrapped_func)
        wrapped_func = click.option(
            "--label-selector",
            callback=_parse_json_flag,
            help='JSON object of resource limits, e.g. \'{"cpu":"2","memory":"4Gi"}\'',
            metavar="JSON",
        )(wrapped_func)

        wrapped_func = click.option(
            "--volume",
            multiple=True,
            callback=_parse_volume_param,
            help="List of volume configurations. \
                Command structure: --volume name=<volume_name>,type=<volume_type>,mount_path=<mount_path>,<type-specific options> \
                For hostPath: --volume name=model-data,type=hostPath,mount_path=/data,path=/data  \
                For persistentVolumeClaim: --volume name=training-output,type=pvc,mount_path=/mnt/output,claim_name=training-output-pvc,read_only=false \
                If multiple --volume flag if multiple volumes are needed.",
        )(wrapped_func)

        # Add list options
        list_params = {
            "command": "List of command arguments",
            "args": "List of script arguments, e.g. '[--batch-size, 32, --learning-rate, 0.001]'",
            "elastic_replica_discrete_values": "List of discrete replica values for elastic training, e.g. '[2, 4, 8, 16]'",
        }

        for param_name, help_text in list_params.items():
            wrapped_func = click.option(
                f"--{param_name.replace('_', '-')}",
                callback=_parse_list_flag,
                type=str,
                default=None,
                help=help_text,
                metavar="LIST",
            )(wrapped_func)

        excluded_props = set(
            [
                "version",
                "environment",
                "label_selector",
                "command",
                "args",
                "volume",
                "elastic_replica_discrete_values"
            ]
        )

        schema = load_schema_for_version(version, schema_pkg)
        props = schema.get("properties", {})
        reqs = set(schema.get("required", []))

        # reverse so flags appear in the same order as in schema.json
        for name, spec in reversed(list(props.items())):
            if name in excluded_props:
                continue

            # type inference
            if "enum" in spec:
                ctype = click.Choice(spec["enum"])
            elif spec.get("type") == "integer":
                ctype = int
            elif spec.get("type") == "number":
                ctype = float
            elif spec.get("type") == "boolean":
                ctype = bool
            else:
                ctype = str

            wrapped_func = click.option(
                f"--{name.replace('_','-')}",
                required=(name in reqs),
                default=spec.get("default", None),
                show_default=("default" in spec),
                type=ctype,
                help=spec.get("description", ""),
            )(wrapped_func)

        return wrapped_func

    return decorator
