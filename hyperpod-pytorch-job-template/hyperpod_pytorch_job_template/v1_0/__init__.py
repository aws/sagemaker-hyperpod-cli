from .model import PyTorchJobConfig

def validate(data: dict):
    return PyTorchJobConfig(**data)


__all__ = ["validate", "PyTorchJobConfig"]