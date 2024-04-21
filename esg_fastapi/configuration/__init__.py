"""This module exists to contain the settings wiring and components.

Its been moved from the main init so that instrumentation can be setup as early as possible.
"""

from uuid import UUID

from pydantic import UUID4, Field
from pydantic_loggings.base import Logging as LoggingConfig
from pydantic_settings import BaseSettings, SettingsConfigDict

from esg_fastapi.configuration.gunicorn import GunicornSettings
from esg_fastapi.configuration.logging import ESGFLogging
from esg_fastapi.configuration.opentelemetry import OTELSettings


class UnifiedSettingsModel(BaseSettings):
    """An importable Pydantic Settings object."""

    model_config = SettingsConfigDict(env_prefix="ESG_FASTAPI_", env_nested_delimiter="__")

    gunicorn: GunicornSettings = Field(default_factory=GunicornSettings)
    logging: LoggingConfig = Field(default_factory=ESGFLogging)
    otel: OTELSettings = Field(default_factory=OTELSettings)

    # Globus functions are typed to accept UUIDs so use the coercion for validation
    # ref: https://github.com/globus/globus-sdk-python/blob/b6fa2edc7e81201494d150585078a99d3926dfc7/src/globus_sdk/_types.py#L18
    globus_search_index: UUID4 = Field(
        default=UUID("ea4595f4-7b71-4da7-a1f0-e3f5d8f7f062", version=4),
        title="Globus Search Index ID",
        description="The ID of the Globus Search Index queries will be submitted to. The default is the ORNL Globus Search Index.",
    )


settings = UnifiedSettingsModel()
