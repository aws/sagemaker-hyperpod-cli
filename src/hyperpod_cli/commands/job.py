# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
import boto3
import datetime
import logging
import json
import os
import sys
import subprocess
from typing import Any, Dict, Optional, List

import click
import yaml
from hydra import compose, initialize_config_dir
from hyperpod_cli import utils

from hyperpod_cli.constants.command_constants import (
    ENV_VARS_DICT,
    GENERATED_LAUNCHER_CONFIG_FILE_PATH,
    HYPERPOD_AUTO_RESUME_ANNOTATION_KEY,
    HYPERPOD_KUBERNETES_JOB_PREFIX,
    HYPERPOD_MAX_RETRY_ANNOTATION_KEY,
    KUEUE_QUEUE_NAME_LABEL_KEY,
    NODE_AFFINITY_DICT,
    DEEP_HEALTH_CHECK_PASSED_ONLY_NODE_AFFINITY_DICT,
    PullPolicy,
    RestartPolicy,
    PersistentVolumeClaim,
    Volume,
)
from hyperpod_cli.clients.kubernetes_client import KubernetesClient
from hyperpod_cli.custom_launcher.main import main as customer_launcher
from hyperpod_cli.service.cancel_training_job import CancelTrainingJob
from hyperpod_cli.service.get_training_job import GetTrainingJob
from hyperpod_cli.service.list_pods import ListPods
from hyperpod_cli.service.list_training_jobs import ListTrainingJobs
from hyperpod_cli.templates.k8s_pytorch_job_template import (
    KUBERNETES_PYTORCH_JOB_TEMPLATE,
)
from hyperpod_cli.utils import setup_logger, set_logging_level
from hyperpod_cli.validators.job_validator import JobValidator

logger = setup_logger(__name__)


@click.command()
@click.option(
    "--job-name",
    type=click.STRING,
    required=True,
    help="The name of the training job you want to get details",
)
@click.option(
    "--namespace",
    "-n",
    type=click.STRING,
    required=False,
    help="The namespace where training job was submitted",
)
@click.option(
    "--verbose",
    type=click.BOOL,
    is_flag=True,
    default=False,
    required=False,
    help="List training jobs from all namespaces",
)
@click.option(
    "--debug", 
    is_flag=True, 
    help="Enable debug mode"
)
def get_job(
    job_name: str,
    namespace: Optional[str],
    verbose: Optional[bool],
    debug: bool,
):
    """
    Get details for job running on Hyperpod Cluster
    """
    if debug:
        set_logging_level(logger, logging.DEBUG)

    get_training_job_service = GetTrainingJob()

    try:
        logger.debug("Getting training job details")
        # Execute the command to describe training job
        result = get_training_job_service.get_training_job(job_name, namespace, verbose)
        click.echo(result)
    except Exception as e:
        sys.exit(
            f"Unexpected error happens when trying to get training job {job_name} : {e}"
        )


@click.command()
@click.option(
    "--namespace",
    "-n",
    type=click.STRING,
    required=False,
    help="The namespace where from where to list training jobs",
)
@click.option(
    "--all-namespaces",
    "-A",
    type=click.BOOL,
    is_flag=True,
    default=False,
    required=False,
    help="List training jobs from all namespaces",
)
@click.option(
    "--selector",
    "-l",
    type=click.STRING,
    required=False,
    help="Filter training jobs based on labels provided",
)
@click.option(
    "--debug", 
    is_flag=True, 
    help="Enable debug mode"
)
def list_jobs(
    namespace: Optional[str],
    all_namespaces: Optional[bool],
    selector: Optional[str],
    debug: bool,
):
    if debug:
        set_logging_level(logger, logging.DEBUG)

    """List training jobs in the hyperpod cluster."""
    list_training_job_service = ListTrainingJobs()
    try:
        logger.debug("Listing training jobs")
        result = list_training_job_service.list_training_jobs(
            namespace, all_namespaces, selector
        )
        click.echo(result)
    except Exception as e:
        sys.exit(f"Unexpected error happens when trying to list training job : {e}")


@click.command()
@click.option(
    "--job-name",
    type=click.STRING,
    required=True,
    help="The name of the training job you want to describe",
)
@click.option(
    "--namespace",
    "-n",
    type=click.STRING,
    required=False,
    help="The namespace where training job was submitted",
)
@click.option(
    "--debug", 
    is_flag=True, 
    help="Enable debug mode"
)
def list_pods(
    job_name: str,
    namespace: Optional[str],
    debug: bool,
):
    """
    List pods associted with a training job on hyperpod cluster
    """
    if debug:
        set_logging_level(logger, logging.DEBUG)

    list_pods_service = ListPods()

    try:
        logger.debug("Listing Pods for the training job")
        result = list_pods_service.list_pods_for_training_job(job_name, namespace, True)
        click.echo(result)
    except Exception as e:
        sys.exit(
            f"Unexpected error happens when trying to list pods for training job {job_name} : {e}"
        )


