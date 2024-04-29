from pydantic import AnyUrl, BaseModel
from pydantic_core import Url


class Pyroscope(BaseModel):
    application_name: str  # set by the parent model

    server_address: AnyUrl = Url("http://localhost:4040")
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

    # tags: dict[str, str] = {
    #     "region": '{os.getenv("REGION")}',
    # }

    # basic_auth_username: str = ""
    # basic_auth_password: str = ""
    # tenant_id: str = ""
