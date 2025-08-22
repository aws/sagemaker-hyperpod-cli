from pydantic import ConfigDict, Field

from sagemaker.hyperpod.cli.constants.command_constants import INSTANCE_TYPE_LABEL
from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_unified_config import (
    _HyperPodPytorchJob, HyperPodPytorchJobStatus
)
from sagemaker.hyperpod.common.config.metadata import Metadata
from kubernetes import client, config
from typing import List, Optional, ClassVar
from sagemaker.hyperpod.common.utils import (
    handle_exception,
    get_default_namespace,
    setup_logging,
    verify_kubernetes_version_compatibility
)
from sagemaker.hyperpod.common.telemetry.telemetry_logging import (
    _hyperpod_telemetry_emitter,
)
from sagemaker.hyperpod.common.telemetry.constants import Feature
import yaml
import logging

from sagemaker.hyperpod.training.quota_allocation_util import _is_valid, _get_resources_from_compute_quotas, _get_resources_from_instance, _get_limits



TRAINING_GROUP = "sagemaker.amazonaws.com"
API_VERSION = "v1"
PLURAL = "hyperpodpytorchjobs"
KIND = "HyperPodPyTorchJob"
TRAINING_OPERATOR_NAMESPACE = "aws-hyperpod"
TRAINING_OPERATOR_LABEL = "hp-training-control-plane"


