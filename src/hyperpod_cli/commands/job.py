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
import shlex
from typing import Any, Dict, Optional, List, Tuple

import click
import yaml
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
    SAGEMAKER_TRAINING_LAUNCHER_DIR,
    PullPolicy,
    RestartPolicy,
    PersistentVolumeClaim,
    Volume,
)
from hyperpod_cli.clients.kubernetes_client import (
    KubernetesClient,
)

# Add the private sagemaker training launcher to the sys path
if 'SAGEMAKER_TRAINING_LAUNCHER_DIR' not in os.environ:
    os.environ['SAGEMAKER_TRAINING_LAUNCHER_DIR'] = SAGEMAKER_TRAINING_LAUNCHER_DIR

launcher_dir = os.environ['SAGEMAKER_TRAINING_LAUNCHER_DIR']
if launcher_dir not in sys.path:
    sys.path.append(launcher_dir)

from main import main as customer_launcher

from hyperpod_cli.service.cancel_training_job import (
    CancelTrainingJob,
)
from hyperpod_cli.service.get_training_job import (
    GetTrainingJob,
)
from hyperpod_cli.service.list_pods import (
    ListPods,
)
from hyperpod_cli.service.list_training_jobs import (
    ListTrainingJobs,
)
from hyperpod_cli.templates.k8s_pytorch_job_template import (
    KUBERNETES_PYTORCH_JOB_TEMPLATE,
)
from hyperpod_cli.utils import (
    setup_logger,
    set_logging_level,
)
from hyperpod_cli.validators.job_validator import (
    JobValidator,
)

logger = setup_logger(__name__)

