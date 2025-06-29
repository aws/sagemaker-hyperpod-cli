from kubernetes import client
from kubernetes import config as k8s_config


def validate_cluster_connection():
    try:
        k8s_config.load_kube_config()
        v1 = client.CoreV1Api()
        return True
    except Exception as e:
        return False
