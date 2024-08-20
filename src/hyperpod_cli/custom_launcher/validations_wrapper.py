from functools import wraps
from typing import TypeVar, Any, Callable, cast

from omegaconf import DictConfig

from .launcher.config_validator.value_validator import ValueValidator
from .launcher.config_validator.type_validator import TypeValidator

_T = TypeVar("_T", bound=Callable[..., Any])


def validate_config(fn: _T) -> _T:
    @wraps(fn)
    def validations_wrapper(config: DictConfig, *args, **kwargs) -> DictConfig:
        """
        Execute all validations in this function
        """
        type_validator = TypeValidator(config)
        type_validator.validate()
        schema_validator = ValueValidator(config)
        schema_validator.validate()

        return fn(config, *args, **kwargs)

    return cast(_T, validations_wrapper)
