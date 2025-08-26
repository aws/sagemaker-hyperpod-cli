import click
import json
import sys
from typing import Optional, Any
from tabulate import tabulate
from sagemaker.hyperpod.common.cli_decorators import handle_cli_exceptions
from sagemaker.hyperpod.common.lazy_loading import (
    LazyRegistry, LazyDecorator, LazyImportManager, create_critical_deps_loader
)
from sagemaker.hyperpod.cli.command_registry import register_inference_command

# Define what should be available for lazy loading
__all__ = [
    'boto3', 'generate_click_command', 'JS_REG', 'C_REG', 'HPJumpStartEndpoint',
    'HPEndpoint', 'Endpoint', '_hyperpod_telemetry_emitter', 'Feature', 'display_formatted_logs'
]

# Configuration for this module - centralizes template dependencies
_MODULE_CONFIG = {
    'jumpstart_template_package': 'hyperpod_jumpstart_inference_template',
    'custom_template_package': 'hyperpod_custom_inference_template',
    'supported_versions': ['1.0'],  # Conservative: only 1.0 to avoid notebook issues
}

# Critical dependencies for decorators
_CRITICAL_DEPENDENCIES = {
    '_hyperpod_telemetry_emitter': 'sagemaker.hyperpod.common.telemetry.telemetry_logging:_hyperpod_telemetry_emitter',
    'Feature': 'sagemaker.hyperpod.common.telemetry.constants:Feature',
    'generate_click_command': 'sagemaker.hyperpod.cli.inference_utils:generate_click_command',
}

def _setup_inference_registries(deps):
    """Extra setup function to create the inference registries."""
    js_registry = LazyRegistry(
        versions=_MODULE_CONFIG['supported_versions'],
        registry_import_path=f'{_MODULE_CONFIG["jumpstart_template_package"]}.registry:SCHEMA_REGISTRY'
    )
    
    custom_registry = LazyRegistry(
        versions=_MODULE_CONFIG['supported_versions'],
        registry_import_path=f'{_MODULE_CONFIG["custom_template_package"]}.registry:SCHEMA_REGISTRY'
    )
    
    deps['JS_REG'] = js_registry
    deps['C_REG'] = custom_registry
    setattr(sys.modules[__name__], 'JS_REG', js_registry)
    setattr(sys.modules[__name__], 'C_REG', custom_registry)

# Create the critical dependencies loader (but don't call it yet)
_ensure_critical_deps = create_critical_deps_loader(
    dependencies=_CRITICAL_DEPENDENCIES,
    module_name=__name__,
    extra_setup=_setup_inference_registries
)

# Load critical deps immediately for CLI generation decorators
_ensure_critical_deps()

# Lazy import mapping - declarative and template-agnostic
_LAZY_IMPORTS = {
    'boto3': 'boto3',
    'generate_click_command': 'sagemaker.hyperpod.cli.inference_utils:generate_click_command',
    'JS_REG': f'{_MODULE_CONFIG["jumpstart_template_package"]}.registry:SCHEMA_REGISTRY',
    'C_REG': f'{_MODULE_CONFIG["custom_template_package"]}.registry:SCHEMA_REGISTRY',
    'HPJumpStartEndpoint': 'sagemaker.hyperpod.inference.hp_jumpstart_endpoint:HPJumpStartEndpoint',
    'HPEndpoint': 'sagemaker.hyperpod.inference.hp_endpoint:HPEndpoint',
    'Endpoint': 'sagemaker_core.resources:Endpoint',
    '_hyperpod_telemetry_emitter': 'sagemaker.hyperpod.common.telemetry.telemetry_logging:_hyperpod_telemetry_emitter',
    'Feature': 'sagemaker.hyperpod.common.telemetry.constants:Feature',
    'display_formatted_logs': 'sagemaker.hyperpod.common.utils:display_formatted_logs'
}

# Create the lazy import manager
_import_manager = LazyImportManager(_LAZY_IMPORTS)

