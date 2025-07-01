from kubernetes import client
from kubernetes import config as k8s_config
from pydantic import ValidationError
from kubernetes.client.exceptions import ApiException


def validate_cluster_connection():
    try:
        k8s_config.load_kube_config()
        v1 = client.CoreV1Api()
        return True
    except Exception as e:
        return False


def handle_exception(e: Exception, name: str, namespace: str):
    if isinstance(e, ApiException):
        if e.status == 401:
            raise Exception(f"Credentials unauthorized.") from e
        elif e.status == 403:
            raise Exception(
                f"Access denied to resource '{name}' in '{namespace}'."
            ) from e
        if e.status == 404:
            raise Exception(f"Resource '{name}' not found in '{namespace}'.") from e
        elif e.status == 409:
            raise Exception(
                f"Resource '{name}' already exists in '{namespace}'."
            ) from e
        elif 500 <= e.status < 600:
            raise Exception("Kubernetes API internal server error.") from e
        else:
            raise Exception(f"Unhandled Kubernetes error: {e.status} {e.reason}") from e

    if isinstance(e, ValidationError):
        raise Exception("Response did not match expected schema.") from e

    raise e
