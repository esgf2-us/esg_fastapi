"""Configuration settings for Globus Search."""

from uuid import UUID

from pydantic import UUID4, BaseModel, Field


class GlobusSettings(BaseModel):
    """Settings related to Globus Search."""

    # Globus functions are typed to accept UUIDs so use the coercion for validation
    # ref: https://github.com/globus/globus-sdk-python/blob/b6fa2edc7e81201494d150585078a99d3926dfc7/src/globus_sdk/_types.py#L18
    search_index: UUID4 = Field(
        default=UUID("a8ef4320-9e5a-4793-837b-c45161ca1845", version=4),
        title="Globus Search Index ID",
        description="The ID of the Globus Search Index to which queries will be submitted. The default is the ORNL Globus Search Index.",
    )

    client_id: str | None = None
    client_secret: str | None = None

    token_renewal_interval: float = 60 * 60  # seconds
    """The interval in seconds at which the Globus Search token should be renewed."""