# Use the manager to create our __getattr__ function
__getattr__ = _import_manager.create_getattr_function(__name__)


# Helper functions to get decorators (these will be lazy loaded)
def _get_telemetry_emitter():
    return _hyperpod_telemetry_emitter

def _get_generate_click_command():
    # Trigger lazy loading via __getattr__
    return getattr(sys.modules[__name__], 'generate_click_command')


# CREATE
@register_inference_command("hyp-jumpstart-endpoint", "create")
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the jumpstart model endpoint to create. Default set to 'default'",
)
@click.option("--version", default="1.0", help="Schema version to use")
@LazyDecorator(_get_generate_click_command,
    schema_pkg=_MODULE_CONFIG["jumpstart_template_package"],
    registry=lambda: sys.modules[__name__].JS_REG,
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "create_js_endpoint_cli")
@handle_cli_exceptions()
def js_create(name, namespace, version, js_endpoint):
    """
    Create a jumpstart model endpoint.
    """

    js_endpoint.create(name=name, namespace=namespace)


@register_inference_command("hyp-custom-endpoint", "create")
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the jumpstart model endpoint to create. Default set to 'default'",
)
@click.option("--version", default="1.0", help="Schema version to use")
@LazyDecorator(_get_generate_click_command,
    schema_pkg=_MODULE_CONFIG["custom_template_package"],
    registry=lambda: sys.modules[__name__].C_REG,
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "create_custom_endpoint_cli")
@handle_cli_exceptions()
def custom_create(name, namespace, version, custom_endpoint):
    """
    Create a custom model endpoint.
    """

    custom_endpoint.create(name=name, namespace=namespace)


# INVOKE
@click.command("hyp-custom-endpoint")
@click.option(
    "--endpoint-name",
    type=click.STRING,
    required=True,
    help="Required. The name of the model endpoint to invoke.",
)
@click.option(
    "--body",
    type=click.STRING,
    required=True,
    help="Required. The body of the request to invoke.",
)
@click.option(
    "--content-type",
    type=click.STRING,
    required=False,
    default="application/json",
    help="Optional. The content type of the request to invoke. Default set to 'application/json'",
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "invoke_custom_endpoint_cli")
@handle_cli_exceptions()
def custom_invoke(
    endpoint_name: str,
    body: str,
    content_type: Optional[str]
):
    """
    Invoke a model endpoint.
    """
    try:
        payload = json.dumps(json.loads(body))
    except json.JSONDecodeError:
        raise click.ClickException("--body must be valid JSON")

    rt = boto3.client("sagemaker-runtime")

    try:
        endpoint = Endpoint.get(endpoint_name)
    except Exception as e:
        endpoint = None

    if endpoint and endpoint.endpoint_status != "InService":
        raise click.ClickException(
            f"Endpoint {endpoint_name} creation has been initated but is currently not in service")
    elif not endpoint:
        try:
            hp_endpoint = HPEndpoint.get(endpoint_name)
        except Exception as e:
            hp_endpoint = None

        if not hp_endpoint:
            raise click.ClickException(f"Endpoint {endpoint_name} not found. Please check the endpoint name input")
        else:
            raise click.ClickException(f"Job has been initiated but the Endpoint is not created yet. Please check logs or wait and try again later")

    resp = rt.invoke_endpoint(
        EndpointName=endpoint_name,
        Body=payload.encode("utf-8"),
        ContentType=content_type,
    )
    result = resp["Body"].read().decode("utf-8")
    click.echo(result)


