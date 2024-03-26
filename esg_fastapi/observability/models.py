from typing import Literal

from pydantic import BaseModel


class ProbeResponse(BaseModel):
    status: Literal["ready", "live"]
