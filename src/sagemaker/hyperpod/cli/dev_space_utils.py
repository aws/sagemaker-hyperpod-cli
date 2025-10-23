import json
import pkgutil
import click
from typing import Callable, Optional, Mapping, Type, Dict, Any
from pydantic import ValidationError
from sagemaker.hyperpod.cli.constants.dev_space_constants import IMMUTABLE_FIELDS


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
    schema_pkg: str = "hyperpod_dev_space_template",
    registry: Mapping[str, Type] = None,
    is_update: bool = False,
) -> Callable:
    """
    Decorator factory for dev space commands.
    """
    if registry is None:
        raise ValueError("You must pass a registry mapping version→Model")

    # get schema defaults for manually handled options
    schema = load_schema_for_version(version_key or "1.0", schema_pkg)
    props = schema.get("properties", {})

    def decorator(func: Callable) -> Callable:
        # build resources from CPU/memory options  
        def _build_resources(cpu, memory, gpu):
            if cpu is None and memory is None and gpu is None:
                return None

            default_resources = props["resources"]["default"]
            return {
                "cpu": cpu or default_resources["cpu"],
                "memory": memory or default_resources["memory"],
                "nvidia.com/gpu": gpu or default_resources["nvidia.com/gpu"]
            }
    
        # 1) the wrapper click will call
        def wrapped_func(*args, **kwargs):
            version = version_key or kwargs.pop("version", "1.0")

            Model = registry.get(version)
            if Model is None:
                raise click.ClickException(f"Unsupported schema version: {version}")

            resources = _build_resources(kwargs.pop("cpu", None), kwargs.pop("memory", None), kwargs.pop("gpu", None))
            if resources is not None:
                kwargs["resources"] = resources

            # filter out None/empty values so Pydantic model defaults apply
            filtered_kwargs = {}
            for key, value in kwargs.items():
                if value is not None:
                    filtered_kwargs[key] = value

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

            return func(version, domain_config)
        
        # 2) inject click options from JSON Schema
        wrapped_func = click.option(
            "--cpu",
            type=str,
            default=None,
            help="CPU resource, e.g. '250m'",
        )(wrapped_func)

        wrapped_func = click.option(
            "--memory",
            type=str,
            default=None,
            help="Memory resource, e.g. '256Mi'",
        )(wrapped_func)

        wrapped_func = click.option(
            "--gpu",
            type=str,
            default=None,
            help="Gpu resource, e.g. '1'",
        )(wrapped_func)

        # Exclude the props that were handled out of the below for loop
        excluded_props = set(
            [
                "resources",
                "version",
            ]
        )

        # 3) auto-inject all schema.json fields
        reqs = set(schema.get("required", []))

        for name, spec in reversed(list(props.items())):
            if name in excluded_props:
                continue

            if is_update and name in IMMUTABLE_FIELDS:
                continue

            # infer click type
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
                type=ctype,
                help=spec.get("description", ""),
            )(wrapped_func)

        # 4) if no hard-coded version_key, inject the top-level --version flag
        if version_key is None:
            wrapped_func = click.option(
                "--version",
                default="1.0",
                help="Schema version to use",
            )(wrapped_func)

        return wrapped_func

    return decorator
