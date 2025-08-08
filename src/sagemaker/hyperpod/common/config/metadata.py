from typing import Dict, Optional
from pydantic import Field, BaseModel


class Metadata(BaseModel):
    """Metadata class"""

    name: str = Field(
        description="The name of the Kubernetes resource. Must follow RFC1123 naming conventions: lowercase alphanumeric characters or hyphens, start and end with alphanumeric character, 1-63 characters long (e.g., 'my-pytorch-job-123')."
    )
    namespace: Optional[str] = Field(
        default=None,
        description="The Kubernetes namespace where the resource will be created. If not specified, uses the default namespace or the namespace configured in your cluster context.",
    )
    labels: Optional[Dict[str, str]] = Field(
        default=None,
        description="Labels are key value pairs that are attached to objects, such as Pod. Labels are intended to be used to specify identifying attributes of objects. The system ignores labels that are not in the service's selector. Labels can only be added to objects during creation.",
    )
    annotations: Optional[Dict[str, str]] = Field(
        default=None,
        description="Annotations are key-value pairs that can be used to attach arbitrary non-identifying metadata to objects.",
    )