# LIST
@click.command("hyp-jumpstart-endpoint")
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the jumpstart model endpoint to list. Default set to 'default'",
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "list_js_endpoints_cli")
@handle_cli_exceptions()
def js_list(
    namespace: Optional[str],
):
    """
    List all Hyperpod Jumpstart model endpoints.
    """
    endpoints = HPJumpStartEndpoint.model_construct().list(namespace)
    data = [ep.model_dump() for ep in endpoints]

    if not data:
        click.echo("No endpoints found")
        return

    headers = ["name", "namespace", "labels", "status"]
    rows = []
    for item in data:
        if not isinstance(item, dict):
            continue

        metadata = item.get("metadata") or {}
        status = item.get("status") or {}
        deployment_status = status.get("deploymentStatus") or {}

        row = [
            metadata.get("name", ""),
            metadata.get("namespace", ""),
            metadata.get("labels", ""),
            deployment_status.get("deploymentObjectOverallState", "")
        ]
        rows.append(row)
    click.echo(tabulate(rows, headers=headers, tablefmt="github"))


@click.command("hyp-custom-endpoint")
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the custom model endpoint to list. Default set to 'default'",
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "list_custom_endpoints_cli")
@handle_cli_exceptions()
def custom_list(
    namespace: Optional[str],
):
    """
    List all Hyperpod custom model endpoints.
    """
    endpoints = HPEndpoint.model_construct().list(namespace)
    data = [ep.model_dump() for ep in endpoints]

    if not data:
        click.echo("No endpoints found")
        return

    headers = ["name", "namespace", "labels", "status"]
    rows = []
    for item in data:
        if not isinstance(item, dict):
            continue

        metadata = item.get("metadata") or {}
        status = item.get("status") or {}
        deployment_status = status.get("deploymentStatus") or {}

        row = [
            metadata.get("name", ""),
            metadata.get("namespace", ""),
            metadata.get("labels", ""),
            deployment_status.get("deploymentObjectOverallState", "")
        ]
        rows.append(row)
    click.echo(tabulate(rows, headers=headers, tablefmt="github"))


