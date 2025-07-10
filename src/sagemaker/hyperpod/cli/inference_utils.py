import json
import pkgutil
import click
from typing import Callable, Optional, Mapping, Type


def load_schema_for_version(version: str, schema_pkg: str) -> dict:
    ver_pkg = f"{schema_pkg}.v{version.replace('.', '_')}"
    raw = pkgutil.get_data(ver_pkg, "schema.json")
    if raw is None:
        raise click.ClickException(f"Could not load schema.json for version {version}")
    return json.loads(raw)


def generate_click_command(
    *,
    version_key: Optional[str] = None,
    schema_pkg: str = "hyperpod_jumpstart_inference_template",
    registry: Mapping[str, Type] = None,
) -> Callable:
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

        # 1) the wrapper click actually invokes
        def wrapped_func(*args, **kwargs):
            namespace = kwargs.pop("namespace", None)
            version = version_key or kwargs.pop("version", "1.0")

            Model = registry.get(version)
            if Model is None:
                raise click.ClickException(f"Unsupported schema version: {version}")

            flat = Model(**kwargs)
            domain = flat.to_domain()
            return func(namespace, version, domain)

        # 2) inject the special JSON‐env flag before everything else
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
            "--dimensions",
            callback=_parse_json_flag,
            type=str,
            default=None,
            help=("JSON object of dimensions, e.g. " '\'{"VAR1":"foo","VAR2":"bar"}\''),
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

        # 3) auto-inject all schema.json fields
        schema = load_schema_for_version(version_key or "1.0", schema_pkg)
        props = schema.get("properties", {})
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
