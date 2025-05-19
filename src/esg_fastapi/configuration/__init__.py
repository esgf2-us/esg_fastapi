"""This module exists to contain the settings wiring and components.

Its been moved from the main init so that instrumentation can be setup as early as possible.
"""

from importlib.metadata import version
from typing import Optional
from uuid import UUID

from pydantic import UUID4, Field
from pydantic_loggings.base import Logging as LoggingConfig
from pydantic_settings import BaseSettings, SettingsConfigDict

from esg_fastapi.api.versions.v1.types import SemVer
from esg_fastapi.configuration.logging import ESGFLogging
from esg_fastapi.configuration.opentelemetry import OTELSettings
from esg_fastapi.configuration.profiling import Pyroscope

DEFAULT_GLOBUS_SEARCH_INDEX = "a8ef4320-9e5a-4793-837b-c45161ca1845"


class UnifiedSettingsModel(BaseSettings):
    """An importable Pydantic Settings object."""

    model_config = SettingsConfigDict(env_prefix="ESG_FASTAPI_", env_nested_delimiter="__")
    app_id: str = "esg_fastapi"
    app_version: SemVer = Field(default=version("esg_fastapi"))

    pyroscope: Pyroscope = Pyroscope(application_name=app_id)
    logging: LoggingConfig = ESGFLogging(service_name=app_id)
    otel: OTELSettings = OTELSettings(otel_service_name=app_id)

    # Client Credentials
    globus_client_id: Optional[str] = None
    globus_client_secret: Optional[str] = None

    # Globus functions are typed to accept UUIDs so use the coercion for validation
    # ref: https://github.com/globus/globus-sdk-python/blob/b6fa2edc7e81201494d150585078a99d3926dfc7/src/globus_sdk/_types.py#L18
    globus_search_index: UUID4 = Field(
        default=UUID(DEFAULT_GLOBUS_SEARCH_INDEX, version=4),
        title="Globus Search Index ID",
        description="The ID of the Globus Search Index queries will be submitted to. The default is the ORNL Globus Search Index.",
    )


settings = UnifiedSettingsModel()
