"""Globus Search client and supporting components."""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Literal

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from hishel import AsyncCacheClient, AsyncInMemoryStorage, Controller
from httpx import HTTPStatusError, Response, TimeoutException
from opentelemetry import trace
from starlette import status

from esg_fastapi import settings
from esg_fastapi.api.models import GlobusSearchQuery
from esg_fastapi.api.types import GlobusToken, GlobusTokenResponse
from esg_fastapi.observability.metrics import CACHE_HITS
from esg_fastapi.utils import get_current_trace_id

logger = logging.getLogger(__name__)


async def globus_timings(response: Response) -> None:
    """Response extension hook to parse Globus Search's `server-timing` header and return the timings in an extension."""
    server_sent_timings = response.headers.get("server-timing", "")
    if server_sent_timings:
        response.extensions["globus_timings"] = {}
        for pair in server_sent_timings.split(","):
            measurement, _ = pair.split(";")
            metric, value = measurement.split("=")
            response.extensions["globus_timings"][metric] = (
                # convert from sec (Globus) to ms (Solr)
                int(float(value) * 1000)
            )


async def cache_hits_metric(response: Response) -> None:
    """Response extension hook to increment the `CACHE_HITS` metric."""
    if response.extensions.get("from_cache"):
        CACHE_HITS.inc(exemplar={"TraceID": get_current_trace_id()})


class ThinSearchClient:
    """Light-weight, cache-enable, async alternative to the globus-sdk `SearchClient`."""

    def __init__(self) -> None:
        """Initializes the caching httpx client."""
        self.client = AsyncCacheClient(
            storage=AsyncInMemoryStorage(ttl=300),
            controller=Controller(cacheable_methods=["POST"]),
            event_hooks={"response": [globus_timings, cache_hits_metric]},
            timeout=60,  # Globus Search sometimes takes a while to respond, so we set a longer timeout
        )
        self.search_url = f"https://search.api.globus.org/v1/index/{settings.globus.search_index}/search"
        self.access_token: str | None = None

    @property
    def auth_header(self) -> dict[Literal["Authorization"], str]:
        """Return a Bearer Token Authorization header."""
        return {"Authorization": f"Bearer {self.access_token}"}

    async def search(self, query: GlobusSearchQuery, **kwargs: dict) -> Response:
        """Search the Globus Index with the given `GlobusSearchQuery`."""
        data = query.model_dump_json(exclude_none=True)
        logger.debug(f"Issuing search query: {data}")

        headers = kwargs.get("headers", {}) | {"Content-Type": "application/json"}
        if self.access_token:
            headers |= self.auth_header

        tracer = trace.get_tracer("esg_fastapi")
        with tracer.start_as_current_span("globus_search"):
            return (
                await self.client.post(self.search_url, content=data, headers=headers, extensions={"force_cache": True})
            ).raise_for_status()


def find_search_token(token_response: GlobusTokenResponse) -> GlobusToken:
    """Parse a `GlobusTokenResponse` and find the token for search.api.globus.org."""
    if token_response["resource_server"] == "search.api.globus.org":
        return token_response
    for token in token_response["other_tokens"]:
        if token["resource_server"] == "search.api.globus.org":
            return token
    raise RuntimeError("Token response did not contain a search token")


async def keep_token_fresh(app: FastAPI) -> None:
    """Keep the Globus Search token fresh by renewing it periodically."""
    while True:
        logger.info("Renewing Globus Search token")
        token_response = await app.state.globus_client.client.post(
            "https://auth.globus.org/v2/oauth2/token",
            auth=(settings.globus.client_id, settings.globus.client_secret),
            data={"grant_type": "client_credentials", "scope": "urn:globus:auth:scope:search.api.globus.org:search"},
            extensions={"cache_disabled": True},
        )
        search_token: GlobusToken = find_search_token(token_response.json())
        app.state.globus_client.access_token = search_token["access_token"]

        logger.debug("Will renew Globus Search token in %d seconds", settings.globus.token_renewal_interval)
        await asyncio.sleep(settings.globus.token_renewal_interval)


@asynccontextmanager
async def lifespan_manager(app: FastAPI) -> AsyncGenerator[None, Any]:
    """If Globus credentials are set, start a background task to keep the token fresh."""
    if settings.globus.client_id and settings.globus.client_secret:
        renewer = asyncio.create_task(keep_token_fresh(app))
    else:
        renewer = asyncio.Future()
        logger.warning("Globus client ID and secret not set, skipping token renewal.")

    yield

    renewer.cancel()


async def handle_upstream_timeout(_: Request, exc: TimeoutException) -> JSONResponse:
    """Handle timeout errors to the Globus Search service."""
    error_response = {
        "type": type(exc).__name__,
        "title": "Timeout While Connecting to Globus Search",
        "status": status.HTTP_504_GATEWAY_TIMEOUT,
        "detail": str(exc),
        "trace_id": get_current_trace_id(),
    }
    logger.error(json.dumps(error_response), exc_info=True)
    return JSONResponse(status_code=status.HTTP_504_GATEWAY_TIMEOUT, content=error_response)


async def handle_upstream_http_status_error(_: Request, exc: HTTPStatusError) -> JSONResponse:
    """Handle http status errors from the Globus Search service."""
    error_response = {
        "type": type(exc).__name__,
        "title": "HTTP Status Error While Connecting to Globus Search",
        "status": exc.response.status_code,
        "detail": str(exc),
        "trace_id": get_current_trace_id(),
    }
    logger.error(json.dumps(error_response), exc_info=True)
    return JSONResponse(status_code=exc.response.status_code, content=error_response)
