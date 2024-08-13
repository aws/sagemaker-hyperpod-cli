import json
from typing import Optional

from hyperpod_cli.constants.command_constants import RestartPolicy
from hyperpod_cli.constants.hyperpod_instance_types import HyperpodInstanceType
from hyperpod_cli.utils import setup_logger
from hyperpod_cli.validators.validator import Validator

logger = setup_logger(__name__)


class JobValidator(Validator):
    def __init__(self):
        super().__init__()

    def validate_submit_job_args(
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
    ):
        if job_kind is not None and job_kind != "kubeflow/PyTorchJob":
            logger.error("The only supported 'job-kind' is 'kubeflow/PyTorchJob'.")
            return False

        if command is not None and command != "torchrun":
            logger.error("The only supported 'command' is 'torchrun'.")
            return False

        if scheduler_type is not None and scheduler_type != "Kueue":
            logger.error("The only supported 'scheduler_type' is 'Kueue'.")
            return False

        if (queue_name is None and priority is not None) or (
            queue_name is not None and priority is None
        ):
            logger.error("Must provide both or neither of 'queue_name' and 'priority'.")
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
            if node_count is None:
                logger.error(
                    "Please provide 'node-count' to specify number of nodes used for training job"
                )
                return False

            if instance_type is None:
                logger.error(
                    "Please provide 'instance-type' to specify instance type for training job"
                )
                return False

            else:
                if instance_type not in [member.value for member in HyperpodInstanceType]:
                    logger.error("Please provide SageMaker HyperPod supported 'instance-type'")
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

            if auto_resume and restart_policy != RestartPolicy.ON_FAILURE.value:
                logger.error(
                    "To enable 'auto_resume', please ensure the 'restart-policy' is 'OnFailure'. "
                )
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
        elif isinstance(value, list) and not all(isinstance(item, str) for item in value):
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
