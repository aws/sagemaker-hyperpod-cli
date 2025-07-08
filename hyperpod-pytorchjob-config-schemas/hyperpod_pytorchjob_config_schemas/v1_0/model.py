from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Union
from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_config import (
    Container,
    ReplicaSpec,
    Resources,
    RunPolicy,
    Spec,
    Template,
    Metadata,
)


class PyTorchJobConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_name: str = Field(alias="job_name", description="Job name")
    image: str = Field(description="Docker image for training")
    namespace: Optional[str] = Field(default=None, description="Kubernetes namespace")
    command: Optional[List[str]] = Field(
        default=None, description="Command to run in the container"
    )
    args: Optional[List[str]] = Field(
        default=None, alias="args", description="Arguments for the entry script"
    )
    environment: Optional[Dict[str, str]] = Field(
        default=None, description="Environment variables as key_value pairs"
    )
    pull_policy: Optional[str] = Field(
        default=None, alias="pull_policy", description="Image pull policy"
    )
    instance_type: Optional[str] = Field(
        default=None, alias="instance_type", description="Instance type for training"
    )
    node_count: Optional[int] = Field(
        default=None, alias="node_count", description="Number of nodes"
    )
    tasks_per_node: Optional[int] = Field(
        default=None, alias="tasks_per_node", description="Number of tasks per node"
    )
    label_selector: Optional[Dict[str, str]] = Field(
        default=None,
        alias="label_selector",
        description="Node label selector as key_value pairs",
    )
    deep_health_check_passed_nodes_only: Optional[bool] = Field(
        default=False,
        alias="deep_health_check_passed_nodes_only",
        description="Schedule pods only on nodes that passed deep health check",
    )
    scheduler_type: Optional[str] = Field(
        default=None, alias="scheduler_type", description="Scheduler type"
    )
    queue_name: Optional[str] = Field(
        default=None, alias="queue_name", description="Queue name for job scheduling"
    )
    priority: Optional[str] = Field(
        default=None, description="Priority class for job scheduling"
    )
    max_retry: Optional[int] = Field(
        default=None, alias="max_retry", description="Maximum number of job retries"
    )
    volumes: Optional[List[str]] = Field(
        default=None, description="List of volumes to mount"
    )
    persistent_volume_claims: Optional[List[str]] = Field(
        default=None,
        alias="persistent_volume_claims",
        description="List of persistent volume claims",
    )
    service_account_name: Optional[str] = Field(
        default=None, alias="service_account_name", description="Service account name"
    )

    def to_domain(self) -> Dict:
        """
        Convert flat config to domain model (HyperPodPytorchJobSpec)
        """
        # Create container with required fields
        container_kwargs = {
            "name": "container-name",
            "image": self.image,
            "resources": Resources(
                requests={"nvidia.com/gpu": "0"},
                limits={"nvidia.com/gpu": "0"},
            ),
        }

        # Add optional container fields
        if self.command is not None:
            container_kwargs["command"] = self.command
        if self.args is not None:
            container_kwargs["args"] = self.args
        if self.pull_policy is not None:
            container_kwargs["image_pull_policy"] = self.pull_policy
        if self.environment is not None:
            container_kwargs["env"] = [
                {"name": k, "value": v} for k, v in self.environment.items()
            ]
        if self.volumes is not None:
            container_kwargs["volume_mounts"] = [
                {"name": v, "mount_path": f"/mnt/{v}"} for v in self.volumes
            ]

        # Create container object
        container = Container(**container_kwargs)

        # Create pod spec kwargs
        spec_kwargs = {"containers": list([container])}

        # Add node selector if any selector fields are present
        node_selector = {}
        if self.instance_type is not None:
            map = {"node.kubernetes.io/instance-type": self.instance_type}
            node_selector.update(map)
        if self.label_selector is not None:
            node_selector.update(self.label_selector)
        if self.deep_health_check_passed_nodes_only:
            map = {"deep-health-check-passed": "true"}
            node_selector.update(map)
        if node_selector:
            spec_kwargs.update({"node_selector": node_selector})

        # Add other optional pod spec fields
        if self.service_account_name is not None:
            map = {"service_account_name": self.service_account_name}
            spec_kwargs.update(map)

        if self.scheduler_type is not None:
            map = {"scheduler_name": self.scheduler_type}
            spec_kwargs.update(map)

        # Build metadata labels only if relevant fields are present
        metadata_kwargs = {"name": self.job_name}
        if self.namespace is not None:
            metadata_kwargs["namespace"] = self.namespace

        metadata_labels = {}
        if self.queue_name is not None:
            metadata_labels["kueue.x-k8s.io/queue-name"] = self.queue_name
        if self.priority is not None:
            metadata_labels["kueue.x-k8s.io/priority-class"] = self.priority

        if metadata_labels:
            metadata_kwargs["labels"] = metadata_labels

        # Create replica spec with only non-None values
        replica_kwargs = {
            "name": "pod",
            "template": Template(
                metadata=Metadata(**metadata_kwargs), spec=Spec(**spec_kwargs)
            ),
        }

        if self.node_count is not None:
            replica_kwargs["replicas"] = self.node_count

        replica_spec = ReplicaSpec(**replica_kwargs)

        replica_specs = list([replica_spec])

        job_kwargs = {"replica_specs": replica_specs}
        # Add optional fields only if they exist
        if self.tasks_per_node is not None:
            job_kwargs["nproc_per_node"] = str(self.tasks_per_node)

        if self.max_retry is not None:
            job_kwargs["run_policy"] = RunPolicy(
                clean_pod_policy="None", job_max_retry_count=self.max_retry
            )

        # Create base return dictionary
        result = {
            "name": self.job_name,
            "namespace": self.namespace,
            "spec": job_kwargs,
        }

        return result