@click.command("hyp-jumpstart-endpoint")
@click.option(
    "--name",
    type=click.STRING,
    required=True,
    help="Required. The name of the jumpstart model endpoint to describe.",
)
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the jumpstart model endpoint to describe. Default set to 'default'.",
)
@click.option(
    "--full",
    type=click.BOOL,
    is_flag=True,
    default=False,
    required=False,
    help="Optional. If set to `True`, the full json will be displayed",
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "get_js_endpoint_cli")
@handle_cli_exceptions()
def js_describe(
    name: str,
    namespace: Optional[str],
    full: bool
):
    """
    Describe a Hyperpod Jumpstart model endpoint.
    """
    my_endpoint = HPJumpStartEndpoint.model_construct().get(name, namespace)
    data = my_endpoint.model_dump()

    if full:
        click.echo("\nFull JSON:")
        click.echo(json.dumps(data, indent=2))

    else:
        if not isinstance(data, dict):
            click.echo("Invalid data received: expected a dictionary.")
            return
        
        click.echo("\nDeployment (should be completed in 1-5 min):")
    
        status = data.get("status") or {}
        metadata = data.get("metadata") or {}
        model = data.get("model") or {}
        server = data.get("server") or {}
        tls = data.get("tlsConfig") or {}

        raw_state = status.get("deploymentStatus", {}) \
                        .get("deploymentObjectOverallState", "") or ""
        if raw_state == "DeploymentComplete":
            fg = "green"
        elif raw_state == "DeploymentInProgress":
            fg = "yellow"
        else:
            fg = "red"
        colored_state = click.style(raw_state, fg=fg, bold=True)

        summary = [
            ("Status:",                 colored_state),
            ("Metadata Name:",          metadata.get("name", "")),
            ("Namespace:",              metadata.get("namespace", "")),
            ("Label:",                  metadata.get("label", "")),
            ("Model ID:",               model.get("modelId", "")),
            ("Instance Type:",          server.get("instanceType", "")),
            ("Accept eula:",            model.get("acceptEula", "")),
            ("Model Version:",          model.get("modelVersion", "")),
            ("TLS Cert. Output S3 URI:",tls.get("tlsCertificateOutputS3Uri", "")),
        ]
        click.echo(tabulate(summary, tablefmt="plain"))

        click.echo("\nDeployment Status Conditions:")

        status = data.get("status") if isinstance(data, dict) else {}
        status = status or {}

        deployment_status = status.get("deploymentStatus") or {}
        dep_status_inner = deployment_status.get("status") or {}
        dep_conds = dep_status_inner.get("conditions") or []

        if isinstance(dep_conds, list) and dep_conds:
            headers = ["TYPE", "STATUS", "LAST TRANSITION", "LAST UPDATE", "MESSAGE"]
            rows = [
                [
                    c.get("type", ""),
                    c.get("status", ""),
                    c.get("lastTransitionTime", ""),
                    c.get("lastUpdateTime", ""),
                    c.get("message") or ""
                ]
                for c in dep_conds if isinstance(c, dict)
            ]
            click.echo(tabulate(rows, headers=headers, tablefmt="github"))
        else:
            click.echo("  <none>")

        click.echo() 
        click.echo(click.style("─" * 60, fg="white"))
        
        click.echo("\nSageMaker Endpoint (takes ~10 min to create):")
        status     = data.get("status")     or {}
        endpoints  = status.get("endpoints") or {}
        sagemaker_info = endpoints.get("sagemaker")

        if not sagemaker_info:
            click.secho("  <no SageMaker endpoint information available>", fg="yellow")
        else:
            raw_state = sagemaker_info.get("state", "") or ""
            if raw_state == "CreationCompleted":
                fg = "green"
            elif raw_state == "CreationInProgress":
                fg = "yellow"
            else:
                fg = "red"
            colored_state = click.style(raw_state, fg=fg, bold=True)
            ep_rows = [
                    ("Status:",         colored_state),
                    ("Name:",          data.get("sageMakerEndpoint", {}).get("name")),
                    ("ARN:",           sagemaker_info.get("endpointArn")),
            ]
            click.echo(tabulate(ep_rows, tablefmt="plain"))

        click.echo("\nSagemaker Endpoint Status Conditions:")

        status = data.get("status") if isinstance(data, dict) else {}
        status = status or {}  
        conds = status.get("conditions", [])

        if isinstance(conds, list) and conds:
            headers = ["TYPE", "STATUS", "LAST TRANSITION", "LAST UPDATE", "MESSAGE"]
            rows = [
                [
                    c.get("type", ""),
                    c.get("status", ""),
                    c.get("lastTransitionTime", ""),
                    c.get("lastUpdateTime", ""),
                    c.get("message") or ""
                ]
                for c in conds if isinstance(c, dict)
            ]
            click.echo(tabulate(rows, headers=headers, tablefmt="github"))
        else:
            click.echo("  <none>")


