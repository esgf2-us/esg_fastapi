"""Globus Search client and supporting components."""

import asyncio
import logging
from typing import Literal, Optional

from fastapi import FastAPI
from hishel import AsyncCacheClient, AsyncInMemoryStorage, Controller
from httpx import Response
from httpx._types import AuthTypes
from opentelemetry import trace

from esg_fastapi import settings
from esg_fastapi.api.versions.v1.models import GlobusSearchQuery
from esg_fastapi.api.versions.v1.types import GlobusToken, GlobusTokenResponse

logger = logging.getLogger(__name__)


async def globus_timings(response: Response) -> None:
    """Response extension hook to parse Globus Search's `server-timing` header and return the timings in an extension."""
    server_sent_timings = response.headers.get("server-timing", "")
    if server_sent_timings:
        response.extensions["globus_timings"] = {}
        for pair in server_sent_timings.split(","):
            measurement, _ = pair.split(";")
            metric, value = measurement.split("=")
            response.extensions["globus_timings"][metric] = float(value) * 1000  # convert from sec (Globus) to ms (Solr)


class ThinSearchClient:
    """Light-weight, cache-enable, async alternative to the globus-sdk `SearchClient`."""

    def __init__(self) -> None:
        """Initializes the caching httpx client."""
        self.client = AsyncCacheClient(
            storage=AsyncInMemoryStorage(ttl=300),
            controller=Controller(cacheable_methods=["POST"]),
            event_hooks={"response": [globus_timings]},
        )
        self.search_url = f"https://search.api.globus.org/v1/index/{settings.globus.globus_search_index}/search"
        self.refresh_token: Optional[str] = None
        self.access_token: Optional[str] = None

    @property
    def auth_header(self) -> dict[Literal["Authorization"], str]:
        """Return a Bearer Token Authorization header."""
        return {"Authorization": f"Bearer {self.access_token}"}

    async def search(self, query: GlobusSearchQuery, **kwargs: dict) -> Response:
        """Search the Globus Index with the given `GlobusSearchQuery`."""
        data = query.model_dump(exclude_none=True)
        logger.debug(f"Issuing search query: {data}")

        headers = kwargs.get("headers", {}) | {"Content-Type": "application/json"}
        if self.access_token:
            headers |= self.auth_header

        tracer = trace.get_tracer("esg_fastapi")
        with tracer.start_as_current_span("globus_search"):
            return await self.client.post(self.search_url, data=data, headers=headers, extensions={"force_cache": True})


def find_search_token(token_response: GlobusTokenResponse) -> GlobusToken:
    """Parse a `GlobusTokenResponse` and find the token for search.api.globus.org."""
    if token_response["resource_server"] == "search.api.globus.org":
        return token_response
    for token in token_response["other_tokens"]:
        if token["resource_server"] == "search.api.globus.org":
            return token
    raise RuntimeError("Token response did not contain a search token")


class FastAPIWithSearchClient(FastAPI):
    """FastAPI app with a globus_client."""

    def __init__[**P](self, *args: P.args, **kwargs: P.kwargs) -> None:
        """Initializes the FastAPI app with a Globus Search client."""
        super().__init__(*args, **kwargs)
        self.globus_client = ThinSearchClient()


async def _renew_token(app: FastAPIWithSearchClient, auth: AuthTypes) -> int:
    logger.debug("Renewing Globus Search token")
    token_response = await app.globus_client.client.post(
        "https://auth.globus.org/v2/oauth2/token",
        auth=auth,
        extensions={"cache_disabled": True},
    )
    search_token: GlobusToken = find_search_token(token_response.json())
    app.globus_client.access_token = search_token["access_token"]
    app.globus_client.refresh_token = search_token["refresh_token"]
    return search_token["expires_in"]


async def token_renewal_watchdog(app: FastAPIWithSearchClient) -> None:
    """Trade app credentials for access/refresh tokens if they are set."""
    if settings.globus.globus_client_id and settings.globus.globus_client_secret:
        app_credentials = (settings.globus.globus_client_id, settings.globus.globus_client_secret)
        next_renewal = await _renew_token(app, app_credentials) - 60  # seconds
        logger.debug(f"Scheduling next token renewal in {next_renewal} seconds")
        loop = asyncio.get_event_loop()
        loop.call_later(next_renewal, _renew_token, app, app_credentials)