@click.command()
@click.option(
    "--job-name",
    type=click.STRING,
    required=True,
    help="The name of the training job you want to cancel",
)
@click.option(
    "--namespace",
    "-n",
    type=click.STRING,
    required=False,
    help="The namespace where training job was submitted",
)
@click.option(
    "--debug", 
    is_flag=True, 
    help="Enable debug mode"
)
def cancel_job(
    job_name: str,
    namespace: Optional[str],
    debug: bool,
):
    """Cancel the job running on hyperpod cluster."""
    if debug:
        set_logging_level(logger, logging.DEBUG)

    cancel_training_job_service = CancelTrainingJob()

    try:
        logger.debug("Cancelling the training job")
        result = cancel_training_job_service.cancel_training_job(job_name, namespace)
        click.echo(result)
    except Exception as e:
        sys.exit(
            f"Unexpected error happens when trying to cancel training job {job_name} : {e}"
        )


@click.command()
@click.option(
    "--config-file",
    type=click.Path(),
    help="Config file to submit training job. Please provide absolute path to the file or a file under current folder",
)
@click.option(
    "--job-name", 
    type=click.STRING, 
    help="The name of the training job"
)
@click.option(
    "--namespace",
    type=click.STRING,
    help="The cluster's namespace to run training job",
)
@click.option(
    "--job-kind",
    type=click.STRING,
    default="kubeflow/PyTorchJob",
    help="The type of training job, currently only kubeflow/PytorchJob supported",
)
@click.option(
    "--image",
    type=click.STRING,
    help="The docker container image used for training job",
)
@click.option(
    "--pull-policy",
    type=click.Choice([c.value for c in PullPolicy]),
    default=PullPolicy.IF_NOT_PRESENT.value,
    help="Policy to pull container image",
)
@click.option(
    "--entry-script",
    type=click.STRING,
    help="The training docker container entry script",
)
@click.option(
    "--command",
    type=click.STRING,
    default="torchrun",
    help="The command to run entry script. Currently, only 'torchrun' supported",
)
@click.option(
    "--script-args", 
    type=click.STRING, 
    help="The arguments list for entry script"
)
@click.option(
    "--results-dir",
    type=click.STRING,
    default="./results",
    help="The location to store the results, checkpoints and logs.",
)
@click.option(
    "--environment",
    type=click.STRING,
    help="The environment variables for training docker container",
)
@click.option(
    "--instance-type",
    type=click.STRING,
    help="The instance type for the node to run the training job",
)
@click.option(
    "--node-count",
    type=click.INT,
    help="The number of nodes to run distributed training job",
)
@click.option(
    "--tasks-per-node",
    type=click.INT,
    help="The number of tasks per node when running training job",
)
@click.option(
    "--label-selector",
    type=click.STRING,
    help="Customize node label selection rules for training job",
)
@click.option(
    "--scheduler-type",
    type=click.STRING,
    default="Kueue",
    help="The Kubernetes scheduler type. Currently only support Kueue",
)
@click.option(
    "--queue-name", 
    type=click.STRING, 
    help="The name of the Kueue"
)
@click.option(
    "--priority", 
    type=click.STRING, 
    help="The priority of the training job"
)
@click.option(
    "--auto-resume",
    type=click.BOOL,
    default=False,
    help="Whether enable auto-resume for the training job",
)
@click.option(
    "--max-retry",
    type=click.INT,
    help="The max retry configured for auto-resume training job",
)
@click.option(
    "--restart-policy",
    type=click.Choice([c.value for c in RestartPolicy]),
    default=RestartPolicy.ON_FAILURE.value,
    help="The PyTorchJob restart policy",
)
@click.option(
    "--deep-health-check-passed-nodes-only",
    type=click.BOOL,
    default=False,
    help="Start job only on the nodes that passed deep health check",
)
@click.option(
    "--service-account-name",
    type=click.STRING,
    required=False,
    help="Service account name to give permissions to call aws services",
)
@click.option(
    "--persistent-volume-claims",
    type=click.STRING,
    required=False,
    help="A pod can have more than one claims to mounts, provide them in comma seperated format without spaces"
    " claimName:<container/mount/path>,claimName1:<container/mount/path1>",
)
@click.option(
    "--volumes",
    type=click.STRING,
    required=False,
    help="add temp directory for container to store data in the hosts"
    " <volume_name>:</host/mount/path>:</container/mount/path>,<volume_name>:</host/mount/path1>:</container/mount/path1>",
)
@click.option(
    "--debug", 
    is_flag=True, 
    help="Enable debug mode"
)
def start_job(
    config_file: Optional[str],
    job_name: Optional[str],
    namespace: Optional[str],
    job_kind: Optional[str],
    image: Optional[str],
    pull_policy: str,
    entry_script: Optional[str],
    command: Optional[str],
    script_args: Optional[str],
    results_dir: Optional[str],
    environment: Optional[str],
    instance_type: Optional[str],
    node_count: Optional[int],
    tasks_per_node: Optional[int],
    label_selector: Optional[str],
    scheduler_type: Optional[str],
    queue_name: Optional[str],
    priority: Optional[str],
    auto_resume: bool,
    max_retry: Optional[int],
    restart_policy: Optional[str],
    deep_health_check_passed_nodes_only: bool,
    service_account_name: Optional[str],
    persistent_volume_claims: Optional[str],
    volumes: Optional[str],
    debug: bool,
):
    if debug:
        set_logging_level(logger, logging.DEBUG)

    validator = JobValidator()
    if not validator.validate_aws_credential(boto3.Session()):
        logger.error("Cannot start Training job due to AWS credentials issue")
        sys.exit(1)

    if not namespace and config_file is None:
        k8s_client = KubernetesClient()
        namespace = k8s_client.get_current_context_namespace()

    if not validator.validate_start_job_args(
        config_file,
        job_name,
        node_count,
        instance_type,
        image,
        job_kind,
        command,
        label_selector,
        scheduler_type,
        queue_name,
        priority,
        auto_resume,
        restart_policy,
        max_retry,
        namespace,
        entry_script,
    ):
        sys.exit(1)

    """Submit job with the provided configuration file or directly with CLI
    arguments."""
    if job_name is not None:
        config = yaml.safe_load(KUBERNETES_PYTORCH_JOB_TEMPLATE)
        try:
            # Update the configuration with provided arguments
            config["container"] = image
            config["cluster"]["instance_type"] = str(instance_type)[len("ml.") :]
            config["training_cfg"]["entry_script"] = entry_script
            config["training_cfg"]["run"]["name"] = job_name
            config["training_cfg"]["run"]["nodes"] = node_count
            config["env_vars"] = ENV_VARS_DICT if environment is None else environment

            if (
                not _is_accelerator_instance_type(str(instance_type))
                and tasks_per_node is None
            ):
                config["training_cfg"]["run"]["ntasks_per_node"] = 8
            else:
                _override_or_remove(
                    config["training_cfg"]["run"], "ntasks_per_node", tasks_per_node
                )

            if service_account_name:
                config["cluster"]["cluster_config"]["service_account_name"] = (
                    service_account_name
                )

            persistent_volume_claims_list: List[PersistentVolumeClaim] = []
            if persistent_volume_claims:
                for claim in persistent_volume_claims.split(","):
                    claim_name, mount_path = claim.split(":")
                    persistent_volume_claims_list.append(
                        PersistentVolumeClaim(claim_name, mount_path)
                    )
            if persistent_volume_claims_list and len(persistent_volume_claims_list) > 0:
                pvc_mount = []
                for persistent_volume_claim in persistent_volume_claims_list:
                    pvc_mount.append(
                        {
                            "claimName": persistent_volume_claim.claim_name,
                            "mountPath": persistent_volume_claim.mount_path,
                        }
                    )
                config["cluster"]["cluster_config"]["persistent_volume_claims"] = (
                    pvc_mount
                )

            volume_list: List[Volume] = []

            if volumes:
                for volume in volumes.split(","):
                    volume_name, host_path, container_path = volume.split(":")
                    volume_list.append(Volume(volume_name, host_path, container_path))
            if volume_list and len(volume_list) > 0:
                volume_mount = []
                for volume in volume_list:
                    volume_mount.append(
                        {
                            "hostPath": volume.host_path,
                            "mountPath": volume.mount_path,
                            "volumeName": volume.volume_name,
                        }
                    )
                config["cluster"]["cluster_config"]["volumes"] = volume_mount

            if label_selector is not None:
                config["cluster"]["cluster_config"]["label_selector"] = label_selector
            elif deep_health_check_passed_nodes_only:
                config["cluster"]["cluster_config"]["label_selector"] = (
                    DEEP_HEALTH_CHECK_PASSED_ONLY_NODE_AFFINITY_DICT
                )
            else:
                config["cluster"]["cluster_config"]["label_selector"] = (
                    NODE_AFFINITY_DICT
                )

            if auto_resume:
                # Set max_retry default to 1
                if max_retry is None:
                    max_retry = 1

                annotations = {
                    HYPERPOD_AUTO_RESUME_ANNOTATION_KEY: auto_resume,
                    HYPERPOD_MAX_RETRY_ANNOTATION_KEY: max_retry,
                }
                config["cluster"]["cluster_config"]["annotations"] = annotations
            else:
                config["cluster"]["cluster_config"].pop("annotations")

            _override_or_remove(
                config["cluster"]["cluster_config"], "pullPolicy", pull_policy
            )
            _override_or_remove(
                config["cluster"]["cluster_config"], "restartPolicy", restart_policy
            )
            _override_or_remove(
                config["cluster"]["cluster_config"],
                "custom_labels",
                {KUEUE_QUEUE_NAME_LABEL_KEY: queue_name}
                if queue_name is not None
                else None,
            )
            _override_or_remove(
                config["cluster"]["cluster_config"], "priority_class_name", priority
            )
            _override_or_remove(config["training_cfg"], "script_args", script_args)
            _override_or_remove(
                config["cluster"]["cluster_config"], "namespace", namespace
            )
            _override_or_remove(config, "base_results_dir", results_dir)
        except Exception as e:
            logger.error(f"Config template has unexpected error: {e}")
            sys.exit(1)

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d-%H%M%S")
        filename = f"{HYPERPOD_KUBERNETES_JOB_PREFIX}-{timestamp}.yaml"
        with open(
            os.path.join(GENERATED_LAUNCHER_CONFIG_FILE_PATH, filename), "w"
        ) as file:
            yaml.dump(config, file, default_flow_style=False)

        logger.debug(
            f"Configuration file generated in: {GENERATED_LAUNCHER_CONFIG_FILE_PATH + filename}"
        )
        launcher_config_path = GENERATED_LAUNCHER_CONFIG_FILE_PATH
        launcher_config_file_name = filename
    else:
        """Start job with the provided configuration file or directly with CLI
        arguments"""
        if os.path.isabs(config_file):
            abs_config_file_path = config_file
        else:
            abs_config_file_path = os.path.abspath(config_file)
        if not validator.validate_start_job_config_yaml(abs_config_file_path):
            sys.exit(1)
        config_path, config_name = os.path.split(abs_config_file_path)
        launcher_config_path = str(config_path)
        launcher_config_file_name = str(config_name)

    logger.debug(
        f"Starting job with config {launcher_config_path}/{launcher_config_file_name}"
    )

    # Initialize Hydra and call custom launcher with Hydra config to submit job
    try:
        with initialize_config_dir(config_dir=launcher_config_path, version_base="1.2"):
            cfg = compose(config_name=launcher_config_file_name)
            with suppress_standard_output_context():
                customer_launcher(cfg)
    except Exception as e:
        logger.error(f"Starting job failed due to: {e}")
        sys.exit(1)
    finally:
        # Remove temporary created Launcher config file for submit via CLI argument case
        if job_name is not None and config_file is None:
            file_to_delete = os.path.join(
                launcher_config_path, launcher_config_file_name
            )
            if os.path.exists(file_to_delete):
                os.remove(file_to_delete)
    console_link = utils.get_cluster_console_url()
    print(json.dumps({"Console URL": console_link}, indent=1, sort_keys=False))


def _override_or_remove(
    config: Dict,
    key: str,
    value: Optional[Any],
):
    if value is not None:
        config[key] = value
    else:
        config.pop(key)


def _is_accelerator_instance_type(
    instance_type: str,
) -> bool:
    if (
        instance_type.startswith("ml.p")
        or instance_type.startswith("ml.g")
        or instance_type.startswith("ml.trn")
    ):
        return True
    return False


class suppress_standard_output_context:
    def __enter__(self):
        self._original_popen = subprocess.Popen
        subprocess.Popen = self._popen_suppress

    def __exit__(self, exc_type, exc_value, traceback):
        subprocess.Popen = self._original_popen

    def _popen_suppress(self, *args, **kwargs):
        if "stdout" not in kwargs:
            kwargs["stdout"] = open(os.devnull, "w")
        return self._original_popen(*args, **kwargs)