@click.command("hyp-custom-endpoint")
@click.option(
    "--name",
    type=click.STRING,
    required=True,
    help="Required. The name of the custom model endpoint to describe.",
)
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the custom model endpoint to describe. Default set to 'default'.",
)
@click.option(
    "--full",
    type=click.BOOL,
    is_flag=True,
    default=False,
    required=False,
    help="Optional. If set to `True`, the full json will be displayed",
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "get_custom_endpoint_cli")
@handle_cli_exceptions()
def custom_describe(
    name: str,
    namespace: Optional[str],
    full: bool
):
    """
    Describe a Hyperpod custom model endpoint.
    """
    my_endpoint = HPEndpoint.model_construct().get(name, namespace)
    data = my_endpoint.model_dump()

    if full:
        click.echo("\nFull JSON:")
        click.echo(json.dumps(data, indent=2))

    else:
        if not isinstance(data, dict):
            click.echo("Invalid data received: expected a dictionary.")
            return

        click.echo("\nDeployment (should be completed in 1-5 min):")

        status = data.get("status") or {}
        metadata = data.get("metadata") or {}
        metrics = data.get("metrics") or {}
        model_source = data.get("modelSourceConfig") or {}
        s3_storage = model_source.get("s3Storage") or {}
        fsx_storage = model_source.get("fsxStorage") or {}
        tls = data.get("tlsConfig") or {}
        worker = data.get("worker") or {}
        resources = worker.get("resources") or {}
        volume_mount = worker.get("modelVolumeMount") or {}
        model_port = worker.get("modelInvocationPort") or {}
        cloudwatch = data.get("autoScalingSpec", {}).get("cloudWatchTrigger") or {}

        raw_state = status.get("deploymentStatus", {}) \
                        .get("deploymentObjectOverallState", "") or ""
        if raw_state == "DeploymentComplete":
            fg = "green"
        elif raw_state == "DeploymentInProgress":
            fg = "yellow"
        else:
            fg = "red"
        colored_state = click.style(raw_state, fg=fg, bold=True)

        summary = [
            ("Deployment State:",           colored_state),
            ("Metadata Name:",              metadata.get("name", "")),
            ("Namespace:",                  metadata.get("namespace", "")),
            ("Label:",                      metadata.get("label", "")),
            ("Invocation Endpoint",         data.get("invocationEndpoint", "")),
            ("Instance Type",               data.get("instanceType", "")),
            ("Metrics Enabled",             metrics.get("enabled", "")),
            ("Model Name",                  data.get("modelName", "")),
            ("Model Version",               data.get("modelVersion", "")),
            ("Model Source Type",           model_source.get("modelSourceType", "")),
            ("Model Location",              model_source.get("modelLocation", "")),
            ("Prefetch Enabled",            model_source.get("prefetchEnabled", "")),
            ("TLS Cert S3 URI",             tls.get("tlsCertificateOutputS3Uri", "")),
            ("FSx DNS Name",                fsx_storage.get("dnsName", "")),
            ("FSx File System ID",          fsx_storage.get("fileSystemId", "")),
            ("FSx Mount Name",              fsx_storage.get("mountName", "")),
            ("S3 Bucket Name",              s3_storage.get("bucketName", "")),
            ("S3 Region",                   s3_storage.get("region", "")),
            ("Image URI",                   data.get("imageUri") or worker.get("image", "")),
            ("Container Port",              data.get("containerPort") or model_port.get("containerPort", "")),
            ("Model Volume Mount Path",     data.get("modelVolumeMountPath") or volume_mount.get("mountPath", "")),
            ("Model Volume Mount Name",     data.get("modelVolumeMountName") or volume_mount.get("name", "")),
            ("Resources Limits",            data.get("resourcesLimits") or resources.get("limits", "")),
            ("Resources Requests",          data.get("resourcesRequests") or resources.get("requests", "")),
            ("Dimensions",                  data.get("dimensions") or cloudwatch.get("dimensions", "")),
            ("Metric Collection Period",    data.get("metricCollectionPeriod") or cloudwatch.get("metricCollectionPeriod", "")),
            ("Metric Collection Start Time",data.get("metricCollectionStartTime") or cloudwatch.get("metricCollectionStartTime", "")),
            ("Metric Name",                 data.get("metricName") or cloudwatch.get("metricName", "")),
            ("Metric Stat",                 data.get("metricStat") or cloudwatch.get("metricStat", "")),
            ("Metric Type",                 data.get("metricType") or cloudwatch.get("metricType", "")),
            ("Min Value",                   data.get("minValue") or cloudwatch.get("minValue", "")),
            ("CW Trigger Name",             data.get("cloudWatchTriggerName") or cloudwatch.get("name", "")),
            ("CW Trigger Namespace",        data.get("cloudWatchTriggerNamespace") or cloudwatch.get("namespace", "")),
            ("Target Value",                data.get("targetValue") or cloudwatch.get("targetValue", "")),
            ("Use Cached Metrics",          data.get("useCachedMetrics") or cloudwatch.get("useCachedMetrics", "")),
        ]

        click.echo(tabulate(summary, tablefmt="plain"))

        click.echo("\nDeployment Status Conditions:")

        status = data.get("status") if isinstance(data, dict) else {}
        status = status or {}

        deployment_status = status.get("deploymentStatus") or {}
        dep_status_inner = deployment_status.get("status") or {}
        dep_conds = dep_status_inner.get("conditions") or []

        if isinstance(dep_conds, list) and dep_conds:
            headers = ["TYPE", "STATUS", "LAST TRANSITION", "LAST UPDATE", "MESSAGE"]
            rows = [
                [
                    c.get("type", ""),
                    c.get("status", ""),
                    c.get("lastTransitionTime", ""),
                    c.get("lastUpdateTime", ""),
                    c.get("message") or ""
                ]
                for c in dep_conds if isinstance(c, dict)
            ]
            click.echo(tabulate(rows, headers=headers, tablefmt="github"))
        else:
            click.echo("  <none>")

        click.echo() 
        click.echo(click.style("─" * 60, fg="white"))
        
        click.echo("\nSageMaker Endpoint (takes ~10 min to create):")
        status     = data.get("status")     or {}
        endpoints  = status.get("endpoints") or {}
        sagemaker_info = endpoints.get("sagemaker")

        if not sagemaker_info:
            click.secho("  <no SageMaker endpoint information available>", fg="yellow")
        else:
            raw_state = sagemaker_info.get("state", "") or ""
            if raw_state == "CreationCompleted":
                fg = "green"
            elif raw_state == "CreationInProgress":
                fg = "yellow"
            else:
                fg = "red"
            colored_state = click.style(raw_state, fg=fg, bold=True)
            ep_rows = [
                    ("Status:",         colored_state),
                    ("Name:",          data.get("sageMakerEndpoint", {}).get("name")),
                    ("ARN:",           sagemaker_info.get("endpointArn")),
            ]
            click.echo(tabulate(ep_rows, tablefmt="plain"))

        click.echo("\nSagemaker Endpoint Status Conditions:")

        status = data.get("status") if isinstance(data, dict) else {}
        status = status or {}  
        conds = status.get("conditions", [])

        if isinstance(conds, list) and conds:
            headers = ["TYPE", "STATUS", "LAST TRANSITION", "LAST UPDATE", "MESSAGE"]
            rows = [
                [
                    c.get("type", ""),
                    c.get("status", ""),
                    c.get("lastTransitionTime", ""),
                    c.get("lastUpdateTime", ""),
                    c.get("message") or ""
                ]
                for c in conds if isinstance(c, dict)
            ]
            click.echo(tabulate(rows, headers=headers, tablefmt="github"))
        else:
            click.echo("  <none>")


