import click
import json
import boto3
from typing import Optional
from tabulate import tabulate

from sagemaker.hyperpod.cli.inference_utils import generate_click_command
from jumpstart_inference_config_schemas.registry import SCHEMA_REGISTRY as JS_REG
from custom_inference_config_schemas.registry import SCHEMA_REGISTRY as C_REG
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint


# CREATE
@click.command("hyp-jumpstart-endpoint")
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the jumpstart model to create. Default set to 'default'",
)
@click.option("--version", default="1.0", help="Schema version to use")
@generate_click_command(
    schema_pkg="jumpstart_inference_config_schemas",
    registry=JS_REG,
)
def js_create(namespace, version, js_endpoint):
    click.echo(
        f"✅ Schema {version} verified. Creating endpoint {js_endpoint.model.modelId} with instance type {js_endpoint.server.instanceType}."
    )
    js_endpoint.create(namespace=namespace)


@click.command("hyp-custom-endpoint")
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the jumpstart model to create. Default set to 'default'",
)
@click.option("--version", default="1.0", help="Schema version to use")
@generate_click_command(
    schema_pkg="custom_inference_config_schemas",
    registry=C_REG,
)
def custom_create(namespace, version, custom_endpoint):
    click.echo(
        f"✅ Schema {version} verified. Creating endpoint {custom_endpoint.modelName} with instance type {custom_endpoint.instanceType}."
    )
    custom_endpoint.create(namespace=namespace)


