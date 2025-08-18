"""
Constants and enums for 404 error handling system.
"""

from enum import Enum


class ResourceType(Enum):
    """Direct template names for different resource types."""
    HYP_PYTORCH_JOB = "hyp_pytorch_job"
    HYP_CUSTOM_ENDPOINT = "hyp_custom_endpoint" 
    HYP_JUMPSTART_ENDPOINT = "hyp_jumpstart_endpoint"


class OperationType(Enum):
    """Types of operations that can trigger 404 errors."""
    DELETE = "delete"
    GET = "get"
    DESCRIBE = "describe"
    LIST = "list"


# Mapping from resource types to their corresponding list commands
RESOURCE_LIST_COMMANDS = {
    ResourceType.HYP_PYTORCH_JOB: "hyp list hyp-pytorch-job",
    ResourceType.HYP_CUSTOM_ENDPOINT: "hyp list hyp-custom-endpoint",
    ResourceType.HYP_JUMPSTART_ENDPOINT: "hyp list hyp-jumpstart-endpoint"
}

# Mapping from resource types to user-friendly display names
RESOURCE_DISPLAY_NAMES = {
    ResourceType.HYP_PYTORCH_JOB: "Job",
    ResourceType.HYP_CUSTOM_ENDPOINT: "Custom endpoint",
    ResourceType.HYP_JUMPSTART_ENDPOINT: "JumpStart endpoint"
}
