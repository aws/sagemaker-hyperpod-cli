import click
import json
import boto3
from typing import Optional

from hyperpod_cli.inference_utils import generate_click_command
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
@click.option("--version", default="1.0.0", help="Schema version to use")
@generate_click_command(
    schema_pkg="jumpstart_inference_config_schemas",
    registry=JS_REG,
)
def js_create(namespace, version, js_endpoint):
    click.echo(f"✅ Schema {version} verified. Creating endpoint {js_endpoint.model.modelId} with instance type {js_endpoint.server.instanceType}.")
    js_endpoint.create(namespace=namespace)


@click.command("hyp-custom-endpoint")
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the jumpstart model to create. Default set to 'default'",
)
@click.option("--version", default="1.0.0", help="Schema version to use")
@generate_click_command(
    schema_pkg="custom_inference_config_schemas",
    registry=C_REG,
)
def custom_create(namespace, version, custom_endpoint):
    click.echo(f"✅ Schema {version} verified. Creating endpoint {custom_endpoint.modelName} with instance type {custom_endpoint.instanceType}.")
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


#LIST
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
    out = [ep.metadata.model_dump() for ep in endpoints]
    click.echo(json.dumps(out, indent=2))


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
    out = [ep.metadata.model_dump() for ep in endpoints]
    click.echo(json.dumps(out, indent=2))


@click.command("hyp-jumpstart-endpoint")
@click.option(
    "--name",
    type=click.STRING,
    required=True,
    help="Required. The names of the jumpstart model to get.",
)
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the jumpstart model to get. Default set to 'default'.",
)
def js_get(
    name: str,
    namespace: Optional[str],
):
    """
    Get a jumpstart model endpoint with provided name and namespace.
    """

    my_endpoint = HPJumpStartEndpoint.model_construct().get(name, namespace)
    click.echo(json.dumps(my_endpoint.model_dump(), indent=2))


@click.command("hyp-custom-endpoint")
@click.option(
    "--name",
    type=click.STRING,
    required=True,
    help="Required. The names of the custom model to get.",
)
@click.option(
    "--namespace",
    type=click.STRING,
    required=False,
    default="default",
    help="Optional. The namespace of the custom model to get. Default set to 'default'.",
)
def custom_get(
    name: str,
    namespace: Optional[str],
):
    """
    Get a custom model endpoint with provided name and namespace.
    """

    my_endpoint = HPEndpoint.model_construct().get(name, namespace)
    click.echo(json.dumps(my_endpoint.model_dump(), indent=2))


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