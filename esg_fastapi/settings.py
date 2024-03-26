import sys
from types import ModuleType
from typing import Any, cast
from uuid import UUID

from pydantic import UUID4, Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClassModule:
    __path__ = []
    __file__ = __file__
    __cached__ = __cached__
    __spec__ = __spec__


class Settings(BaseSettings, ClassModule):
    model_config = SettingsConfigDict(env_prefix="ESG_FASTAPI_")

    @field_validator("*", mode="after")
    @classmethod
    def add_defaults_to_examples(cls, v: Any, info: ValidationInfo) -> Any:
        """If a Field has a default but no examples, use the default as an example."""
        current_field = cls.model_fields[info.field_name]  # type: ignore
        if current_field.examples is None and current_field.default is not None:
            current_field.examples = [current_field.default]
        return v

    # Globus functions are typed to accept UUIDs so use the coercion for validation
    # ref: https://github.com/globus/globus-sdk-python/blob/b6fa2edc7e81201494d150585078a99d3926dfc7/src/globus_sdk/_types.py#L18
    globus_search_index: UUID4 = Field(
        default=UUID("ea4595f4-7b71-4da7-a1f0-e3f5d8f7f062", version=4),
        title="Globus Search Index ID",
        description="The ID of the Globus Search Index queries will be submitted to. The default is the ORNL Globus Search Index.",
    )


sys.modules[__name__] = cast(ModuleType, Settings())
