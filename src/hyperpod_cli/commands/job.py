import datetime
import os
import sys
from typing import Any, Dict, Optional

import click
import yaml
from hydra import compose, initialize_config_dir

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
)
from hyperpod_cli.custom_launcher.main import main as customer_launcher
from hyperpod_cli.service.cancel_training_job import CancelTrainingJob
from hyperpod_cli.service.describe_training_job import DescribeTrainingJob
from hyperpod_cli.service.list_pods import ListPods
from hyperpod_cli.service.list_training_jobs import ListTrainingJobs
from hyperpod_cli.templates.k8s_pytorch_job_template import KUBERNETES_PYTORCH_JOB_TEMPLATE
from hyperpod_cli.utils import setup_logger
from hyperpod_cli.validators.job_validator import JobValidator

logger = setup_logger(__name__)


@click.command()
@click.option(
    "--name",
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
    "--verbose",
    type=click.BOOL,
    is_flag=True,
    default=False,
    required=False,
    help="List training jobs from all namespaces",
)
def get_job(name: str, namespace: Optional[str], verbose: Optional[bool]):
    """
    Describe a job running on Hyperpod Cluster
    """

    describe_training_job_service = DescribeTrainingJob()

    try:
        # Execute the command to describe training job
        result = describe_training_job_service.describe_training_job(name, namespace, verbose)
        click.echo(result)
    except Exception as e:
        sys.exit(f"Unexpected error happens when trying to describe training job {name} : {e}")


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
def list_jobs(namespace: Optional[str], all_namespaces: Optional[bool], selector: Optional[str]):
    """List training jobs in the hyperpod cluster."""
    list_training_job_service = ListTrainingJobs()
    try:
        result = list_training_job_service.list_training_jobs(namespace, all_namespaces, selector)
        click.echo(result)
    except Exception as e:
        sys.exit(f"Unexpected error happens when trying to list training job : {e}")