@click.command("hyp-jumpstart-endpoint")
@click.option(
    "--name",
    type=click.STRING,
    required=True,
    help="Required. The name of the jumpstart model endpoint to delete.",
)
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the jumpstart model endpoint to delete. Default set to 'default'.",
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "delete_js_endpoint_cli")
@handle_cli_exceptions()
def js_delete(
    name: str,
    namespace: Optional[str],
):
    """
    Delete a Hyperpod Jumpstart model endpoint.
    """
    # Auto-detects the endpoint type and operation
    # 0Provides 404 message: "❓ JumpStart endpoint 'missing-name' not found..."
    my_endpoint = HPJumpStartEndpoint.model_construct().get(name, namespace)
    my_endpoint.delete()


@click.command("hyp-custom-endpoint")
@click.option(
    "--name",
    type=click.STRING,
    required=True,
    help="Required. The names of the custom model endpoint to delete.",
)
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the custom model endpoint to delete. Default set to 'default'.",
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "delete_custom_endpoint_cli")
@handle_cli_exceptions()
def custom_delete(
    name: str,
    namespace: Optional[str],
):
    """
    Delete a Hyperpod custom model endpoint.
    """
    my_endpoint = HPEndpoint.model_construct().get(name, namespace)
    my_endpoint.delete()


