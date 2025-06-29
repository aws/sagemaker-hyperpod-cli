from .v1_0.model import PyTorchJobConfig  # Import your model
from typing import Dict, Type
from pydantic import BaseModel

# Direct version-to-model mapping
SCHEMA_REGISTRY: Dict[str, Type[BaseModel]] = {
    "1.0": PyTorchJobConfig,
}