@click.command()
@click.option(
    "--name",
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
def list_pods(name: str, namespace: Optional[str]):
    """
    List pods associted with a training job on hyperpod cluster
    """

    list_pods_service = ListPods()

    try:
        result = list_pods_service.list_pods_for_training_job(name, namespace, True)
        click.echo(result)
    except Exception as e:
        sys.exit(f"Unexpected error happens when trying to list pods for training job {name} : {e}")


@click.command()
@click.option(
    "--name",
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
def cancel_job(name: str, namespace: Optional[str]):
    """Cancel the job running on hyperpod cluster."""

    cancel_training_job_service = CancelTrainingJob()

    try:
        result = cancel_training_job_service.cancel_training_job(name, namespace)
        click.echo(result)
    except Exception as e:
        sys.exit(f"Unexpected error happens when trying to cancel training job {name} : {e}")


@click.command()
@click.option("--config-name", type=click.Path(), help="Config file to submit training job")
@click.option(
    "--config-path", default="../HyperpodCLI/", help="Path to the configuration directory"
)
@click.option("--name", type=click.STRING, help="The name of the training job")
@click.option(
    "--namespace",
    type=click.STRING,
    default="kubeflow",
    help="The cluster's namespace to run training job",
)
@click.option(
    "--job-kind",
    type=click.STRING,
    default="kubeflow/PyTorchJob",
    help="The type of training job, currently only kubeflow/PytorchJob supported",
)
@click.option("--image", type=click.STRING, help="The docker container image used for training job")
@click.option(
    "--pull-policy",
    type=click.Choice([c.value for c in PullPolicy]),
    default=PullPolicy.IF_NOT_PRESENT.value,
    help="Policy to pull container image",
)
@click.option(
    "--entry-script",
    type=click.STRING,
    default="./train.py",
    help="The training docker container entry script",
)
@click.option(
    "--command",
    type=click.STRING,
    default="torchrun",
    help="The command to run entry script. Currently, only 'torchrun' supported",
)
@click.option("--script-args", type=click.STRING, help="The arguments list for entry script")
@click.option(
    "--results-dir",
    type=click.STRING,
    default="./result",
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
    "--node-count", type=click.INT, help="The number of nodes to run distributed training job"
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
@click.option("--queue-name", type=click.STRING, help="The name of the Kueue")
@click.option("--priority", type=click.STRING, help="The priority of the training job")
@click.option(
    "--auto-resume",
    type=click.BOOL,
    default=False,
    help="Whether enable auto-resume for the training job",
)
@click.option(
    "--max-retry",
    type=click.INT,
    default=1,
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
def start_job(
    config_name: Optional[str],
    config_path: Optional[str],
    name: Optional[str],
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
):
    # TODO: Support more job kinds and command

    validator = JobValidator()
    if not validator.validate_submit_job_args(
        config_name,
        name,
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
    ):
        sys.exit(1)

    """Submit job with the provided configuration file or directly with CLI
    arguments."""
    if name is not None:
        config = yaml.safe_load(KUBERNETES_PYTORCH_JOB_TEMPLATE)
        try:
            # Update the configuration with provided arguments
            config["container"] = image
            config["cluster"]["instance_type"] = str(instance_type)[len("ml.") :]
            config["training_cfg"]["entry_script"] = entry_script
            config["training_cfg"]["run"]["name"] = name
            config["training_cfg"]["run"]["nodes"] = node_count
            config["env_vars"] = ENV_VARS_DICT if environment is None else environment

            if not _is_accelerator_instance_type(str(instance_type)) and tasks_per_node is None:
                config["training_cfg"]["run"]["ntasks_per_node"] = 8
            else:
                _override_or_remove(
                    config["training_cfg"]["run"], "ntasks_per_node", tasks_per_node
                )

            if label_selector is not None:
                config["cluster"]["cluster_config"]["label_selector"] = label_selector
            elif deep_health_check_passed_nodes_only:
                config["cluster"]["cluster_config"]["label_selector"] = DEEP_HEALTH_CHECK_PASSED_ONLY_NODE_AFFINITY_DICT
            else:
                config["cluster"]["cluster_config"]["label_selector"] = NODE_AFFINITY_DICT

            if auto_resume and max_retry is not None:
                annotations = {
                    HYPERPOD_AUTO_RESUME_ANNOTATION_KEY: auto_resume,
                    HYPERPOD_MAX_RETRY_ANNOTATION_KEY: max_retry,
                }
                config["cluster"]["cluster_config"]["annotations"] = annotations
            else:
                config["cluster"]["cluster_config"].pop("annotations")

            _override_or_remove(config["cluster"]["cluster_config"], "pullPolicy", pull_policy)
            _override_or_remove(
                config["cluster"]["cluster_config"], "restartPolicy", restart_policy
            )
            _override_or_remove(
                config["cluster"]["cluster_config"],
                "custom_labels",
                {KUEUE_QUEUE_NAME_LABEL_KEY: queue_name} if queue_name is not None else None,
            )
            _override_or_remove(
                config["cluster"]["cluster_config"], "priority_class_name", priority
            )
            _override_or_remove(config["training_cfg"], "script_args", script_args)
            _override_or_remove(config["cluster"]["cluster_config"], "namespace", namespace)
            _override_or_remove(config, "base_results_dir", results_dir)
        except Exception as e:
            logger.error(f"Config template has unexpected error: {e}")
            sys.exit(1)

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d-%H%M%S")
        filename = f"{HYPERPOD_KUBERNETES_JOB_PREFIX}-{timestamp}.yaml"
        with open(os.path.join(GENERATED_LAUNCHER_CONFIG_FILE_PATH, filename), "w") as file:
            yaml.dump(config, file, default_flow_style=False)

        logger.debug(
            f"Configuration file generated in: {GENERATED_LAUNCHER_CONFIG_FILE_PATH + filename}"
        )
        launcher_config_path = GENERATED_LAUNCHER_CONFIG_FILE_PATH
        launcher_config_file_name = filename
    else:
        """Submit job with the provided configuration file or directly with CLI
        arguments"""
        config_file_path = os.path.join(str(config_path), str(config_name))
        if not os.path.exists(config_file_path):
            logger.error(f"Configuration file {config_file_path} does not exist.")
            sys.exit(1)
        launcher_config_path = str(config_path)
        launcher_config_file_name = str(config_name)

    logger.debug(f"Submitting job with config {launcher_config_path}/{launcher_config_file_name}")

    # Initialize Hydra and call custom launcher with Hydra config to submit job
    try:
        with initialize_config_dir(config_dir=launcher_config_path, version_base="1.2"):
            cfg = compose(config_name=launcher_config_file_name)
            customer_launcher(cfg)
    except Exception as e:
        logger.error(f"Submitting job failed due to: {e}")
        sys.exit(1)
    finally:
        # Remove temporary created Launcher config file for submit via CLI argument case
        if name is not None and config_name is None:
            file_to_delete = os.path.join(launcher_config_path, launcher_config_file_name)
            if os.path.exists(file_to_delete):
                os.remove(file_to_delete)


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
