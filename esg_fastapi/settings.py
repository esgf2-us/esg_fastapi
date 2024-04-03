"""Create a Pydantic settings object that can be imported."""

import sys
from types import ModuleType
from typing import TYPE_CHECKING
from uuid import UUID

from annotated_types import T
from pydantic import UUID4, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def type_of(baseclass: T) -> T:
    """Inherit from `baseclass` only for type checking purposes.

    This allows informing type checkers that the inheriting class ducktypes
    as the given `baseclass` without actually inheriting from it.

    Notes:
    - `typing.Protocol` is the right answer to this problem, but `sys.modules.__setitem__`
      currently checks for the ModuleType directly rather than a Protocol.
    - `pydantic_settings.BaseSettings` can't inherit from `ModuleType` due to conflicts
      in its use of `__slots__`
    """
    if TYPE_CHECKING:
        return baseclass
    return object


class ClassModule(type_of(ModuleType)):
    """Mixin class that allows a subclass to pretend to be a Module.

    This isn't required for the class to be used as intended, but these
    attributes make the class instance adhere to the PEP module interface.
    """

    __path__ = []
    __file__ = __file__
    __cached__ = __cached__
    __spec__ = __spec__


class Settings(BaseSettings, ClassModule):
    """An importable Pydantic Settings object."""

    model_config = SettingsConfigDict(env_prefix="ESG_FASTAPI_")

    # Globus functions are typed to accept UUIDs so use the coercion for validation
    # ref: https://github.com/globus/globus-sdk-python/blob/b6fa2edc7e81201494d150585078a99d3926dfc7/src/globus_sdk/_types.py#L18
    globus_search_index: UUID4 = Field(
        default=UUID("ea4595f4-7b71-4da7-a1f0-e3f5d8f7f062", version=4),
        title="Globus Search Index ID",
        description="The ID of the Globus Search Index queries will be submitted to. The default is the ORNL Globus Search Index.",
    )


sys.modules[__name__] = Settings()
