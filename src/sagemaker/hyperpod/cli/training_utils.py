import json
import pkgutil
import click
from typing import Callable, Optional, Mapping, Type, Dict, Any
from pydantic import ValidationError
from .parser_utils import parse_complex_parameter


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


def generate_click_command(
    *,
    version_key: Optional[str] = None,
    schema_pkg: str,
    registry: Mapping[str, Type] = None,
) -> Callable:
    """
    Decorator factory that:
      1) Injects click.options from the JSON Schema under `schema_pkg`
      2) At runtime, pops `version`, builds the flat model from `registry`, calls .to_domain()
      3) Finally invokes your handler as `func(version, domain_config)`
    - `version_key`: if given, hard-codes the version (no --version flag injected)
    - `schema_pkg`: the importable package root to read schema.json from
    - `registry`: a dict mapping version → flat‐model class, e.g. hyperpod_pytorch_job_template.registry.SCHEMA_REGISTRY
    """
    if registry is None:
        raise ValueError("You must pass a registry mapping version→Model")

    def decorator(func: Callable) -> Callable:

        # Specific parser functions for different parameter types
        def _parse_list_flag(ctx, param, value):
            """Parse list parameters like --command and --args"""
            return parse_complex_parameter(ctx, param, value, list)
        
        def _parse_dict_flag(ctx, param, value):
            """Parse dictionary parameters like --environment and --label_selector"""
            return parse_complex_parameter(ctx, param, value, dict)
        
        def _parse_volume_param(ctx, param, value):
            """Parse volume parameters (multiple dictionaries)"""
            return parse_complex_parameter(ctx, param, value, dict, allow_multiple=True)
    
        # 1) the wrapper click will call
        def wrapped_func(*args, **kwargs):
            # extract version
            version = version_key or kwargs.pop("version", "1.0")
            debug = kwargs.pop("debug", False)

            # look up the model class
            Model = registry.get(version)
            if Model is None:
                raise click.ClickException(f"Unsupported schema version: {version}")

            try:
                flat = Model(**kwargs)
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
            callback=_parse_dict_flag,
            type=str,
            default=None,
            help=(
                "Dictionary of environment variables, e.g. "
                '"{\'VAR1\': \'foo\', \'VAR2\': \'bar\'}"'
            ),
            metavar="DICT",
        )(wrapped_func)
        wrapped_func = click.option(
            "--label_selector",
            callback=_parse_dict_flag,
            help='Dictionary of resource limits, e.g. "{\'cpu\': \'2\', \'memory\': \'4Gi\'}"',
            metavar="DICT",
        )(wrapped_func)

        wrapped_func = click.option(
            "--volume",
            multiple=True,
            callback=_parse_volume_param,
            help="Volume configurations as dictionaries. \
                Example: --volume \"{\'name\': \'vol1\', \'type\': \'hostPath\', \'mountPath\': \'/data\', \'hostPath\': \'/host\'}\" \
                For hostPath: --volume \"{\'name\': \'model-data\', \'type\': \'hostPath\', \'mountPath\': \'/data\', \'hostPath\': \'/data\'}\"  \
                For persistentVolumeClaim: --volume \"{\'name\': \'training-output\', \'type\': \'pvc\', \'mountPath\': \'/mnt/output\', \'claimName\': \'training-output-pvc\', \'readOnly\': False}\" \
                Use multiple --volume flags if multiple volumes are needed.",
        )(wrapped_func)

        # Add list options
        list_params = {
            "command": "List of command arguments, e.g. \"['python', 'train.py']\"",
            "args": "List of script arguments, e.g. \"['--batch-size', '32', '--learning-rate', '0.001']\"",
        }

        for param_name, help_text in list_params.items():
            wrapped_func = click.option(
                f"--{param_name}",
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
            ]
        )

        schema = load_schema_for_version(version_key or "1.0", schema_pkg)
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

        # 3) if no hard-coded version_key, inject the top-level --version flag
        if version_key is None:
            wrapped_func = click.option(
                "--version",
                default="1.0",
                show_default=True,
                help="Schema version to use",
            )(wrapped_func)

        return wrapped_func

    return decorator
