import json
import pkgutil
import click
import re
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
        def _build_resources(cpu, cpu_limit, memory, memory_limit, gpu, gpu_limit,
            accelerator_partition_type, accelerator_partition_count):
            if not any([cpu, cpu_limit, memory, memory_limit, gpu, gpu_limit,
                accelerator_partition_type, accelerator_partition_count]):
                return None
            
            if (accelerator_partition_type is None) ^ (accelerator_partition_count is None):
                raise click.UsageError(
                    "Both accelerator-partition-type and accelerator-partition-count must be specified together"
                )

            # Build requests dictionary
            requests = {}
            limits = {}
            if cpu is not None:
                requests["cpu"] = cpu
            if cpu_limit is not None:
                limits["cpu"] = cpu_limit
            if memory is not None:
                requests["memory"] = memory
            if memory_limit is not None:
                limits["memory"] = memory_limit
            if gpu is not None:
                requests["nvidia.com/gpu"] = gpu
            if gpu_limit is not None:
                limits["nvidia.com/gpu"] = gpu_limit
            if accelerator_partition_type is not None and accelerator_partition_count is not None:
                if not accelerator_partition_type.startswith("mig"):
                    raise click.UsageError(f"Invalid accelerator partition type '{accelerator_partition_type}'")
                requests[f"nvidia.com/{accelerator_partition_type}"] = accelerator_partition_count
                limits[f"nvidia.com/{accelerator_partition_type}"] = accelerator_partition_count

            # Return ResourceRequirements structure
            return {
                "requests": requests,
                "limits": limits,
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

        def _parse_template_ref(ctx, param, value):
            """Parse template ref from command line format to dictionary format."""
            if not value:
                return None

            try:
                parts = {}
                for item in value.split(','):
                    if '=' not in item:
                        raise click.UsageError(f"Invalid template ref format: '{item}' should be key=value")
                    key, val = item.split('=', 1)
                    parts[key.strip()] = val.strip()
                return parts
            except Exception as e:
                raise click.UsageError(f"Error parsing template ref: {str(e)}")

        def _parse_idle_shutdown_param(ctx, param, value):
            """Parse idle shutdown parameters from command line format to dictionary format."""
            if not value:
                return None

            try:
                parts = {}
                for item in re.split(r',(?![^{]*})', value):
                    if '=' not in item:
                        raise click.UsageError(f"Invalid idle-shutdown format: '{item}' should be key=value")
                    key, val = item.split('=', 1)
                    key = key.strip()
                    val = val.strip()

                    if key == 'idle_timeout_in_minutes':
                        key = 'idleTimeoutInMinutes'
                    elif key == 'enabled':
                        val = val.lower() in ('True', 'true', '1', 'yes')
                    elif key == 'detection':
                        try:
                            val = json.loads(val)
                        except json.JSONDecodeError:
                            raise click.UsageError(f"Invalid JSON for --{key}: {val}")
                    parts[key] = val
                return parts
            except Exception as e:
                raise click.UsageError(f"Error parsing idle-shutdown: {str(e)}")

        # 1) the wrapper click will call
        def wrapped_func(*args, **kwargs):
            version = version_key or kwargs.pop("version", "1.0")
            debug = kwargs.pop("debug", False)

            Model = registry.get(version)
            if Model is None:
                raise click.ClickException(f"Unsupported schema version: {version}")

            resources = _build_resources(
                kwargs.pop("cpu", None),
                kwargs.pop("cpu_limit", None),
                kwargs.pop("memory", None),
                kwargs.pop("memory_limit", None),
                kwargs.pop("gpu", None),
                kwargs.pop("gpu_limit", None),
                kwargs.pop("accelerator_partition_type", None),
                kwargs.pop("accelerator_partition_count", None),
            )
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

            template_ref = kwargs.pop("template_ref", None)
            if template_ref is not None:
                kwargs["template_ref"] = template_ref

            idle_shutdown = kwargs.pop("idle_shutdown", None)
            if idle_shutdown is not None:
                kwargs["idle_shutdown"] = idle_shutdown

            # filter out None/empty values so Pydantic model defaults apply
            filtered_kwargs = {}
            for key, value in kwargs.items():
                # Skip debug parameter as it's not part of the model
                if key == "debug":
                    continue
                    
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

            # For update operations, add temporary display_name if not provided to pass validation
            is_update_and_display_name_not_exist = False
            if is_update and 'display_name' not in filtered_kwargs:
                filtered_kwargs['display_name'] = 'dummy'
                is_update_and_display_name_not_exist = True

            try:
                flat = Model(**filtered_kwargs)
                config_dict = flat.model_dump(exclude_none=True, by_alias=True)
                if is_update_and_display_name_not_exist:
                    config_dict['display_name'] = None
            except ValidationError as e:
                error_messages = []
                for err in e.errors():
                    loc = ".".join(str(x).replace('_','-') for x in err["loc"])
                    msg = err["msg"]
                    error_messages.append(f"  – {loc}: {msg}")
                
                raise click.UsageError(
                    f"Configuration validation errors:\n" + "\n".join(error_messages)
                )

            # Call the original function with appropriate parameters
            import inspect
            sig = inspect.signature(func)
            if 'debug' in sig.parameters:
                return func(version, debug, config_dict)
            else:
                return func(version, config_dict)
        
        # 2) inject click options from JSON Schema
        wrapped_func = click.option(
            "--cpu",
            type=str,
            default=None,
            help="CPU resource request, e.g. '500m'",
        )(wrapped_func)

        wrapped_func = click.option(
            "--cpu-limit",
            type=str,
            default=None,
            help="CPU resource limit, e.g. '500m'",
        )(wrapped_func)

        wrapped_func = click.option(
            "--memory",
            type=str,
            default=None,
            help="Memory resource request, e.g. '2Gi'",
        )(wrapped_func)

        wrapped_func = click.option(
            "--memory-limit",
            type=str,
            default=None,
            help="Memory resource limit, e.g. '2Gi'",
        )(wrapped_func)

        wrapped_func = click.option(
            "--gpu",
            type=str,
            default=None,
            help="GPU resource request, e.g. '1'",
        )(wrapped_func)

        wrapped_func = click.option(
            "--gpu-limit",
            type=str,
            default=None,
            help="GPU resource limit, e.g. '1'",
        )(wrapped_func)

        wrapped_func = click.option(
            "--accelerator-partition-type",
            type=str,
            default=None,
            help="Fractional GPU partition type, e.g. 'mig-3g.20gb'",
        )(wrapped_func)

        wrapped_func = click.option(
            "--accelerator-partition-count",
            type=str,
            default=None,
            help="Fractional GPU partition count, e.g. '1'",
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

        wrapped_func = click.option(
            "--template-ref",
            callback=_parse_template_ref,
            help="TemplateRef references a WorkspaceTemplate to use as base configuration. Format: --template-ref name=<name>,namespace=<namespace>",
        )(wrapped_func)

        wrapped_func = click.option(
            "--idle-shutdown",
            callback=_parse_idle_shutdown_param,
            help="Idle shutdown configuration. Format: --idle-shutdown enabled=<bool>,idleTimeoutInMinutes=<int>,detection=<JSON string>",
        )(wrapped_func)

        # Exclude the props that were handled out of the below for loop
        excluded_props = set(
            [
                "resources",
                "version",
                "volumes",
                "storage",
                "container_config",
                "template_ref",
                "idle_shutdown",
                "debug",  # Exclude debug from validation
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
