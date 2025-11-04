import json
import pkgutil
import click
from typing import Callable, Optional, Mapping, Type, Dict, Any
from pydantic import ValidationError
from sagemaker.hyperpod.cli.constants.space_constants import IMMUTABLE_FIELDS


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
    schema_pkg: str = "hyperpod_space_template",
    registry: Mapping[str, Type] = None,
    is_update: bool = False,
) -> Callable:
    """
    Decorator factory for space commands.
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

            # Build requests dictionary
            requests = {}
            if cpu is not None:
                requests["cpu"] = cpu
            if memory is not None:
                requests["memory"] = memory
            if gpu is not None:
                requests["nvidia.com/gpu"] = gpu

            # Return ResourceRequirements structure
            return {
                "requests": requests
            }

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
                        # Convert snake_case to match model field names
                        if key.strip() == 'mount_path':
                            key = 'mountPath'
                        elif key.strip() == 'persistent_volume_claim_name':
                            key = 'persistentVolumeClaimName'
                        parts[key.strip()] = val.strip()
                    
                    volumes.append(parts)
                except Exception as e:
                    raise click.UsageError(f"Error parsing volume {i+1}: {str(e)}")
            
            return volumes

        def _parse_storage_param(ctx, param, value):
            """Parse storage parameters from command line format to dictionary format."""
            if not value:
                return None
            
            try:
                parts = {}
                for item in value.split(','):
                    if '=' not in item:
                        raise click.UsageError(f"Invalid storage format: '{item}' should be key=value")
                    key, val = item.split('=', 1)
                    # Convert snake_case to match model field names
                    if key.strip() == 'storage_class_name':
                        key = 'storageClassName'
                    elif key.strip() == 'mount_path':
                        key = 'mountPath'
                    parts[key.strip()] = val.strip()
                return parts
            except Exception as e:
                raise click.UsageError(f"Error parsing storage: {str(e)}")

        def _parse_container_config_param(ctx, param, value):
            """Parse container config parameters from command line format to dictionary format."""
            if not value:
                return None
            
            try:
                parts = {}
                for item in value.split(','):
                    if '=' not in item:
                        raise click.UsageError(f"Invalid container-config format: '{item}' should be key=value")
                    key, val = item.split('=', 1)
                    key = key.strip()
                    val = val.strip()
                    
                    # Handle array fields (command and args)
                    if key in ['command', 'args']:
                        parts[key] = [item.strip() for item in val.split(';') if item.strip()]
                    else:
                        parts[key] = val
                
                return parts
            except Exception as e:
                raise click.UsageError(f"Error parsing container-config: {str(e)}")
    
        # 1) the wrapper click will call
        def wrapped_func(*args, **kwargs):
            version = version_key or kwargs.pop("version", "1.0")

            Model = registry.get(version)
            if Model is None:
                raise click.ClickException(f"Unsupported schema version: {version}")

            resources = _build_resources(kwargs.pop("cpu", None), kwargs.pop("memory", None), kwargs.pop("gpu", None))
            if resources is not None:
                kwargs["resources"] = resources

            volumes = kwargs.pop("volume", None)
            if volumes is not None:
                kwargs["volumes"] = volumes

            storage = kwargs.pop("storage", None)
            if storage is not None:
                kwargs["storage"] = storage

            container_config = kwargs.pop("container_config", None)
            if container_config is not None:
                kwargs["container_config"] = container_config

            # filter out None/empty values so Pydantic model defaults apply
            filtered_kwargs = {}
            for key, value in kwargs.items():
                if value is not None:
                    # Parse JSON for object/array type parameters
                    spec = props.get(key, {})
                    is_object_type = False
                    
                    if spec.get("type") == "object" or spec.get("type") == "array":
                        is_object_type = True
                    elif "anyOf" in spec:
                        # Check if any of the anyOf options is an object/aray type
                        for option in spec["anyOf"]:
                            if option.get("type") == "object" or option.get("type") == "array":
                                is_object_type = True
                                break
                    
                    if isinstance(value, str) and is_object_type:
                        try:
                            value = json.loads(value)
                        except json.JSONDecodeError:
                            raise click.UsageError(f"Invalid JSON for --{key.replace('_', '-')}: {value}")
                    
                    filtered_kwargs[key] = value

            try:
                flat = Model(**filtered_kwargs)
                domain_config = flat.to_domain()
            except ValidationError as e:
                error_messages = []
                for err in e.errors():
                    loc = ".".join(str(x).replace('_','-') for x in err["loc"])
                    msg = err["msg"]
                    error_messages.append(f"  – {loc}: {msg}")
                
                raise click.UsageError(
                    f"Configuration validation errors:\n" + "\n".join(error_messages)
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

        wrapped_func = click.option(
            "--volume",
            multiple=True,
            callback=_parse_volume_param,
            help="Volume configuration. Format: --volume name=<name>,mountPath=<path>,persistentVolumeClaimName=<pvc_name>. Use multiple --volume flags for multiple volumes.",
        )(wrapped_func)

        # Only add storage option if not in update mode as storage is immutable
        if not is_update:
            wrapped_func = click.option(
                "--storage",
                callback=_parse_storage_param,
                help="Storage configuration. Format: --storage storageClassName=<class>,size=<size>,mountPath=<path>",
            )(wrapped_func)

        wrapped_func = click.option(
            "--container-config",
            callback=_parse_container_config_param,
            help="Container configuration. Format: --container-config command=<cmd>,args=<arg1;arg2>",
        )(wrapped_func)

        # Exclude the props that were handled out of the below for loop
        excluded_props = set(
            [
                "resources",
                "version",
                "volumes",
                "storage",
                "container_config",
            ]
        )

        # 3) auto-inject all schema.json fields
        reqs = set(schema.get("required", []))

        # Make display_name optional for update operation
        if is_update and "display_name" in reqs:
            reqs.remove("display_name")

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
            elif spec.get("type") == "object":
                ctype = str  # JSON string input
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
