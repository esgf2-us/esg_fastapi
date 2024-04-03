"""Create a Pydantic settings object that can be imported."""

import sys
from types import ModuleType
from typing import cast
from uuid import UUID

from pydantic import UUID4, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClassModule:
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


sys.modules[__name__] = cast(ModuleType, Settings())