@click.command()
@click.option(
    "--job-name",
    type=click.STRING,
    required=False,
    help="Required. The name of the job to see the details of.",
)
@click.option(
    "--namespace",
    "-n",
    type=click.STRING,
    required=False,
    help="Optional. The namespace to describe the job in. If not provided, the CLI will try to describe the job in the namespace set by the user while connecting to the cluster. If provided, and the user has access to the namespace, the CLI will describe the job from the specified namespace.",
)
@click.option(
    "--verbose",
    type=click.BOOL,
    is_flag=True,
    default=False,
    required=False,
    help="Optional. If set to `True`, the command enables verbose mode and prints out more detailed output with additional fields.",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode",
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
    help="Optional. The namespace to list the jobs in. If not provided, this command lists the jobs in the namespace specified during connecting to the cluster. If the namespace is provided and if the user has access to the namespace, this command lists the jobs from the specified namespace.",
)
@click.option(
    "--all-namespaces",
    "-A",
    type=click.BOOL,
    is_flag=True,
    default=False,
    required=False,
    help="Optional. If set, this command lists jobs from all namespaces the data scientist users have access to. The namespace in the current AWS account credentials will be ignored, even if specified with the `--namespace` option.",
)
@click.option(
    "--selector",
    "-l",
    type=click.STRING,
    required=False,
    help="Optional. A label selector to filter the listed jobs. The selector supports the '=', '==', and '!=' operators (e.g., `-l key1=value1,key2=value2`).",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode",
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
    help="Required. The name of the job to list pods for.",
)
@click.option(
    "--namespace",
    "-n",
    type=click.STRING,
    required=False,
    help="Optional. The namespace to list the pods in. If not provided, the CLI will list the pods in the namespace set by the user while connecting to the cluster. If provided, and the user has access to the namespace, the CLI will list the pods from the specified namespace.",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode",
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
    help="Required. The name of the job to cancel.",
)
@click.option(
    "--namespace",
    "-n",
    type=click.STRING,
    required=False,
    help="Optional. The namespace to cancel the job in. If not provided, the CLI will try to cancel the job in the namespace set by the user while connecting to the cluster. If provided, and the user has access to the namespace, the CLI will cancel the job from the specified namespace.",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode",
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
    help="Optional. Specify the K8s job config file to submit a training job. You should pass the absolute path to the file or the file in the current folder. If you use this, you don't need to specify any other options.",
)
@click.option(
    "--job-name",
    type=click.STRING,
    help="The name of the training job",
)
@click.option(
    "--namespace",
    "-n",
    type=click.STRING,
    help="Optional. The namespace to use. If not specified, this command uses the [Kubernetes namespace](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) of the Amazon EKS cluster associated with the SageMaker HyperPod cluster in your AWS account.",
)
@click.option(
    "--job-kind",
    type=click.STRING,
    default="kubeflow/PyTorchJob",
    help="Optional. The training job kind. The job types currently supported are `kubeflow` and `PyTorchJob`.",
)
@click.option(
    "--image",
    type=click.STRING,
    help="Required. The image used when creating the training job.",
)
@click.option(
    "--pull-policy",
    type=click.Choice([c.value for c in PullPolicy]),
    default=PullPolicy.IF_NOT_PRESENT.value,
    help="Optional. The policy to pull the container image. Valid values are `Always`, `IfNotPresent`, and `Never`, as available from the PyTorchJob. The default is `Always`.",
)
@click.option(
    "--entry-script",
    type=click.STRING,
    help="Required. The path to the training script.",
)
@click.option(
    "--command",
    type=click.STRING,
    default="torchrun",
    help="Optional. The command to run the entrypoint script. Currently, only `torchrun` is supported.",
)
@click.option(
    "--script-args",
    type=click.STRING,
    help="The list of arguments for entryscripts.",
)
@click.option(
    "--results-dir",
    type=click.STRING,
    default="./results",
    help="Optional. The location to store the results, checkpoints, and logs. The cluster admin users should set this up and provide it to the data scientist users. The default value is `./results`.",
)
@click.option(
    "--environment",
    type=click.STRING,
    help="Optional. The environment variables (key-value pairs) to set in the containers.",
)
@click.option(
    "--instance-type",
    type=click.STRING,
    help="Required. The instance type to launch the job on. Note that the instance types you can use are the available instances within your SageMaker quotas for instances prefixed with `ml`.",
)
@click.option(
    "--node-count",
    type=click.INT,
    help="Required. The number of nodes (instances) to launch the jobs on.",
)
@click.option(
    "--tasks-per-node",
    type=click.INT,
    help="Optional. The number of devices to use per instance.",
)
@click.option(
    "--label-selector",
    type=click.STRING,
    help="Optional. A dictionary of labels and their values that will override the predefined node selection rules based on the HyperPod `node-health-status` label and values. If users provide this field, the CLI will launch the job with this customized label selection.",
)
@click.option(
    "--scheduler-type",
    type=click.STRING,
    default="Kueue",
    help="Optional. The scheduler type to use. Currently, only `Kueue` is supported.",
)
@click.option(
    "--queue-name",
    type=click.STRING,
    help="Optional. The name of the queue to submit the job to, which is created by the cluster admin users in your AWS account.",
)
@click.option(
    "--priority",
    type=click.STRING,
    help="Optional. The priority for the job, which needs to be created by the cluster admin users and match the name in the cluster.",
)
@click.option(
    "--auto-resume",
    type=click.BOOL,
    default=False,
    help="Optional. The flag to enable HyperPod resilience job auto resume. If set to `true`, the job will automatically resume after pod or node failure. To enable `auto-resume`, you also should set `restart-policy` to `OnFailure`.",
)
@click.option(
    "--max-retry",
    type=click.INT,
    help="Optional. The maximum number of retries for HyperPod resilience job auto resume. If `auto-resume` is set to true and `max-retry` is not specified, the default value is 1.",
)
@click.option(
    "--restart-policy",
    type=click.Choice([c.value for c in RestartPolicy]),
    default=RestartPolicy.ON_FAILURE.value,
    help="Optional. The PyTorchJob restart policy, which can be `Always`, `OnFailure`, `Never`, or `ExitCode`. The default is `OnFailure`. To enable `auto-resume`, `restart-policy` should be set to `OnFailure`.",
)
@click.option(
    "--deep-health-check-passed-nodes-only",
    type=click.BOOL,
    default=False,
    help="Optional. If set to `true`, the job will be launched only on nodes that have the `deep-health-check-status` label with the value `passed`.",
)
@click.option(
    "--service-account-name",
    type=click.STRING,
    required=False,
    help="Optional. The Kubernetes service account that allows Pods to access resources based on the permissions granted to that service account. The cluster admin users should create the Kubernetes service account.",
)
@click.option(
    "--persistent-volume-claims",
    type=click.STRING,
    required=False,
    help="Optional. The pre-created persistent volume claims (PVCs) that the data scientist can choose to mount to the containers. The cluster admin users should create PVCs and provide it to the data scientist users.",
)
@click.option(
    "--volumes",
    type=click.STRING,
    required=False,
    help="Optional. Add a temp directory for containers to store data in the hosts."
    " <volume_name>:</host/mount/path>:</container/mount/path>,<volume_name>:</host/mount/path1>:</container/mount/path1>",
)
@click.option(
    "--recipe",
    type=click.STRING,
    required=False,
    help = """Optional. Recipe which accelerates distributed training jobs.
            Current supported recipes are as follows: \n
            fine-tuning/llama/hf_llama3_8b_seq8192_gpu \n
            fine-tuning/llama/hf_llama3_8b_seq8192_gpu_lora \n
            fine-tuning/llama/hf_llama3_70b_seq8192_gpu_lora \n
            fine-tuning/llama/hf_llama3_405b_seq8192_gpu_qlora \n
            fine-tuning/llama/hf_llama3_405b_seq131072_gpu_qlora \n
            training/llama/hf_llama3_7B_config_trainium \n
            training/llama/hf_llama3_8b_seq8192_gpu \n
            training/llama/llama2_7b_nemo \n
            training/llama/megatron_llama_7B_config \n
            training/mistral/hf_mistral_gpu \n
            training/mixtral/hf_mixtral_gpu \n
            """
)
@click.option(
    "--override-parameters",
    type=click.STRING,
    help="""Optional. Override parameters for the recipe. Format: 'key1=value1 key2=value2 ...'
    hyperpod start-job --recipe fine-tuning/llama/hf_llama3_8b_seq8192_gpu --override-parameters \
'{
  "+cluster.persistent_volume_claims.0.claimName":"fsx-claim",
  "+cluster.persistent_volume_claims.0.mountPath":"data",
  "recipes.run.name": "name",
  "recipes.exp_manager.exp_dir": "/data/llama8b",
  "recipes.trainer.num_nodes": 1,
  "recipes.model.num_hidden_layers": 4,
  "recipes.model.num_attention_heads": 8,
  "recipes.model.max_context_width": 8192,
  "recipes.model.max_position_embeddings": 8192,
  "recipes.model.train_batch_size": 1,
  "recipes.model.data.use_synthetic_data": true,
  "instance_type": "g5.48xlarge",
  "cluster": "k8s",
  "cluster_type": "k8s",
  "container": "container link",
  "recipes.model.data.train_dir": "/data/datasets/wikicorpus_llama3_tokenized_8k/",
  "recipes.model.data.val_dir": "/data/datasets/wikicorpus_llama3_tokenized_8k_val/",
}'
    """,
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode",
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
    recipe: Optional[str],
    override_parameters: Optional[str],
    debug: bool,
):
    if debug:
        set_logging_level(logger, logging.DEBUG)
        os.environ['HYDRA_FULL_ERROR'] = '1'

    # Perform Post-Processing parameter validations
    # TODO: refactor validate_start_job_args to use Click ctx
    ctx = click.get_current_context()
    validate_only_config_file_argument(ctx)

    validator = JobValidator()
    if not validator.validate_aws_credential(boto3.Session()):
        logger.error("Cannot start Training job due to AWS credentials issue")
        sys.exit(1)

    #if not namespace and config_file is None:
    #    k8s_client = KubernetesClient()
    #    namespace = k8s_client.get_current_context_namespace()
    
    launcher_config_path = None
    launcher_config_file_name = None

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
        recipe,
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
    elif config_file is not None:
        """Start job with the provided configuration file"""
        if os.path.isabs(config_file):
            abs_config_file_path = config_file
        else:
            abs_config_file_path = os.path.abspath(config_file)
        if not validator.validate_start_job_config_yaml(abs_config_file_path):
            sys.exit(1)
        config_path, config_name = os.path.split(abs_config_file_path)
        launcher_config_path = str(config_path)
        launcher_config_file_name = str(config_name)

    start_training_job(recipe, override_parameters, job_name, config_file, launcher_config_path, launcher_config_file_name)

    #console_link = utils.get_cluster_console_url()
    #print(json.dumps({"Console URL": console_link}, indent=1, sort_keys=False))


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


