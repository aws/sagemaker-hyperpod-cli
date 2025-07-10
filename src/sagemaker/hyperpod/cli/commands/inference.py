import click
import json
import boto3
from typing import Optional
from tabulate import tabulate

from sagemaker.hyperpod.cli.inference_utils import generate_click_command
from hyperpod_jumpstart_inference_template.registry import SCHEMA_REGISTRY as JS_REG
from hyperpod_custom_inference_template.registry import SCHEMA_REGISTRY as C_REG
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint
from sagemaker_core.resources import Endpoint


# CREATE
@click.command("hyp-jumpstart-endpoint")
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the jumpstart model endpoint to create. Default set to 'default'",
)
@click.option("--version", default="1.0", help="Schema version to use")
@generate_click_command(
    schema_pkg="hyperpod_jumpstart_inference_template",
    registry=JS_REG,
)
def js_create(namespace, version, js_endpoint):
    """
    Create a jumpstart model endpoint.
    """

    js_endpoint.create(namespace=namespace)


@click.command("hyp-custom-endpoint")
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the jumpstart model endpoint to create. Default set to 'default'",
)
@click.option("--version", default="1.0", help="Schema version to use")
@generate_click_command(
    schema_pkg="hyperpod_custom_inference_template",
    registry=C_REG,
)
def custom_create(namespace, version, custom_endpoint):
    """
    Create a custom model endpoint.
    """

    custom_endpoint.create(namespace=namespace)


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
def custom_invoke(
    endpoint_name: str,
    body: str,
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
        ContentType="application/json",
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
def js_list(
    namespace: Optional[str],
):
    """
    List jumpstart model endpoints with provided namespace.
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
def custom_list(
    namespace: Optional[str],
):
    """
    List custom model endpoints with provided namespace.
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
def js_describe(
    name: str,
    namespace: Optional[str],
    full: bool
):
    """
    Describe a jumpstart model endpoint with provided name and namespace.
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

        status = data.get("status") or {}
        metadata = data.get("metadata") or {}
        model = data.get("model") or {}
        server = data.get("server") or {}
        tls = data.get("tlsConfig") or {}

        summary = [
            ("Deployment State:",       status.get("deploymentStatus", {}).get("deploymentObjectOverallState", "")),
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

        click.echo("\nSageMaker Endpoint:")
        status     = data.get("status")     or {}
        endpoints  = status.get("endpoints") or {}
        sagemaker_info = endpoints.get("sagemaker")
        if not sagemaker_info:
            click.secho("  <no SageMaker endpoint information available>", fg="yellow")
        else:
            ep_rows = [
                    ("State:",         data.get("status", {}).get("endpoints", {}).get("sagemaker", {}).get("state")),
                    ("Name:",          data.get("sageMakerEndpoint", {}).get("name")),
                    ("ARN:",           data.get("status", {}).get("endpoints", {}).get("sagemaker", {}).get("endpointArn")),
            ]
            click.echo(tabulate(ep_rows, tablefmt="plain"))

        click.echo("\nConditions:")

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

        click.echo("\nDeploymentStatus Conditions:")

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
def custom_describe(
    name: str,
    namespace: Optional[str],
    full: bool
):
    """
    Describe a custom model endpoint with provided name and namespace.
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

        # Safe access blocks
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

        summary = [
            ("Deployment State:",           status.get("deploymentStatus", {}).get("deploymentObjectOverallState", "")),
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

        click.echo("\nSageMaker Endpoint:")
        sm_endpoints = status.get("endpoints") or {}
        sagemaker_info = sm_endpoints.get("sagemaker")
        if not sagemaker_info:
            click.secho("  <no SageMaker endpoint information available>", fg="yellow")
        else:
            ep_rows = [
                ("State:", sm_endpoints.get("sagemaker", {}).get("state", "")),
                ("Name:", data.get("sageMakerEndpoint", {}).get("name", "")),
                ("ARN:", sm_endpoints.get("sagemaker", {}).get("endpointArn", "")),
            ]
            click.echo(tabulate(ep_rows, tablefmt="plain"))

        click.echo("\nConditions:")
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

        click.echo("\nDeploymentStatus Conditions:")
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
def js_delete(
    name: str,
    namespace: Optional[str],
):
    """
    Delete a jumpstart model endpoint with provided name and namespace.
    """
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
def custom_delete(
    name: str,
    namespace: Optional[str],
):
    """
    Delete a custom model endpoint with provided name and namespace.
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
def js_list_pods(
    namespace: Optional[str],
):
    """
    Get specific pod log for jumpstart model endpoint.
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
def custom_list_pods(
    namespace: Optional[str],
):
    """
    Get specific pod log for custom model endpoint.
    """
    my_endpoint = HPEndpoint.model_construct()
    pods = my_endpoint.list_pods(namespace=namespace)
    click.echo(pods)


@click.command("hyp-jumpstart-endpoint")
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
    click.echo(logs)


@click.command("hyp-custom-endpoint")
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
    click.echo(logs)


@click.command("hyp-jumpstart-endpoint")
@click.option(
    "--since-hours",
    type=click.FLOAT,
    required=True,
    help="Required. The time frame to get logs for.",
)
def js_get_operator_logs(
    since_hours: float,
):
    """
    Get operator logs for jumpstart model endpoint in the set time frame.
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
def custom_get_operator_logs(
    since_hours: float,
):
    """
    Get operator logs for custom model endpoint in the set time frame.
    """
    my_endpoint = HPEndpoint.model_construct()
    logs = my_endpoint.get_operator_logs(since_hours=since_hours)
    click.echo(logs)