@click.command("hyp-jumpstart-endpoint")
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the jumpstart model to list pods for. Default set to 'default'.",
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "list_pods_js_endpoint_cli")
@handle_cli_exceptions()
def js_list_pods(
    namespace: Optional[str],
):
    """
    List all pods related to jumpstart model endpoint.
    """
    my_endpoint = HPJumpStartEndpoint.model_construct()
    pods = my_endpoint.list_pods(namespace=namespace)
    click.echo(pods)


@click.command("hyp-custom-endpoint")
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the custom model to list pods for. Default set to 'default'.",
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "list_pods_custom_endpoint_cli")
@handle_cli_exceptions()
def custom_list_pods(
    namespace: Optional[str],
):
    """
    List all pods related to custom model endpoint.
    """
    my_endpoint = HPEndpoint.model_construct()
    pods = my_endpoint.list_pods(namespace=namespace)
    click.echo(pods)


@register_inference_command("hyp-jumpstart-endpoint", "get-logs")
@click.option(
    "--pod-name",
    type=click.STRING,
    required=True,
    help="Required. The pod name to get logs for.",
)
@click.option(
    "--container",
    type=click.STRING,
    required=False,
    help="Optional. The container name to get logs for.",
)
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the jumpstart model to get logs for. Default set to 'default'.",
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "get_logs_js_endpoint")
@handle_cli_exceptions()
def js_get_logs(
    pod_name: str,
    container: Optional[str],
    namespace: Optional[str],
):
    """
    Get specific pod log for jumpstart model endpoint.
    """
    my_endpoint = HPJumpStartEndpoint.model_construct()
    logs = my_endpoint.get_logs(pod=pod_name, container=container, namespace=namespace)
    
    # Use common log display utility for consistent formatting across all job types
    container_info = f" (container: {container})" if container else ""
    display_formatted_logs(logs, title=f"JumpStart Endpoint Logs for {pod_name}{container_info}")


@register_inference_command("hyp-custom-endpoint", "get-logs")
@click.option(
    "--pod-name",
    type=click.STRING,
    required=True,
    help="Required. The pod name to get logs for.",
)
@click.option(
    "--container",
    type=click.STRING,
    required=False,
    help="Optional. The container name to get logs for.",
)
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the custom model to get logs for. Default set to 'default'.",
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "get_logs_custom_endpoint")
@handle_cli_exceptions()
def custom_get_logs(
    pod_name: str,
    container: Optional[str],
    namespace: Optional[str],
):
    """
    Get specific pod log for custom model endpoint.
    """
    my_endpoint = HPEndpoint.model_construct()
    logs = my_endpoint.get_logs(pod=pod_name, container=container, namespace=namespace)
    
    # Use common log display utility for consistent formatting across all job types
    container_info = f" (container: {container})" if container else ""
    display_formatted_logs(logs, title=f"Custom Endpoint Logs for {pod_name}{container_info}")


@click.command("hyp-jumpstart-endpoint")
@click.option(
    "--since-hours",
    type=click.FLOAT,
    required=True,
    help="Required. The time frame to get logs for.",
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "get_js_operator_logs")
@handle_cli_exceptions()
def js_get_operator_logs(
    since_hours: float,
):
    """
    Get operator logs for jumpstart model endpoint.
    """
    my_endpoint = HPJumpStartEndpoint.model_construct()
    logs = my_endpoint.get_operator_logs(since_hours=since_hours)
    click.echo(logs)


@click.command("hyp-custom-endpoint")
@click.option(
    "--since-hours",
    type=click.FLOAT,
    required=True,
    help="Required. The time frame get logs for.",
)
@LazyDecorator(_get_telemetry_emitter, lambda: sys.modules[__name__].Feature.HYPERPOD_CLI, "get_custom_operator_logs")
@handle_cli_exceptions()
def custom_get_operator_logs(
    since_hours: float,
):
    """
    Get operator logs for custom model endpoint.
    """
    my_endpoint = HPEndpoint.model_construct()
    logs = my_endpoint.get_operator_logs(since_hours=since_hours)
    click.echo(logs)