def validate_only_config_file_argument(ctx):
    # Get all the arguments passed to the command
    all_args = ctx.params

    # Filter out None values and arguments that has default values
    provided_args = {
        k: v
        for k, v in all_args.items()
        if v is not None
        and ctx.get_parameter_source(k) != click.core.ParameterSource.DEFAULT
    }

    # If config-file provided with other arguments, raise an error
    if len(provided_args) > 1 and "config_file" in provided_args:
        raise click.BadParameter(
            f"Please only provide 'config-file' argument if you want to start job with .yaml file."
        )


def execute_command(cmd, env=None):
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
        logger.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        logger.error(e.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(1)


def start_training_job(recipe, override_parameters, job_name, config_file, launcher_config_path=None, launcher_config_file_name=None):
    env = os.environ.copy()
    env['HYDRA_FULL_ERROR'] = '1'

    if recipe is None:
        logger.debug(f"Starting job with config {launcher_config_path}{launcher_config_file_name}")
        cmd = [
            'python3',
            f'{SAGEMAKER_TRAINING_LAUNCHER_DIR}/main.py',
            f'--config-path={launcher_config_path}',
            f'--config-name={launcher_config_file_name}',
        ]
        execute_command(cmd, env)
    else:
        cmd = [
            'python3',
            f'{SAGEMAKER_TRAINING_LAUNCHER_DIR}/main.py',
            f'recipes={recipe}',
            'cluster=k8s',
            'cluster_type=k8s',
            f'base_results_dir={os.path.abspath(os.path.join(os.getcwd(), "results"))}'
        ]
        print(override_parameters)
        if override_parameters:
            try:
                # Parse the JSON string into a dictionary
                override_dict = json.loads(override_parameters)
                
                # Convert the dictionary into key=value pairs
                for key, value in override_dict.items():
                    if isinstance(value, str):
                        # Ensure strings are properly quoted
                        cmd.append(f'{key}="{value}"')
                    else:
                        cmd.append(f'{key}={value}')
            except json.JSONDecodeError as e:
                print(f"Invalid JSON format: {e}")
                return
        
        # For debugging: Print out the final command to check formatting
        print(f"Final command: {' '.join(cmd)}")
        
        execute_command(cmd, env)

    if job_name is not None and config_file is None:
        file_to_delete = os.path.join(launcher_config_path, launcher_config_file_name)
        if os.path.exists(file_to_delete):
            os.remove(file_to_delete)


