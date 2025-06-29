from kubernetes import client
from kubernetes import config as k8s_config


def validate_cluster_connection():
    try:
        k8s_config.load_kube_config()
        v1 = client.CoreV1Api()
        return True
    except Exception as e:
        return False


def remove_metadata(hp_job: dict):
    hp_job.pop("metadata")
    return hp_job


def remove_metadata_from_list(hp_job_list):
    hp_job_list.pop("metadata")
    for hp_job in hp_job_list["items"]:
        hp_job = remove_metadata(hp_job)
    return hp_job_list
