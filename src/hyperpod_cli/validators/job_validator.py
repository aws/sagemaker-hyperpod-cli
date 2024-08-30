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

from hyperpod_cli.constants.command_constants import (
    RestartPolicy,
    KUEUE_QUEUE_NAME_LABEL_KEY,
    HYPERPOD_AUTO_RESUME_ANNOTATION_KEY,
    HYPERPOD_MAX_RETRY_ANNOTATION_KEY,
    HYPERPOD_NAMESPACE_PREFIX,
)
from hyperpod_cli.constants.hyperpod_instance_types import HyperpodInstanceType
from hyperpod_cli.utils import setup_logger
from hyperpod_cli.validators.validator import Validator

logger = setup_logger(__name__)


class JobValidator(Validator):
    def __init__(self):
        super().__init__()

    def validate_start_job_args(
        self,
        config_name: Optional[str],
        name: Optional[str],
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
    ):
        # Hard coded validations. TODO: support more options for following fields
        if job_kind is not None and job_kind != "kubeflow/PyTorchJob":
            logger.error("The only supported 'job-kind' is 'kubeflow/PyTorchJob'.")
            return False

        if command is not None and command != "torchrun":
            logger.error("The only supported 'command' is 'torchrun'.")
            return False

        if scheduler_type is not None and scheduler_type != "Kueue":
            logger.error("The only supported 'scheduler_type' is 'Kueue'.")
            return False

        if config_name is not None and name is not None:
            logger.error(
                "Please provide only 'config-name' to submit job using config file or 'name' to submit job via CLI arguments"
            )
            return False

        if config_name is None and name is None:
            logger.error(
                "Please provide either 'config-name' to submit job using config file or 'name' to submit job via CLI arguments"
            )
            return False

        if name is not None:
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
            return validate_hyperpod_related_fields(
                instance_type,
                queue_name,
                priority,
                auto_resume,
                restart_policy,
                max_retry,
                namespace,
            )

        return True

    def validate_start_job_config_yaml(self, file):
        if not os.path.exists(file):
            logger.error(f"Configuration file {file} does not exist.")
            return False
        config_data = verify_and_load_yaml(file)
        if config_data is None:
            return False

        return validate_yaml_content(config_data)


def verify_and_load_yaml(file_path: str):
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

    instance_type = cluster_fields.get("instance_type", None)
    queue_name = None
    if custom_labels is not None:
        queue_name = custom_labels.get(KUEUE_QUEUE_NAME_LABEL_KEY, None)

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

    return validate_hyperpod_related_fields(
        instance_type,
        queue_name,
        priority,
        auto_resume,
        restart_policy,
        max_retry,
        namespace,
    )


def validate_hyperpod_related_fields(
    instance_type: Optional[str],
    queue_name: Optional[str],
    priority: Optional[str],
    auto_resume: bool,
    restart_policy: Optional[RestartPolicy],
    max_retry: Optional[int],
    namespace: Optional[str],
):
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

    if auto_resume and not _is_hyperpod_monitored_namespaces(namespace):
        logger.error(
            "Please ensure submit job to 'kubeflow' namespace or namespace with 'hyperpod' prefix to make 'auto-resume' work as expected "
        )
        return False

    if (queue_name is None and priority is not None) or (
        queue_name is not None and priority is None
    ):
        logger.error("Must provide both or neither of 'queue_name' and 'priority'.")
        return False
    return True


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


def _is_hyperpod_monitored_namespaces(
    namespace: Optional[str],
):
    if namespace is not None:
        if namespace.startswith(HYPERPOD_NAMESPACE_PREFIX) or namespace == "kubeflow":
            return True

    return False
