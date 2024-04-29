from functools import partial
from multiprocessing import cpu_count
from pathlib import Path
from tempfile import mkdtemp
from typing import Annotated, Callable, Optional

from annotated_types import T
from gunicorn.arbiter import Arbiter
from gunicorn.workers.base import Worker
from pydantic import BaseModel, Field, IPvAnyAddress, ValidationInfo, field_validator

from esg_fastapi.api.versions.v1.models import Stringified

from .logging import LogLevels

ValidatedDefault = Annotated[T, Field(validate_default=True)]

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


class GunicornSettings(BaseModel):
    """Settings for the Gunicorn web server."""

    # Fields used for calculation of other Guincorn settings,
    # but not actually passed directly to Gunicorn
    workers_per_core: int = 1
    web_concurrency: int = 0
    max_workers: int = 1
    host: Optional[IPvAnyAddress] = Field(default="0.0.0.0")  # noqa: S104 -- primarily used for k8s so default to making that easier
    port: Optional[int] = 1337

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
    preload_app: bool = True

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
        host = info.data["host"]
        port = info.data["port"]
        if host and port:
            return f"{info.data['host']}:{info.data['port']}"
        raise ValueError(
            "Could not determine a binding address for the Gunicorn server. "
            "Please provide a value for either 'bind' or both 'host' and 'port'."
        )
