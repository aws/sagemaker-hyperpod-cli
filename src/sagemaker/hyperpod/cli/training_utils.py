import json
import pkgutil
import click
from typing import Callable, Optional, Mapping, Type


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
    schema_pkg: str = "hyperpod_jumpstart_inference_template",
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
            return [item.strip() for item in value.split(",") if item.strip()]

        # 1) the wrapper click will call
        def wrapped_func(*args, **kwargs):
            # extract version
            version = version_key or kwargs.pop("version", "1.0")
            debug = kwargs.pop("debug", False)

            # look up the model class
            Model = registry.get(version)
            if Model is None:
                raise click.ClickException(f"Unsupported schema version: {version}")

            # validate & to_domain
            flat = Model(**kwargs)
            domain_config = flat.to_domain()

            # call your handler
            return func(version, debug, domain_config)

        # 2) inject click options from JSON Schema
        excluded_props = set(["version"])
        if schema_pkg == "hyperpod_jumpstart_inference_template":
            wrapped_func = click.option(
                "--env",
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
                "--resources-limits",
                callback=_parse_json_flag,
                help='JSON object of resource limits, e.g. \'{"cpu":"2","memory":"4Gi"}\'',
                metavar="JSON",
            )(wrapped_func)

            wrapped_func = click.option(
                "--resources-requests",
                callback=_parse_json_flag,
                help='JSON object of resource requests, e.g. \'{"cpu":"1","memory":"2Gi"}\'',
                metavar="JSON",
            )(wrapped_func)

            excluded_props = set(
                ["version", "env", "resources_limits", "resources_requests"]
            )

        elif schema_pkg == "hyperpod_pytorch_job_template":
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
                "--label_selector",
                callback=_parse_json_flag,
                help='JSON object of resource limits, e.g. \'{"cpu":"2","memory":"4Gi"}\'',
                metavar="JSON",
            )(wrapped_func)

            # Add list options
            list_params = {
                "command": "List of command arguments",
                "args": "List of script arguments, e.g. '[--batch-size, 32, --learning-rate, 0.001]'",
                "volumes": "List of volumes, e.g. '[vol1, vol2, vol3]'",
                "persistent_volume_claims": "List of persistent volume claims, e.g. '[pvc1, pvc2]'",
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
                    "volumes",
                    "persistent_volume_claims",
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
