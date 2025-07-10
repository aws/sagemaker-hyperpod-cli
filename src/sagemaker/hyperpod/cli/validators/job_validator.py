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
import json
import os
import yaml
from yaml.loader import SafeLoader
from typing import Optional

from sagemaker.hyperpod.cli.clients.kubernetes_client import KubernetesClient
from sagemaker.hyperpod.cli.constants.command_constants import (
    KUEUE_WORKLOAD_PRIORITY_CLASS_LABEL_KEY,
    SAGEMAKER_TRAINING_LAUNCHER_DIR,
    RestartPolicy,
    KUEUE_QUEUE_NAME_LABEL_KEY,
    HYPERPOD_AUTO_RESUME_ANNOTATION_KEY,
    HYPERPOD_MAX_RETRY_ANNOTATION_KEY,
    INSTANCE_TYPE_LABEL,
    SchedulerType
)
from sagemaker.hyperpod.cli.constants.hyperpod_instance_types import (
    HyperpodInstanceType,
)
from sagemaker.hyperpod.cli.utils import setup_logger
from sagemaker.hyperpod.cli.validators.validator import (
    Validator,
)

logger = setup_logger(__name__)

RECIPES_DIR = os.path.join(SAGEMAKER_TRAINING_LAUNCHER_DIR, "recipes_collection/recipes")

class JobValidator(Validator):
    def __init__(self):
        super().__init__()

    def validate_start_job_args(
        self,
        config_file: Optional[str],
        job_name: Optional[str],
        node_count: Optional[int],
        instance_type: Optional[str],
        image: Optional[str],
        job_kind: Optional[str],
        command: Optional[str],
        label_selector: Optional[str],
        scheduler_type: Optional[str],
        queue_name: Optional[str],
        priority: Optional[str],
        auto_resume: bool,
        restart_policy: Optional[RestartPolicy],
        max_retry: Optional[int],
        namespace: Optional[str],
        entry_script: Optional[str],
        recipe: Optional[str] = None,
    ):
        if job_kind is not None and job_kind != "kubeflow/PyTorchJob":
            logger.error("The only supported 'job-kind' is 'kubeflow/PyTorchJob'.")
            return False

        if command is not None and command != "torchrun":
            logger.error("The only supported 'command' is 'torchrun'.")
            return False

        if scheduler_type is not None and scheduler_type not in SchedulerType.get_values():
            logger.error(f"The only supported 'scheduler_type' are {SchedulerType.get_values()}.")
            return False

        if config_file is not None and job_name is not None:
            logger.error(
                "Please provide only 'config-file' to submit job using custom script or 'job-name' to submit job via CLI arguments"
            )
            return False
        
        if config_file is not None and recipe is not None:
            logger.error(
                "Please provide only 'config-file' to submit job using custom script or 'recipe' for recipe-based jobs"
            )
            return False

        if config_file is None and job_name is None and recipe is None:
            logger.error(
                "Please provide either 'recipe' for recipe-based jobs or 'config-file' to submit job using config file or 'job-name' to submit job via CLI arguments"
            )
            return False

        if job_name is not None:
            if entry_script is None:
                logger.error("Please provide 'entry-script' for the training job")
                return False

            if node_count is None:
                logger.error(
                    "Please provide 'node-count' to specify number of nodes used for training job"
                )
                return False

            if image is None:
                logger.error(
                    "Please provide 'image' to specify the training image for training job"
                )
                return False

            if label_selector is not None:
                if not _validate_json_str(label_selector):
                    logger.error("Please provide valid 'label-selector' JSON string")
                    return False
                if not is_dict_str_list_str(json.loads(label_selector)):
                    logger.error(
                        "Please ensure 'label-selector' keys are string type and values are string or list of string type"
                    )
                    return False
            
            if not validate_scheduler_related_fields(scheduler_type, namespace, priority):
                return False
            
            return validate_hyperpod_related_fields(
                instance_type,
                queue_name,
                priority,
                auto_resume,
                restart_policy,
                max_retry,
                namespace
            )
        if recipe is not None:
            return validate_recipe_file(recipe)

        return True


def verify_and_load_yaml(file_path: str):
    if not os.path.exists(file_path):
        logger.error(f"Configuration file {file_path} does not exist.")
        return None
    try:
        with open(file_path, "r") as file:
            # Attempt to load the YAML file
            data = yaml.load(file, Loader=SafeLoader)
            return data
    except Exception as e:
        logger.error(
            f"The config file {file_path} is not a valid YAML file. Error: {e}"
        )
        return None


