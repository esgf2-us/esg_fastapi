"""This module exists to contain the settings wiring and components.

Its been moved from the main init so that instrumentation can be setup as early as possible.
"""

from pydantic_loggings.base import Logging as LoggingConfig
from pydantic_settings import BaseSettings, SettingsConfigDict

from esg_fastapi.configuration.globus import GlobusSettings
from esg_fastapi.configuration.logging import ESGFLogging
from esg_fastapi.configuration.opentelemetry import OTELSettings
from esg_fastapi.configuration.profiling import Pyroscope


class UnifiedSettingsModel(BaseSettings):
    """An importable Pydantic Settings object."""

    model_config = SettingsConfigDict(env_prefix="ESG_FASTAPI_", env_nested_delimiter="__")

    pyroscope: Pyroscope = Pyroscope()
    logging: LoggingConfig = ESGFLogging()
    otel: OTELSettings = OTELSettings()
    globus: GlobusSettings = GlobusSettings()


settings = UnifiedSettingsModel()
