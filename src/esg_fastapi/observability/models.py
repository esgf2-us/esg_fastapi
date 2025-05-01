"""Models related to the Observability component."""

from typing import Literal

from pydantic import BaseModel


class ProbeResponse(BaseModel):
    """Represents the possible response statuses of a Probe."""

    status: Literal["ready", "live"]