def validate_yaml_content(data):
    cluster_fields = data.get("cluster")
    if cluster_fields is None:
        logger.error("Please ensure 'cluster' field provided in the config file")
        return False
    cluster_type = cluster_fields.get("cluster_type")
    if cluster_type is None or cluster_type != "k8s":
        logger.error("Only support 'k8s' cluster type currently.")
        return False
    cluster_config_fields = cluster_fields.get("cluster_config")
    if cluster_config_fields is None:
        logger.error(
            "Please ensure 'cluster' contains 'cluster_config' field in the config file"
        )
        return False

    custom_labels = cluster_config_fields.get("custom_labels")
    annotations = cluster_config_fields.get("annotations")
    namespace = cluster_config_fields.get("namespace")
    scheduler_type = cluster_config_fields.get("scheduler_type", SchedulerType.get_default().value)

    if scheduler_type not in SchedulerType.get_values():
        logger.error(
            f"Unsupported scheduler type '{scheduler_type}', only {SchedulerType.get_values()} are allowed."
        )
        return False
    instance_type = cluster_fields.get("instance_type", None)
    queue_name = None
    if custom_labels is not None:
        queue_name = custom_labels.get(KUEUE_QUEUE_NAME_LABEL_KEY, None)

    label_selector = cluster_config_fields.setdefault("label_selector",{})
    required_labels = label_selector.get("required", {})
    preferred_labels = label_selector.get("preferred", {})

    if (
        not required_labels.get(INSTANCE_TYPE_LABEL) and
        not preferred_labels.get(INSTANCE_TYPE_LABEL)
    ):
        if "required" not in label_selector:
            label_selector["required"] = {}
        label_selector["required"][INSTANCE_TYPE_LABEL] = (
            [str(instance_type)]
        )

    auto_resume = False
    max_retry = None
    if annotations is not None:
        auto_resume = annotations.get(HYPERPOD_AUTO_RESUME_ANNOTATION_KEY, False)
        max_retry = annotations.get(HYPERPOD_MAX_RETRY_ANNOTATION_KEY, None)
        if auto_resume and (annotations.get(HYPERPOD_MAX_RETRY_ANNOTATION_KEY) is None):
            logger.error(
                f"Please provide both '{HYPERPOD_AUTO_RESUME_ANNOTATION_KEY}' "
                f"and '{HYPERPOD_MAX_RETRY_ANNOTATION_KEY}' "
                f"annotations to use Auto Resume feature"
            )
            return False

    priority = cluster_config_fields.get("priority_class_name", None)
    restart_policy = cluster_config_fields.get("restartPolicy", None)
    workload_priority = None

    if custom_labels is not None:
        workload_priority = custom_labels.get(KUEUE_WORKLOAD_PRIORITY_CLASS_LABEL_KEY, None)

    if not validate_scheduler_related_fields(scheduler_type, namespace, workload_priority):
        return False

    if not validate_hyperpod_related_fields(
        instance_type,
        queue_name,
        priority,
        auto_resume,
        restart_policy,
        max_retry,
        namespace,
    ):
        return False

    return True


def validate_hyperpod_related_fields(
    instance_type: Optional[str],
    queue_name: Optional[str],
    priority: Optional[str],
    auto_resume: bool,
    restart_policy: Optional[RestartPolicy],
    max_retry: Optional[int],
    namespace: Optional[str]
):
    logger.info(f"instance_type: {instance_type}, queue_name: {queue_name}, priority: {priority}, auto_resume: {auto_resume}, restart_policy: {restart_policy}, max_retry: {max_retry}, namespace: {namespace}")
    if instance_type is None:
        logger.error(
            "Please provide 'instance-type' to specify instance type for training job"
        )
        return False
    else:
        if instance_type not in [member.value for member in HyperpodInstanceType]:
            logger.error("Please provide SageMaker HyperPod supported 'instance-type'")
            return False

    if max_retry and not auto_resume:
        logger.error("Please enable 'auto_resume' with 'max_retry' option.")
        return False

    if auto_resume and restart_policy != RestartPolicy.ON_FAILURE.value:
        logger.error(
            "To enable 'auto_resume', please ensure the 'restart-policy' is 'OnFailure'. "
        )
        return False

    return True


def validate_scheduler_related_fields(
    scheduler_type: SchedulerType,
    namespace: Optional[str],
    priority: Optional[str],
): 
    if scheduler_type == SchedulerType.SAGEMAKER.value:
        k8s_client = KubernetesClient()
        sm_managed_namespace = k8s_client.get_sagemaker_managed_namespace(namespace)
        if namespace and not sm_managed_namespace:
            logger.error(
                f"Scheduler type is '{SchedulerType.SAGEMAKER.value}' however cannot find namespace '{namespace}' managed by SageMaker. Please ensure namespace exists and you have 'get' access to it."
            )
            return False

        if priority is not None :       
            priority_classes = [item['metadata']['name'] for item in k8s_client.list_workload_priority_classes()['items']]
            if priority not in priority_classes:
                logger.error(
                    f"Workload priority class '{priority}' is not found. Please ensure the priority exists and you have 'get' access to 'WorkloadPriorityClass'. Valid priority values are {priority_classes}."
                )
                return False
    return True

def validate_recipe_file(recipe: str):
    full_recipe_path = os.path.join(RECIPES_DIR, f"{recipe}.yaml")
    
    if os.path.exists(full_recipe_path) and os.path.isfile(full_recipe_path):
        logger.info(f"Recipe file found: {full_recipe_path}")
        return True
    
    logger.error(f"Recipe file '{recipe}.yaml' not found in {RECIPES_DIR}")
    return False

def is_dict_str_list_str(data: dict) -> bool:
    """
    Check if the given dictionary is of type Dict[str, List[str]].

    Parameters:
    data (dict): The dictionary to check.

    Returns:
    bool: True if the dictionary is of type Dict[str, List[str]], False otherwise.
    """
    for key, value in data.items():
        if not isinstance(value, list) and not isinstance(value, str):
            return False
        elif isinstance(value, list) and not all(
            isinstance(item, str) for item in value
        ):
            return False
    return True
def _validate_json_str(
    json_str: str,
):
    """
    Convert a JSON string to a dictionary.

    Parameters:
    json_string (str): A string in JSON format.

    Returns:
    dict: A dictionary representation of the JSON string.
    """
    try:
        # Attempt to convert the JSON string to a dictionary
        json.loads(json_str)
        return True
    except json.JSONDecodeError as e:
        # Handle JSON decoding errors
        logger.error(f"JSON decoding failed: {e}")
        return False
    except Exception as e:
        # Catch any other exceptions
        logger.error(f"An unexpected error occurred: {e}")
        return False