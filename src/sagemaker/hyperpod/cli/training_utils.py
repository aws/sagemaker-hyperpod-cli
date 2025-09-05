import json
import pkgutil
import click
from typing import Callable, Optional, Mapping, Type, Dict, Any
from pydantic import ValidationError
import sys
from sagemaker.hyperpod.cli.common_utils import extract_version_from_args, get_latest_version, load_schema_for_version
from sagemaker.hyperpod.cli.parsers import parse_dict_parameter, parse_list_parameter, parse_complex_object_parameter


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
        # Use unified parsers for consistent behavior across all parameter types
    
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
                domain_config = flat.to_domain()
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
            return func(version, debug, domain_config)

        # 2) inject click options from JSON Schema
        excluded_props = set(["version"])
        
        wrapped_func = click.option(
            "--environment",
            callback=parse_dict_parameter,
            type=str,
            default=None,
            help=(
                "Environment variables. Supports JSON format: "
                '\'{"VAR1":"foo","VAR2":"bar"}\' or simple format: '
                '\'{VAR1: foo, VAR2: bar}\''
            ),
            metavar="JSON|SIMPLE",
        )(wrapped_func)
        wrapped_func = click.option(
            "--label-selector",
            callback=parse_dict_parameter,
            help='Node label selector. Supports JSON format: \'{"cpu":"2","memory":"4Gi"}\' or simple format: \'{cpu: 2, memory: 4Gi}\'',
            metavar="JSON|SIMPLE",
        )(wrapped_func)

        wrapped_func = click.option(
            "--volume",
            multiple=True,
            callback=lambda ctx, param, value: parse_complex_object_parameter(ctx, param, value, allow_multiple=True),
            help="Volume configurations. Supports JSON format: "
                '\'{"name":"vol1","type":"hostPath","mount_path":"/data","path":"/data"}\' '
                "or key-value format: 'name=vol1,type=hostPath,mount_path=/data,path=/data'. "
                "Use multiple --volume flags for multiple volumes.",
        )(wrapped_func)

        # Add list options
        list_params = {
            "command": "Command arguments. Supports JSON format: '[\"python\", \"train.py\"]' or simple format: '[python, train.py]'",
            "args": "Script arguments. Supports JSON format: '[\"--batch-size\", \"32\", \"--learning-rate\", \"0.001\"]' or simple format: '[--batch-size, 32, --learning-rate, 0.001]'",
        }

        for param_name, help_text in list_params.items():
            wrapped_func = click.option(
                f"--{param_name}",
                callback=parse_list_parameter,
                type=str,
                default=None,
                help=help_text,
                metavar="JSON|SIMPLE",
            )(wrapped_func)

        excluded_props = set(
            [
                "version",
                "environment",
                "label_selector",
                "command",
                "args",
                "volume",
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
