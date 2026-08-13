# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import click
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from sagemaker.hyperpod.cli.constants.ray_dashboard_connection_constants import (
    RAY_DASHBOARD_CONNECTION_GROUP,
    RAY_DASHBOARD_CONNECTION_VERSION,
    RAY_DASHBOARD_CONNECTION_PLURAL,
)
from sagemaker.hyperpod.common.telemetry.telemetry_logging import (
    _hyperpod_telemetry_emitter,
)
from sagemaker.hyperpod.common.telemetry.constants import Feature
from sagemaker.hyperpod.common.cli_decorators import handle_cli_exceptions


def _get_eks_api_client():
    """Load kubeconfig and create an authenticated API client.

    Works around a kubernetes-client issue where exec-based tokens
    are not properly forwarded in the Authorization header.
    """
    config.load_kube_config()
    configuration = client.Configuration.get_default_copy()

    # Extract the token from the exec provider
    token = None
    if configuration.api_key and "authorization" in configuration.api_key:
        token_value = configuration.api_key["authorization"]
        prefix = "Bearer "
        if token_value.startswith(prefix):
            token = token_value.removeprefix(prefix)
        else:
            token = token_value

    # Clear api_key to avoid double-auth conflicts
    configuration.api_key = {}
    configuration.api_key_prefix = {}

    if token:
        return client.ApiClient(
            configuration,
            header_name="Authorization",
            header_value=f"Bearer {token}",
        )
    return client.ApiClient(configuration)


@click.command("ray-dashboard-connection")
@click.option("--cluster-name", required=True, help="Name of the RayCluster")
@click.option("--namespace", "-n", required=False, default="default", help="Namespace of the RayCluster")
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "create_ray_dashboard_connection")
@handle_cli_exceptions()
def create_ray_dashboard_connection(cluster_name, namespace):
    """Create a RayDashboardConnection to get a dashboard URL for a RayCluster."""
    api_client = _get_eks_api_client()

    body = {
        "apiVersion": f"{RAY_DASHBOARD_CONNECTION_GROUP}/{RAY_DASHBOARD_CONNECTION_VERSION}",
        "kind": "RayDashboardConnection",
        "metadata": {
            "namespace": namespace,
        },
        "spec": {
            "clusterName": cluster_name,
        },
    }

    api = client.CustomObjectsApi(api_client)

    try:
        result = api.create_namespaced_custom_object(
            group=RAY_DASHBOARD_CONNECTION_GROUP,
            version=RAY_DASHBOARD_CONNECTION_VERSION,
            namespace=namespace,
            plural=RAY_DASHBOARD_CONNECTION_PLURAL,
            body=body,
        )
    except ApiException as e:
        if e.status == 404:
            body_str = e.body or ""
            if "raydashboardconnections" in body_str.lower() or RAY_DASHBOARD_CONNECTION_GROUP in body_str:
                raise click.ClickException(
                    "The RayDashboardConnection API is not available on this cluster.\n"
                    "Please install the hyperpod-ray-endpoint-operator Helm chart.\n"
                )
            raise click.ClickException(f"Not found: {body_str}")
        raise

    connection_url = result.get("status", {}).get("connectionUrl", "")
    if connection_url:
        click.echo(connection_url)
    else:
        raise click.ClickException(
            f"Failed to get dashboard URL for RayCluster '{cluster_name}' in namespace '{namespace}'.\n"
            "Please contact your cluster administrator."
        )
