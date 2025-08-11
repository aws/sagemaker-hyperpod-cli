from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator

class PytorchJobSchema(BaseModel):
    job_name: Optional[str] = Field(alias="job_name", description="Job name")
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