"""This module exists to contain the settings wiring and components.

Its been moved from the main init so that instrumentation can be setup as early as possible.
"""

from pydantic import Field
from pydantic_extra_types.semantic_version import SemanticVersion
from pydantic_loggings.base import Logging as LoggingConfig
from pydantic_settings import BaseSettings, SettingsConfigDict

from esg_fastapi.configuration.globus import GlobusSettings
from esg_fastapi.configuration.logging import ESGFLogging
from esg_fastapi.configuration.opentelemetry import OTELSettings
from esg_fastapi.configuration.profiling import Pyroscope
from esg_fastapi.utils import package_version


class UnifiedSettingsModel(BaseSettings):
    """An importable Pydantic Settings object."""

    model_config = SettingsConfigDict(env_prefix="ESG_FASTAPI_", env_nested_delimiter="__")
    app_id: str = "esg_fastapi"
    app_version: SemanticVersion = Field(default_factory=package_version)

    pyroscope: Pyroscope = Pyroscope(application_name=app_id)
    logging: LoggingConfig = ESGFLogging(service_name=app_id)
    otel: OTELSettings = OTELSettings(otel_service_name=app_id)

    globus: GlobusSettings = GlobusSettings()


settings = UnifiedSettingsModel()
