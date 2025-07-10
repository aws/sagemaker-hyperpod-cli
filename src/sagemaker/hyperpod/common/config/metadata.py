from typing import Dict, Optional
from pydantic import Field, BaseModel


class Metadata(BaseModel):
    """Metadata class"""

    name: str = Field(
        description="Name must match the name of one entry in pod.spec.resourceClaims of the Pod where this field is used. It makes that resource available inside a container."
    )
    namespace: Optional[str] = Field(
        default=None,
        description="Name must match the name of one entry in pod.spec.resourceClaims of the Pod where this field is used. It makes that resource available inside a container.",
    )
    labels: Optional[Dict[str, str]] = Field(
        default=None,
        description="Labels are key value pairs that are attached to objects, such as Pod. Labels are intended to be used to specify identifying attributes of objects. The system ignores labels that are not in the service's selector. Labels can only be added to objects during creation. More info: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    )