# INVOKE
@click.command("hyp-custom-endpoint")
@click.option(
    "--endpoint-name",
    type=click.STRING,
    required=True,
    help="Required. The endpoint name of the custom model to invoke.",
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
    Invoke a custom model endpoint.
    """
    try:
        payload = json.dumps(json.loads(body))
    except json.JSONDecodeError:
        raise click.ClickException("--body must be valid JSON")

    rt = boto3.client("sagemaker-runtime")
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
    help="Optional. The namespace of the jumpstart model to list. Default set to 'default'",
)
def js_list(
    namespace: Optional[str],
):
    """
    List jumpstart model endpoints with provided namespace.
    """

    endpoints = HPJumpStartEndpoint.model_construct().list(namespace)
    data = [ep.metadata.model_dump() for ep in endpoints]

    if not data:
        click.echo("No endpoints found")
        return

    headers = ["name", "namespace", "labels"]
    rows = [
        [item.get("name", ""), item.get("namespace", ""), item.get("labels", "")]
        for item in data
    ]
    click.echo(tabulate(rows, headers=headers, tablefmt="github"))


@click.command("hyp-custom-endpoint")
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the Custom model to list. Default set to 'default'",
)
def custom_list(
    namespace: Optional[str],
):
    """
    List Custom model endpoints with provided namespace.
    """

    endpoints = HPEndpoint.model_construct().list(namespace)
    data = [ep.metadata.model_dump() for ep in endpoints]

    if not data:
        click.echo("No endpoints found")
        return

    headers = ["name", "namespace", "labels"]
    rows = [
        [item.get("name", ""), item.get("namespace", ""), item.get("labels", "")]
        for item in data
    ]
    click.echo(tabulate(rows, headers=headers, tablefmt="github"))


@click.command("hyp-jumpstart-endpoint")
@click.option(
    "--name",
    type=click.STRING,
    required=True,
    help="Required. The names of the jumpstart model to describe.",
)
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the jumpstart model to describe. Default set to 'default'.",
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
        summary = [
            ("Deployment State:",       data.get("status", {}).get("deploymentStatus", {}).get("deploymentObjectOverallState")),
            ("Model ID:",               data.get("model", {}).get("modelId")),
            ("Instance Type:",          data.get("server", {}).get("instanceType")),
            ("Accept eula:",            data.get("model", {}).get("acceptEula")),
            ("Model Version:",          data.get("model", {}).get("modelVersion")),
            ("TLS Cert. Output S3 URI:",data.get("tlsConfig", {}).get("tlsCertificateOutputS3Uri")),
        ]
        click.echo(tabulate(summary, tablefmt="plain"))

        click.echo("\nSageMaker Endpoint:")
        ep_rows = [
                ("State:",         data.get("status", {}).get("endpoints", {}).get("sagemaker", {}).get("state")),
                ("Name:",          data.get("sageMakerEndpoint", {}).get("name")),
                ("ARN:",           data.get("status", {}).get("endpoints", {}).get("sagemaker", {}).get("endpointArn")),
        ]
        click.echo(tabulate(ep_rows, tablefmt="plain"))

        click.echo("\nConditions:")
        conds = data.get("status", {}).get("conditions", [])
        if conds:
            headers = ["TYPE", "STATUS", "LAST TRANSITION", "LAST UPDATE", "MESSAGE"]
            rows = [
                [
                    c.get("type", ""),
                    c.get("status", ""),
                    c.get("lastTransitionTime", ""),
                    c.get("lastUpdateTime", ""),
                    c.get("message") or ""
                ]
                for c in conds
            ]
            click.echo(tabulate(rows, headers=headers, tablefmt="github"))
        else:
            click.echo("  <none>")

        click.echo("\nDeploymentStatus Conditions:")
        dep_status = data.get("status", {}).get("deploymentStatus", {})
        dep_conds = dep_status.get("status", {}).get("conditions", [])
        if dep_conds:
            headers = ["TYPE", "STATUS", "LAST TRANSITION", "LAST UPDATE", "MESSAGE"]
            rows = [
                [
                    c.get("type", ""),
                    c.get("status", ""),
                    c.get("lastTransitionTime", ""),
                    c.get("lastUpdateTime", ""),
                    c.get("message") or ""
                ]
                for c in dep_conds
            ]
            click.echo(tabulate(rows, headers=headers, tablefmt="github"))
        else:
            click.echo("  <none>")



@click.command("hyp-custom-endpoint")
@click.option(
    "--name",
    type=click.STRING,
    required=True,
    help="Required. The names of the custom model to describe.",
)
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the custom model to describe. Default set to 'default'.",
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
        summary = [
            ("Deployment State:",           data.get("status", {}).get("deploymentStatus", {}).get("deploymentObjectOverallState")),
            ("Invocation Endpoint",         data.get("invocationEndpoint")),
            ("Instance Type",               data.get("instanceType")),
            ("Metrics Enabled",             data.get("metrics", {}).get("enabled")),
            ("Model Name",                  data.get("modelName")),
            ("Model Version",               data.get("modelVersion")),
            ("Model Source Type",           data.get("modelSourceConfig", {}).get("modelSourceType")),
            ("Model Location",              data.get("modelSourceConfig", {}).get("modelLocation")),
            ("Prefetch Enabled",            data.get("modelSourceConfig", {}).get("prefetchEnabled")),
            ("TLS Cert S3 URI",             data.get("tlsConfig", {}).get("tlsCertificateOutputS3Uri")),
            ("FSx DNS Name",                data.get("modelSourceConfig", {}).get("fsxStorage", {}).get("dnsName")),
            ("FSx File System ID",          data.get("modelSourceConfig", {}).get("fsxStorage", {}).get("fileSystemId")),
            ("FSx Mount Name",              data.get("modelSourceConfig", {}).get("fsxStorage", {}).get("mountName")),
            ("S3 Bucket Name",              data.get("modelSourceConfig", {}).get("s3Storage", {}).get("bucketName")),
            ("S3 Region",                   data.get("modelSourceConfig", {}).get("s3Storage", {}).get("region")),
            ("Image URI",                   data.get("imageUri") 
                                            or data.get("worker", {}).get("image")),
            ("Container Port",              data.get("containerPort")
                                            or data.get("worker", {})
                                                    .get("modelInvocationPort", {})
                                                    .get("containerPort")),
            ("Model Volume Mount Path",     data.get("modelVolumeMountPath")
                                            or data.get("worker", {})
                                                    .get("modelVolumeMount", {})
                                                    .get("mountPath")),
            ("Model Volume Mount Name",     data.get("modelVolumeMountName")
                                            or data.get("worker", {})
                                                    .get("modelVolumeMount", {})
                                                    .get("name")),
            ("Resources Limits",            data.get("resourcesLimits")
                                            or data.get("worker", {})
                                                    .get("resources", {})
                                                    .get("limits")),
            ("Resources Requests",          data.get("resourcesRequests")
                                            or data.get("worker", {})
                                                    .get("resources", {})
                                                    .get("requests")),
            ("Dimensions",                  data.get("dimensions")
                                            or data.get("autoScalingSpec", {})
                                                    .get("cloudWatchTrigger", {})
                                                    .get("dimensions")),
            ("Metric Collection Period",    data.get("metricCollectionPeriod")
                                            or data.get("autoScalingSpec", {})
                                                    .get("cloudWatchTrigger", {})
                                                    .get("metricCollectionPeriod")),
            ("Metric Collection Start Time",data.get("metricCollectionStartTime")
                                            or data.get("autoScalingSpec", {})
                                                    .get("cloudWatchTrigger", {})
                                                    .get("metricCollectionStartTime")),
            ("Metric Name",                 data.get("metricName")
                                            or data.get("autoScalingSpec", {})
                                                    .get("cloudWatchTrigger", {})
                                                    .get("metricName")),
            ("Metric Stat",                 data.get("metricStat")
                                            or data.get("autoScalingSpec", {})
                                                    .get("cloudWatchTrigger", {})
                                                    .get("metricStat")),
            ("Metric Type",                 data.get("metricType")
                                            or data.get("autoScalingSpec", {})
                                                    .get("cloudWatchTrigger", {})
                                                    .get("metricType")),
            ("Min Value",                   data.get("minValue")
                                            or data.get("autoScalingSpec", {})
                                                    .get("cloudWatchTrigger", {})
                                                    .get("minValue")),
            ("CW Trigger Name",             data.get("cloudWatchTriggerName")
                                            or data.get("autoScalingSpec", {})
                                                    .get("cloudWatchTrigger", {})
                                                    .get("name")),
            ("CW Trigger Namespace",        data.get("cloudWatchTriggerNamespace")
                                            or data.get("autoScalingSpec", {})
                                                    .get("cloudWatchTrigger", {})
                                                    .get("namespace")),
            ("Target Value",                data.get("targetValue")
                                            or data.get("autoScalingSpec", {})
                                                    .get("cloudWatchTrigger", {})
                                                    .get("targetValue")),
            ("Use Cached Metrics",          data.get("useCachedMetrics")
                                            or data.get("autoScalingSpec", {})
                                                    .get("cloudWatchTrigger", {})
                                                    .get("useCachedMetrics")),
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
        conds = data.get("status", {}).get("conditions", [])
        if conds:
            headers = ["TYPE", "STATUS", "LAST TRANSITION", "LAST UPDATE", "MESSAGE"]
            rows = [
                [
                    c.get("type", ""),
                    c.get("status", ""),
                    c.get("lastTransitionTime", ""),
                    c.get("lastUpdateTime", ""),
                    c.get("message") or ""
                ]
                for c in conds
            ]
            click.echo(tabulate(rows, headers=headers, tablefmt="github"))
        else:
            click.echo("  <none>")

        click.echo("\nDeploymentStatus Conditions:")
        dep_status = data.get("status", {}).get("deploymentStatus", {})
        dep_conds = dep_status.get("status", {}).get("conditions", [])
        if dep_conds:
            headers = ["TYPE", "STATUS", "LAST TRANSITION", "LAST UPDATE", "MESSAGE"]
            rows = [
                [
                    c.get("type", ""),
                    c.get("status", ""),
                    c.get("lastTransitionTime", ""),
                    c.get("lastUpdateTime", ""),
                    c.get("message") or ""
                ]
                for c in dep_conds
            ]
            click.echo(tabulate(rows, headers=headers, tablefmt="github"))
        else:
            click.echo("  <none>")


@click.command("hyp-jumpstart-endpoint")
@click.option(
    "--name",
    type=click.STRING,
    required=True,
    help="Required. The names of the jumpstart model to delete.",
)
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the jumpstart model to delete. Default set to 'default'.",
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
    click.echo(f"✅ Endpoint {name} deleted.")


@click.command("hyp-custom-endpoint")
@click.option(
    "--name",
    type=click.STRING,
    required=True,
    help="Required. The names of the custom model to delete.",
)
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the custom model to delete. Default set to 'default'.",
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
    click.echo(f"✅ Endpoint {name} deleted.")


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
    Get specific pod log for jumpstart model endpoint.
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
    Get specific pod log for custom model endpoint.
    """
    my_endpoint = HPEndpoint.model_construct()
    logs = my_endpoint.get_operator_logs(since_hours=since_hours)
    click.echo(logs)
