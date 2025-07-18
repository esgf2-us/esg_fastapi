from pydantic import AnyUrl, BaseModel

from esg_fastapi.utils import metadata


class Pyroscope(BaseModel):
    application_name: str = metadata["name"]

    server_address: AnyUrl = AnyUrl("http://localhost:4040")
    """Pyroscope server address"""

    sample_rate: int = 100
    """Pyroscope sample rate"""

    detect_subprocesses: bool = True
    """Detect subprocesses started by the main process."""

    oncpu: bool = False
    """Report CPU time only"""

    gil_only: bool = False
    """Only include traces for threads that are holding on to the Global Interpreter Lock"""

    enable_logging: bool = False
