from pydantic import ConfigDict, Field, ValidationError
from pydantic import BaseModel, ConfigDict, Field
from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_config import (
    _HyperPodPytorchJob,
)
from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_status import (
    HyperPodPytorchJobStatus,
)
from sagemaker.hyperpod.inference.config.common import Metadata
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from typing import List, Optional
from sagemaker.hyperpod.common.utils import (
    validate_cluster_connection,
    handel_exception,
)
import yaml
import logging

TRAINING_GROUP = "sagemaker.amazonaws.com"
API_VERSION = "v1"
PLURAL = "hyperpodpytorchjobs"
KIND = "HyperPodPyTorchJob"


class HyperPodPytorchJob(_HyperPodPytorchJob):
    model_config = ConfigDict(extra="forbid")

    metadata: Metadata = Field(
        description="The metadata of the HyperPodPytorchJob",
    )

    status: Optional[HyperPodPytorchJobStatus] = Field(
        default=None, description="The status of the HyperPodPytorchJob"
    )

    def create(self, debug=False):
        if not validate_cluster_connection():
            raise Exception(
                "Failed to connect to the Kubernetes cluster. Please check your kubeconfig."
            )

        if debug:
            logging.basicConfig(level=logging.DEBUG)

        spec = _HyperPodPytorchJob(**self.model_dump(by_alias=True, exclude_none=True))

        config = {
            "apiVersion": f"{TRAINING_GROUP}/{API_VERSION}",
            "kind": KIND,
            "metadata": self.metadata.model_dump(),
            "spec": spec.model_dump(),
        }

        custom_api = client.CustomObjectsApi()
        logging.debug(
            "Deploying HyperPodPytorchJob with config:\n",
            yaml.dump(config),
            sep="",
        )

        try:
            custom_api.create_namespaced_custom_object(
                group=TRAINING_GROUP,
                version=API_VERSION,
                namespace=self.metadata.namespace,
                plural=PLURAL,
                body=config,
            )
            logging.debug("Successful submitted HyperPodPytorchJob!")
        except Exception as e:
            logging.debug(f"Failed to create HyperPodPytorchJob {self.metadata.name}!")
            handel_exception(e, self.metadata.name, self.metadata.namespace)

    @classmethod
    def list(cls, namespace="default") -> List["HyperPodPytorchJob"]:
        if not validate_cluster_connection():
            raise Exception(
                "Failed to connect to the Kubernetes cluster. Please check your kubeconfig."
            )

        custom_api = client.CustomObjectsApi()

        try:
            hp_job_list = custom_api.list_namespaced_custom_object(
                group=TRAINING_GROUP,
                version=API_VERSION,
                namespace=namespace,
                plural=PLURAL,
            )
            return _load_hp_job_list(hp_job_list)
        except Exception as e:
            logging.debug(f"Failed to list HyperpodPytorchJobs!")
            handel_exception(e, "", namespace)

    def delete(self):
        if not validate_cluster_connection():
            raise Exception(
                "Failed to connect to the Kubernetes cluster. Please check your kubeconfig."
            )

        custom_api = client.CustomObjectsApi()

        try:
            custom_api.delete_namespaced_custom_object(
                group=TRAINING_GROUP,
                version=API_VERSION,
                namespace=self.metadata.namespace,
                plural=PLURAL,
                name=self.metadata.name,
            )
            logging.debug(f"Successful deleted HyperPodPytorchJob!")
        except Exception as e:
            logging.debug(f"Failed to delete HyperPodPytorchJob {self.metadata.name}!")
            handel_exception(e, self.metadata.name, self.metadata.namespace)

    @classmethod
    def get(cls, name, namespace="default") -> "HyperPodPytorchJob":
        if not validate_cluster_connection():
            raise Exception(
                "Failed to connect to the Kubernetes cluster. Please check your kubeconfig."
            )

        custom_api = client.CustomObjectsApi()

        try:
            response = custom_api.get_namespaced_custom_object(
                group=TRAINING_GROUP,
                version=API_VERSION,
                namespace=namespace,
                plural=PLURAL,
                name=name,
            )
            return _load_hp_job(response)
        except Exception as e:
            logging.debug(f"Failed to describe HyperPodPytorchJob {name}: {e}")
            handel_exception(e, name, namespace)

    def refresh(self) -> "HyperPodPytorchJob":
        if not validate_cluster_connection():
            raise Exception(
                "Failed to connect to the Kubernetes cluster. Please check your kubeconfig."
            )

        custom_api = client.CustomObjectsApi()

        try:
            response = custom_api.get_namespaced_custom_object(
                group=TRAINING_GROUP,
                version=API_VERSION,
                namespace=self.metadata.namespace,
                plural=PLURAL,
                name=self.metadata.name,
            )
            self.status = HyperPodPytorchJobStatus.model_validate(
                response["status"], by_name=True
            )
        except Exception as e:
            logging.debug(f"Failed to refresh HyperPodPytorchJob {self.metadata.name}!")
            handel_exception(e, self.metadata.name, self.metadata.namespace)

    def list_pods(self) -> List[str]:
        if not validate_cluster_connection():
            raise Exception(
                "Failed to connect to the Kubernetes cluster. Please check your kubeconfig."
            )

        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()

            response = v1.list_namespaced_pod(self.metadata.namespace)
            pods = []

            for pod in response.items:
                if pod.metadata.name.startswith(f"{self.metadata.name}-pod"):
                    pods.append(pod.metadata.name)
            return pods
        except Exception as e:
            logging.debug(f"Failed to list pod in namespace {self.metadata.namespace}!")
            handel_exception(e, self.metadata.name, self.metadata.namespace)

    def get_logs_from_pod(self, pod_name: str, container: Optional[str] = None) -> str:
        if not validate_cluster_connection():
            raise Exception(
                "Failed to connect to the Kubernetes cluster. Please check your kubeconfig."
            )

        if container is None:
            # If container name is not set, get logs from the first container in the pod
            container = self.replicaSpecs[0].template.spec.containers[0].name

        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()

            logs = v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=self.metadata.namespace,
                timestamps=True,
                container=container,
            )
            return logs
        except Exception as e:
            logging.debug(f"Failed to get logs from pod {pod_name}!")
            handel_exception(e, self.metadata.name, self.metadata.namespace)


def _load_hp_job(response: dict) -> HyperPodPytorchJob:
    name = response["metadata"]["name"]
    namespace = response["metadata"]["namespace"]

    spec = _HyperPodPytorchJob.model_validate(response["spec"], by_name=True)
    metadata = Metadata(name=name, namespace=namespace)

    if "status" in response:
        status = HyperPodPytorchJobStatus.model_validate(
            response["status"], by_name=True
        )

    else:
        status = None

    job = HyperPodPytorchJob(
        metadata=metadata,
        status=status,
        **spec.model_dump(by_alias=True, exclude_none=True),
    )
    return job


def _load_hp_job_list(response: dict) -> List[HyperPodPytorchJob]:
    job_list = []
    for hp_job in response["items"]:
        job = _load_hp_job(hp_job)
        job_list.append(job)
    return job_list
