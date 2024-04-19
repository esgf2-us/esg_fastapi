"""Create a Pydantic settings object that can be imported."""

import sys
from functools import partial
from multiprocessing import cpu_count
from pathlib import Path
from tempfile import mkdtemp
from typing import TYPE_CHECKING, Annotated, Callable, Self
from uuid import UUID

from annotated_types import T
from gunicorn.arbiter import Arbiter
from gunicorn.workers.base import Worker
from opentelemetry.instrumentation.logging import DEFAULT_LOGGING_FORMAT as OTEL_DEFAULT_LOGGING_FORMAT
from pydantic import (
    UUID4,
    BaseModel,
    Field,
    IPvAnyAddress,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic_loggings.base import Formatter, Handler
from pydantic_loggings.base import Logger as LoggerModel
from pydantic_loggings.base import Logging as LoggingConfig
from pydantic_loggings.types_ import OptionalModel, OptionalModelDict
from pydantic_settings import BaseSettings, SettingsConfigDict

from esg_fastapi.api.versions.v1.models import Stringified
from esg_fastapi.utils import ClassModule, LogLevels, opentelemetry_init

# TODO: we should be able to build this dynamically, but I gave up on figuring out the typing
# def map_annotation(setting: Setting) -> type:
#     type_mapping = {
#         int: int,
#         str: str,
#         callable: Callable,
#         auto_int: Annotated[int, BeforeValidator(auto_int)],
#         None: str,
#     }
#     return type_mapping[setting.type]

# GunicornSettings = create_model(
#     "GunicornSettings",
#     __config__=None,
#     __doc__=None,
#     __base__=BaseModel,
#     __module__=__name__,
#     __cls_kwargs__=None,
#     __validators__={setting.name: setting.validator for setting in KNOWN_SETTINGS},
#     __slots__=None,
#     **{
#         setting.name: (
#             map_annotation(setting),
#             FieldInfo(
#                 title=setting.name,
#                 default=setting(),
#                 description=setting.desc,
#             ),
#         )
#         for setting in KNOWN_SETTINGS
#     },
# )

ValidatedDefault = Annotated[T, Field(validate_default=True)]


class GunicornSettings(BaseModel):
    """Settings for the Gunicorn web server."""

    # Fields used for calculation of other Guincorn settings,
    # but not actually passed directly to Gunicorn
    workers_per_core: int = 1
    web_concurrency: int = 0
    max_workers: int = 0
    host: IPvAnyAddress = Field(default="0.0.0.0")  # noqa: S104 -- primarily used for k8s so default to making that easier
    port: int = 8080

    # Actual Gunicorn config variables
    workers: ValidatedDefault[int] = 0
    worker_class: str = "uvicorn.workers.UvicornWorker"
    worker_tmp_dir: Stringified[Path] = Field(default_factory=partial(mkdtemp, prefix="/dev/shm/"))  # noqa: S108 -- `mkdtemp` is secure, we need to ensure a memory-backed tmp or the worker threads will hang waiting on disk i/o
    loglevel: LogLevels = Field(default="INFO")
    errorlog: Path = Field(default="-")
    accesslog: Path = Field(default="-")
    graceful_timeout: int = 120
    timeout: int = 120
    keepalive: int = 5
    bind: ValidatedDefault[str] = Field(default=None)
    reload: bool = True
    default_proc_name: str = "ESG-Fastapi"
    post_fork: Callable[[Arbiter, Worker], None] = opentelemetry_init

    @field_validator("workers", mode="before")
    @classmethod
    def calculate_workers(cls, value: int, info: ValidationInfo) -> int:
        """Calculate the number of workers for the Gunicorn server.

        Parameters:
        - value (int): The initial value provided for the 'workers' field.
        - info (ValidationInfo): An object containing information about the current validation process.

        Returns:
        - int: The final value for the 'workers' field after applying the validation logic.

        The method first checks if a value has been provided for 'workers'. If not, it attempts to retrieve the value from the 'web_concurrency' or 'max_workers' fields in the info.data dictionary.
        If neither of these fields has a value, the method calculates the number of workers based on the number of CPU cores and rounds the result to the nearest integer, with a minimum value of 2.
        """
        return (
            value
            or info.data["web_concurrency"]
            or info.data["max_workers"]
            or round(max(info.data["workers_per_core"] * cpu_count(), 2))
        )

    @field_validator("bind", mode="before")
    @classmethod
    def get_binding_addr(cls, value: str | None, info: ValidationInfo) -> str:
        """Determine the binding address for the Gunicorn server.

        Parameters:
        - value (str): The initial value provided for the 'bind' field.
        - info (ValidationInfo): An object containing information about the current validation process.

        Returns:
        - str: The final value for the 'bind' field after applying the validation logic.

        The method first checks if a value has been provided for 'bind'. If not, it attempts to retrieve the value from the 'host' and 'port' fields in the info.data dictionary.
        If the 'host' and 'port' fields are not provided, raise a ValueError with an appropriate error message.
        """
        if value is not None:
            return value
        if "host" in info.data and "port" in info.data:
            return f"{info.data['host']}:{info.data['port']}"
        raise ValueError(
            "Could not determine a binding address for the Gunicorn server. "
            "Please provide a value for either 'bind' or both 'host' and 'port'."
        )


class ESGFLogging(LoggingConfig):
    """Python's logging DictConfig represented as a typed and validated Pydantic model."""

    formatters: OptionalModelDict[Formatter] = {
        "otel": Formatter.model_validate(
            {
                "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
                "style": "%",
                "format": OTEL_DEFAULT_LOGGING_FORMAT,
            }
        )
    }
    handlers: OptionalModelDict[Handler] = {
        "stdout": Handler.model_validate({"formatter": "otel", "stream": "ext://sys.stdout"}),
        "stderr": Handler.model_validate({"formatter": "otel", "stream": "ext://sys.stderr"}),
    }
    loggers: OptionalModelDict[LoggerModel] = {
        "uvicorn": {"handlers": ["stdout"]},
        "uvicorn.access": {"handlers": ["stdout"]},
        "uvicorn.error": {"handlers": ["stderr"]},
        "gunicorn.access": {"handlers": ["stdout"]},
        "gunicorn.error": {"handlers": ["stderr"]},
    }
    root: OptionalModel[LoggerModel] = LoggerModel.model_validate(
        {"handlers": ["stdout"], "level": "INFO", "propagate": True}
    )

    @model_validator(mode="after")
    def configure_logger(self: Self) -> Self:
        """Abuse the model validation system to ensure the logger is configured as soon as the model is validated."""
        self.configure()
        return self


class Settings(BaseSettings, ClassModule):
    """An importable Pydantic Settings object."""

    model_config = SettingsConfigDict(env_prefix="ESG_FASTAPI_", env_nested_delimiter="__")

    gunicorn: GunicornSettings = Field(default_factory=GunicornSettings)
    logging: LoggingConfig = Field(default_factory=ESGFLogging)

    # Globus functions are typed to accept UUIDs so use the coercion for validation
    # ref: https://github.com/globus/globus-sdk-python/blob/b6fa2edc7e81201494d150585078a99d3926dfc7/src/globus_sdk/_types.py#L18
    globus_search_index: UUID4 = Field(
        default=UUID("ea4595f4-7b71-4da7-a1f0-e3f5d8f7f062", version=4),
        title="Globus Search Index ID",
        description="The ID of the Globus Search Index queries will be submitted to. The default is the ORNL Globus Search Index.",
    )


sys.modules[__name__] = Settings()
# Static checkers don't see the __getattr__ method on the instance, so we have to explicitly expose
# properties at the module level.
if TYPE_CHECKING:  # pragma: no cover
    globus_search_index = Settings.globus_search_index
    gunicorn: GunicornSettings = Settings.gunicorn
    logging: LoggingConfig = Settings.logging
