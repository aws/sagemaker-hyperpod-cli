from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Union
from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_config import _HyperPodPytorchJob, ReplicaSpec, RunPolicy, Template, Metadata, Spec


class PyTorchJobConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')

    job_name: str = Field(alias="job_name", description="Job name")
    image: str = Field(description="Docker image for training")
    namespace: Optional[str] = Field(default=None, description="Kubernetes namespace")
    command: Optional[List[str]] = Field(default=None, description="Command to run in the container")
    args: Optional[List[str]] = Field(default=None, alias="args", description="Arguments for the entry script")
    environment: Optional[Dict[str, str]] = Field(default=None, description="Environment variables as key_value pairs")
    pull_policy: Optional[str] = Field(default=None, alias="pull_policy", description="Image pull policy")
    instance_type: Optional[str] = Field(default=None, alias="instance_type", description="Instance type for training")
    node_count: Optional[int] = Field(default=None, alias="node_count", description="Number of nodes")
    tasks_per_node: Optional[int] = Field(default=None, alias="tasks_per_node", description="Number of tasks per node")
    label_selector: Optional[Dict[str, str]] = Field(default=None, alias="label_selector", description="Node label selector as key_value pairs")
    deep_health_check_passed_nodes_only: Optional[bool] = Field(default=False, alias="deep_health_check_passed_nodes_only", description="Schedule pods only on nodes that passed deep health check")
    scheduler_type: Optional[str] = Field(default=None, alias="scheduler_type", description="Scheduler type")
    queue_name: Optional[str] = Field(default=None, alias="queue_name", description="Queue name for job scheduling")
    priority: Optional[str] = Field(default=None, description="Priority class for job scheduling")
    max_retry: Optional[int] = Field(default=None, alias="max_retry", description="Maximum number of job retries")
    volumes: Optional[List[str]] = Field(default=None, description="List of volumes to mount")
    persistent_volume_claims: Optional[List[str]] = Field(default=None, alias="persistent_volume_claims", description="List of persistent volume claims")
    service_account_name: Optional[str] = Field(default=None, alias="service_account_name", description="Service account name")



    def to_domain(self) -> _HyperPodPytorchJob:
        """
        Convert flat config to domain model (HyperPodPytorchJobSpec)
        """
        # Create container spec with required fields
        container = {
        "name": self.job_name,
        "image": self.image,
        }

        # Add resources if needed (could be moved to SDK default)
        container["resources"] = {
        "limits": {
            "nvidia.com/gpu": 8
        }
        }

        # Add optional container fields only if they're not None
        optional_container_fields = [
        ("command", "command", self.command),
        ("args", "args", self.args),
        ("image_pull_policy", "pull_policy", self.pull_policy),
        ]

        for k8s_name, attr_name, value in optional_container_fields:
            if value is not None:
                container[k8s_name] = value

        # Add environment variables if present
        if self.environment is not None:
            container["env"] = [{"name": k, "value": v} for k, v in self.environment.items()]

        # Add volume mounts if present
        if self.volumes is not None:
            container["volume_mounts"] = [{"name": v, "mount_path": f"/mnt/{v}"} for v in self.volumes]

        # Create pod template spec
        template_spec = {
        "containers": [container]
        }

        # Build node selector only if relevant fields are present
        node_selector = {}
        if self.instance_type is not None:
            node_selector["node.kubernetes.io/instance-type"] = self.instance_type
        if self.label_selector is not None:
            node_selector.update(self.label_selector)
        if self.deep_health_check_passed_nodes_only:  # This has a default of False
            node_selector["deep-health-check-passed"] = "true"

        if node_selector:
            template_spec["node_selector"] = node_selector

        # Add other optional pod spec fields only if they're not None
        optional_template_fields = [
        ("service_account_name", "service_account_name", self.service_account_name),
        ("scheduler_name", "scheduler_type", self.scheduler_type),
        ]

        for k8s_name, attr_name, value in optional_template_fields:
            if value is not None:
                template_spec[k8s_name] = value

        # Handle volumes only if either volumes or persistent_volume_claims is present
        volumes = []
        if self.volumes is not None:
            volumes.extend([
                {
                    "name": v,
                    "persistent_volume_claim": {"claim_name": v}
                }
                for v in self.volumes
            ])
        if self.persistent_volume_claims is not None:
            volumes.extend([
                {
                    "name": v,
                    "persistent_volume_claim": {"claim_name": v}
                }
                for v in self.persistent_volume_claims
            ])
        if volumes:
            template_spec["volumes"] = volumes

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
        "name": self.job_name,
        "template": Template(
            metadata=Metadata(**metadata_kwargs),
            spec=Spec(**template_spec)
        )
        }

        if self.node_count is not None:
            replica_kwargs["replicas"] = self.node_count

        replica_spec = ReplicaSpec(**replica_kwargs)

        # Create hyperpod job kwargs
        job_kwargs = {
        "replica_specs": [replica_spec]
        }

        # Add optional job fields only if they're not None
        if self.tasks_per_node is not None:
            job_kwargs["nproc_per_node"] = str(self.tasks_per_node)
        if self.max_retry is not None:
            job_kwargs["run_policy"] = RunPolicy(
            job_max_retry_count=self.max_retry,
            clean_pod_policy="All"
         )

        # Create and return the domain model
        return { "name":self.job_name ,
                 "namespace":self.namespace,
                 "spec":_HyperPodPytorchJob(**job_kwargs)
                 }