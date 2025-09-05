import json
import pkgutil
import click
from typing import Callable, Optional, Mapping, Type
import sys
from sagemaker.hyperpod.cli.common_utils import extract_version_from_args, get_latest_version, load_schema_for_version
from sagemaker.hyperpod.cli.parsers import parse_dict_parameter


def generate_click_command(
    *,
    schema_pkg: str = "hyperpod_jumpstart_inference_template",
    registry: Mapping[str, Type] = None,
) -> Callable:
    if registry is None:
        raise ValueError("You must pass a registry mapping version→Model")

    default_version = get_latest_version(registry)
    version = extract_version_from_args(registry, schema_pkg, default_version)

    def decorator(func: Callable) -> Callable:
        # Use unified parser for consistent behavior

        # 1) the wrapper click actually invokes
        def wrapped_func(*args, **kwargs):
            namespace = kwargs.pop("namespace", None)
            name = kwargs.pop("metadata_name", None)
            pop_version = kwargs.pop("version", "1.0")

            Model = registry.get(version)
            if Model is None:
                raise click.ClickException(f"Unsupported schema version: {version}")

            flat = Model(**kwargs)
            domain = flat.to_domain()
            return func(name, namespace, version, domain)

        # 2) inject the special JSON‐env flag before everything else
        schema = load_schema_for_version(version, schema_pkg)
        props = schema.get("properties", {})

        json_flags = {
            "env": "Environment variables. Supports JSON format: '{\"VAR1\":\"foo\",\"VAR2\":\"bar\"}' or simple format: '{VAR1: foo, VAR2: bar}'",
            "dimensions": "Dimensions. Supports JSON format: '{\"VAR1\":\"foo\",\"VAR2\":\"bar\"}' or simple format: '{VAR1: foo, VAR2: bar}'", 
            "resources_limits": "Resource limits. Supports JSON format: '{\"cpu\":\"2\",\"memory\":\"4Gi\"}' or simple format: '{cpu: 2, memory: 4Gi}'",
            "resources_requests": "Resource requests. Supports JSON format: '{\"cpu\":\"1\",\"memory\":\"2Gi\"}' or simple format: '{cpu: 1, memory: 2Gi}'",
        }

        for flag_name, help_text in json_flags.items():
            if flag_name in props:
                wrapped_func = click.option(
                    f"--{flag_name.replace('_', '-')}",
                    callback=parse_dict_parameter,
                    type=str,
                    default=None,
                    help=help_text,
                    metavar="JSON|SIMPLE",
                )(wrapped_func)

        # 3) auto-inject all schema.json fields
        reqs = set(schema.get("required", []))

        for name, spec in reversed(list(props.items())):
            if name in (
                "version",
                "env",
                "dimensions",
                "resources_limits",
                "resources_requests",
            ):
                continue

            # infer click type
            if "enum" in spec:
                ctype = click.Choice(spec["enum"])
            if spec.get("type") == "integer":
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