class HyperPodPytorchJob(_HyperPodPytorchJob):
    is_kubeconfig_loaded: ClassVar[bool] = False

    model_config = ConfigDict(extra="forbid")

    metadata: Metadata = Field(
        description="The metadata of the HyperPodPytorchJob",
    )

    status: Optional[HyperPodPytorchJobStatus] = Field(
        default=None, description="The status of the HyperPodPytorchJob"
    )

    @classmethod
    def get_logger(cls):
        return logging.getLogger(__name__)
    
    @classmethod
    def verify_kube_config(cls):
        if not cls.is_kubeconfig_loaded:
            config.load_kube_config()
            cls.is_kubeconfig_loaded = True
            
            # Verify Kubernetes version compatibility
            verify_kubernetes_version_compatibility(cls.get_logger())
    @classmethod
    def _extract_numeric_value(cls, value):
        """Extract numeric value from strings like '1.5Gi' -> 1.5"""
        if not value:
            return None
        import re
        match = re.match(r'^([0-9]*\.?[0-9]+)', str(value))
        return float(match.group(1)) if match else None

    @classmethod
    def _process_replica_resources(cls, data):
        """Process and validate replica resource configuration."""
        try:
            node_count = data.get('replicas', None)

            # Extract nested configuration with validation
            template = data.get('template', {})
            spec = template.get('spec', {})
            node_selector = spec.get('nodeSelector', {})
            instance_type = node_selector.get(INSTANCE_TYPE_LABEL) if node_selector else None
            if not instance_type:
                return None

            containers = spec.get('containers', [])

            if not containers:
                raise ValueError("No containers found in template spec")

            container = containers[0]
            resources = container.get('resources', {})
            requests = resources.get('requests', {})
            limits = resources.get('limits', {})

            # Extract resource values
            vcpu = float(requests.get('vcpu')) if requests.get('vcpu') else None
            memory = cls._extract_numeric_value(requests.get('memory'))
            accelerators = int(requests.get('accelerators'))  if requests.get('accelerators') else None
            memory_limit = cls._extract_numeric_value(limits.get('memory'))
            vcpu_limit = float(limits.get('vcpu')) if limits.get('vcpu') else None
            accelerators_limit = int(limits.get('accelerators'))  if limits.get('accelerators') else None

            # Validate configuration
            valid, error = _is_valid(vcpu, memory, accelerators, node_count, instance_type)
            if not valid:
                raise ValueError(error)

            # Calculate resource values
            requests_value = (_get_resources_from_compute_quotas(instance_type, vcpu, memory, accelerators)
                              or _get_resources_from_instance(instance_type, node_count=1))
            limits_value = _get_limits(instance_type, vcpu_limit, memory_limit, accelerators_limit)

            # Update data with calculated values
            data['template']['spec']['containers'][0]['resources']['requests'] = requests_value
            data['template']['spec']['containers'][0]['resources']['limits'] = limits_value
            return data
        except KeyError as e:
            raise ValueError(f"Missing required configuration key: {str(e)}")

    @classmethod
    def _get_container_resources(cls, replica_spec):
        """Extract container resources from replica spec."""
        container_resources = replica_spec['template']['spec']['containers'][0]['resources']
        return container_resources['requests'], container_resources['limits']

    @classmethod
    def allocate_quotas_if_applicable(cls, spec):
        try:
            spec_dict = spec.model_dump()
            replica_spec = spec_dict['replicaSpecs'][0]
            cls._process_replica_resources(replica_spec)

            # Update the original spec object directly
            requests, limits = cls._get_container_resources(replica_spec)
            spec.replicaSpecs[0].template.spec.containers[0].resources.requests = requests
            spec.replicaSpecs[0].template.spec.containers[0].resources.limits = limits

            return spec
        except ValueError as e:
            raise ValueError(e)
        except Exception as e:
            # In case of any other exception, return original spec
            return spec

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "create_pytorchjob")
    def create(self, debug=False):
        self.verify_kube_config()

        logger = self.get_logger()
        logger = setup_logging(logger, debug)

        spec = _HyperPodPytorchJob(**self.model_dump(by_alias=True, exclude_none=True))

        if not self.metadata.namespace:
            self.metadata.namespace = get_default_namespace()

        spec = self.allocate_quotas_if_applicable(spec)
        if spec.replicaSpecs[0].replicas is None or spec.replicaSpecs[0].replicas == 0:
            spec.replicaSpecs[0].replicas = 1 # default value

        config = {
            "apiVersion": f"{TRAINING_GROUP}/{API_VERSION}",
            "kind": KIND,
            "metadata": self.metadata.model_dump(exclude_none=True),
            "spec": spec.model_dump(exclude_none=True),
        }

        custom_api = client.CustomObjectsApi()
        logger.debug(
            "Deploying HyperPodPytorchJob with config:\n%s",
            yaml.dump(config),
        )

        try:
            custom_api.create_namespaced_custom_object(
                group=TRAINING_GROUP,
                version=API_VERSION,
                namespace=self.metadata.namespace,
                plural=PLURAL,
                body=config,
            )
            logger.info(f"Successfully submitted HyperPodPytorchJob '{self.metadata.name}'!")
        except Exception as e:
            logger.error(f"Failed to create HyperPodPytorchJob {self.metadata.name}!")
            handle_exception(e, self.metadata.name, self.metadata.namespace)



    @classmethod
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "list_pytorchjobs")
    def list(cls, namespace=None) -> List["HyperPodPytorchJob"]:
        cls.verify_kube_config()

        if namespace is None:
            namespace = get_default_namespace()

        logger = cls.get_logger()
        logger = setup_logging(logger)

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
            logger.error(f"Failed to list HyperpodPytorchJobs!")
            handle_exception(e, "", namespace)

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "delete_pytorchjob")
    def delete(self):
        self.verify_kube_config()

        logger = self.get_logger()
        logger = setup_logging(logger)

        custom_api = client.CustomObjectsApi()

        try:
            custom_api.delete_namespaced_custom_object(
                group=TRAINING_GROUP,
                version=API_VERSION,
                namespace=self.metadata.namespace,
                plural=PLURAL,
                name=self.metadata.name,
            )
            logger.info(f"Successful deleted HyperPodPytorchJob '{self.metadata.name}'!")
        except Exception as e:
            logger.error(f"Failed to delete HyperPodPytorchJob {self.metadata.name}!")
            handle_exception(e, self.metadata.name, self.metadata.namespace, 
                            operation_type='delete', resource_type='training_job')

    @classmethod
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "get_pytorchjob")
    def get(cls, name, namespace=None) -> "HyperPodPytorchJob":
        cls.verify_kube_config()

        if namespace is None:
            namespace = get_default_namespace()

        logger = cls.get_logger()
        logger = setup_logging(logger)

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
            handle_exception(e, name, namespace, 
                            operation_type='get', resource_type='training_job')

    def refresh(self) -> "HyperPodPytorchJob":
        self.verify_kube_config()

        logger = self.get_logger()
        logger = setup_logging(logger)

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
            logger.error(f"Failed to refresh HyperPodPytorchJob {self.metadata.name}!")
            handle_exception(e, self.metadata.name, self.metadata.namespace)

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "list_pods_pytorchjob")
    def list_pods(self) -> List[str]:
        self.verify_kube_config()

        logger = self.get_logger()
        logger = setup_logging(logger)

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
            logger.error(f"Failed to list pod in namespace {self.metadata.namespace}!")
            handle_exception(e, self.metadata.name, self.metadata.namespace)

    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "get_pytorchjob_logs_from_pod")
    def get_logs_from_pod(self, pod_name: str, container: Optional[str] = None) -> str:
        self.verify_kube_config()

        logger = self.get_logger()
        logger = setup_logging(logger)

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
            logger.error(f"Failed to get logs from pod {pod_name}!")
            handle_exception(e, self.metadata.name, self.metadata.namespace)

    @classmethod
    @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "get_operator_logs_pytorchjob")
    def get_operator_logs(cls, since_hours: float):
        cls.verify_kube_config()

        v1 = client.CoreV1Api()

        # Get pods with the training operator label directly
        pods = v1.list_namespaced_pod(
            namespace=TRAINING_OPERATOR_NAMESPACE,
            label_selector=TRAINING_OPERATOR_LABEL
        )

        if not pods.items:
            raise Exception(
                f"No training operator pod found with label {TRAINING_OPERATOR_LABEL}"
            )

        # Use the first pod found
        operator_pod = pods.items[0]
        pod_name = operator_pod.metadata.name

        try:
            logs = v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=TRAINING_OPERATOR_NAMESPACE,
                timestamps=True,
                since_seconds=int(3600 * since_hours),
            )
        except Exception as e:
            handle_exception(e, pod_name, TRAINING_OPERATOR_NAMESPACE)

        return logs


def _load_hp_job(response: dict) -> HyperPodPytorchJob:

    spec = _HyperPodPytorchJob.model_validate(response["spec"], by_name=True)
    metadata = Metadata(**response["metadata"])

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
