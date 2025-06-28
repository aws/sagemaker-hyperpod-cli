from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Union


class PyTorchJobConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')

    job_name: str = Field(alias="job_name", description="Job name")
    namespace: Optional[str] = Field(default='default', description="Kubernetes namespace")
    job_kind: Optional[str] = Field(default='HyperPodPyTorchJob', alias="job_kind")
    image: str = Field(description="Docker image for training")
    command: Optional[List[str]] = Field(default=None, description="Command to run in the container")
    entry_script: Optional[str] = Field(default=None, alias="entry_script", description="Entry script for the job")
    script_args: Optional[List[str]] = Field(default=None, alias="script_args", description="Arguments for the entry script")
    environment: Optional[Dict[str, str]] = Field(default=None, description="Environment variables as key_value pairs")
    pull_policy: Optional[str] = Field(default='IfNotPresent', alias="pull_policy", description="Image pull policy")
    instance_type: Optional[str] = Field(default=None, alias="instance_type", description="Instance type for training")
    node_count: Optional[int] = Field(default=1, alias="node_count", description="Number of nodes")
    tasks_per_node: Optional[int] = Field(default=None, alias="tasks_per_node", description="Number of tasks per node")
    label_selector: Optional[Dict[str, str]] = Field(default=None, alias="label_selector", description="Node label selector as key_value pairs")
    deep_health_check_passed_nodes_only: Optional[bool] = Field(default=False, alias="deep_health_check_passed_nodes_only", description="Schedule pods only on nodes that passed deep health check")
    scheduler_type: Optional[str] = Field(default='default', alias="scheduler_type", description="Scheduler type")
    queue_name: Optional[str] = Field(default=None, alias="queue_name", description="Queue name for job scheduling")
    priority: Optional[str] = Field(default=None, description="Priority class for job scheduling")
    auto_resume: Optional[bool] = Field(default=False, alias="auto_resume", description="Auto resume capability (not supported)")
    max_retry: Optional[int] = Field(default=0, alias="max_retry", description="Maximum number of job retries")
    restart_policy: Optional[str] = Field(default=None, alias="restart_policy", description="Restart policy (not supported _ always synchronized restarts)")
    volumes: Optional[List[str]] = Field(default=None, description="List of volumes to mount")
    persistent_volume_claims: Optional[List[str]] = Field(default=None, alias="persistent_volume_claims", description="List of persistent volume claims")
    results_dir: Optional[str] = Field(default=None, alias="results_dir", description="Directory to store results (part of entry script)")
    service_account_name: Optional[str] = Field(default=None, alias="service_account_name", description="Service account name")
    pre_script: Optional[str] = Field(default=None, alias="pre_script", description="Script to run before main job (part of entry script)")
    post_script: Optional[str] = Field(default=None, alias="post_script", description="Script to run after main job (part of entry script)")