from types import SimpleNamespace
from config.hyperpod_pytorch_job_config import (
    Container,
    HyperPodPytorchJobSpec,
    ReplicaSpec,
    Spec,
    Template,
)
from kubernetes import client
from typing import Optional
from utils import remove_metadata, remove_metadata_from_list, validate_cluster_connection
import yaml

TRAINING_GROUP = "sagemaker.amazonaws.com"
API_VERSION = "v1"
PLURAL = "hyperpodpytorchjobs"
KIND = "HyperPodPyTorchJob"


class HyperpodPytorchJob:
    def __init__(
        self,
        name: str,
        namespace: str = "default",
        spec: Optional[HyperPodPytorchJobSpec] = None,
    ):
        self.apiVersion = f"{TRAINING_GROUP}/{API_VERSION}"
        self.kind = KIND

        self.metadata = SimpleNamespace(name=name, namespace=namespace)

        self.spec = spec

    @classmethod
    def create(
        cls,
        name: str,
        namespace: str = "default",
        nproc_per_node: str = "auto",
        image: str = "",
        node_count: int = 1,
    ):
        spec = HyperPodPytorchJobSpec(
            nproc_per_node=nproc_per_node,
            replica_specs=[
                ReplicaSpec(
                    name="replica-name",
                    replicas=node_count,
                    template=Template(
                        spec=Spec(
                            containers=[
                                Container(name="container-name", image=image)
                            ]
                        )
                    ),
                )
            ],
        )

        job = HyperpodPytorchJob(name, namespace, spec)
        job.submit()
        return job

    @classmethod
    def create_from_spec(
        cls,
        name: str,
        namespace: str = "default",
        spec: HyperPodPytorchJobSpec = None,
    ):
        job = HyperpodPytorchJob(name, namespace, spec)
        job.submit()
        return job

    def config(self):
        return {
            "apiVersion": self.apiVersion,
            "kind": self.kind,
            "metadata": self.metadata.__dict__,
            "spec": self.spec.model_dump(exclude_none=True),
        }

    def submit(self):
        if not validate_cluster_connection():
            raise Exception(
                "Failed to connect to the Kubernetes cluster. Please check your kubeconfig."
            )

        custom_api = client.CustomObjectsApi()
        print(
            "Deploying HyperpodPytorchJob with config:\n",
            yaml.dump(self.config()),
            end="",
        )

        try:
            custom_api.create_namespaced_custom_object(
                group=TRAINING_GROUP,
                version=API_VERSION,
                namespace=self.metadata.namespace,
                plural=PLURAL,
                body=self.config(),
            )
            print("Successful submitted HyperpodPytorchJob!")
        except Exception as e:
            print(f"Failed to submit HyperpodPytorchJob: {e}")

    @classmethod
    def list(cls, namespace="default"):
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
            return remove_metadata_from_list(hp_job_list)
        except Exception as e:
            print(f"Failed to list HyperpodPytorchJobs: {e}")

    @classmethod
    def delete(cls, name, namespace="default"):
        if not validate_cluster_connection():
            raise Exception(
                "Failed to connect to the Kubernetes cluster. Please check your kubeconfig."
            )

        custom_api = client.CustomObjectsApi()

        try:
            custom_api.delete_namespaced_custom_object(
                group=TRAINING_GROUP,
                version=API_VERSION,
                namespace=namespace,
                plural=PLURAL,
                name=name,
            )
            print(f"Successful deleted HyperpodPytorchJob!")
        except Exception as e:
            print(f"Failed to delete HyperpodPytorchJob: {e}")

    @classmethod
    def describe(cls, name, namespace="default"):
        if not validate_cluster_connection():
            raise Exception(
                "Failed to connect to the Kubernetes cluster. Please check your kubeconfig."
            )

        custom_api = client.CustomObjectsApi()

        try:
            hp_job = custom_api.get_namespaced_custom_object(
                group=TRAINING_GROUP,
                version=API_VERSION,
                namespace=namespace,
                plural=PLURAL,
                name=name,
            )
            return remove_metadata(hp_job)
        except Exception as e:
            print(f"Failed to describte HyperpodPytorchJob: {e}")
