"""API routes for version 1 of the ESG search Bridge API."""

import logging
from typing import Annotated

import httpx
import pyroscope
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from opentelemetry import trace
from starlette import status
from starlette.datastructures import Headers

from .models import (
    ESGSearchQuery,
    ESGSearchResponse,
    GlobusSearchQuery,
    GlobusSearchResult,
)

logger = logging.getLogger()

router = APIRouter()



def set_cache_control_headers(response: Response) -> None:
    """Set the cache-control directives for the response."""
    response.headers["cache-control"] = "public max-age=300 stale-while-revalidate=300 stale-if-error=300"


CacheControlHeaders = Depends(set_cache_control_headers)


def validate_cache_request_directives(response: httpx.Response, headers: Headers) -> None:
    """If the response was cached, check for cache-control directives that have require responses."""
    if not response.extensions["from_cache"]:
        return

    cache_key = response.extensions["cache_metadata"]["cache_key"]
    logger.debug(f"Cached response found for {cache_key}")

    if client_etag := headers.get("if-none-match"):
        logger.debug(f"Client sent if-none-match etag header {client_etag} vs {cache_key}")
        if cache_key == client_etag:
            logger.debug("Client etag matched")
            raise HTTPException(status.HTTP_304_NOT_MODIFIED)

    elif client_etag := headers.get("if-match"):
        logger.debug(f"Client sent if-match etag header {client_etag} vs {cache_key}")
        if cache_key != client_etag:
            logger.debug("Client etag did not match")
            raise HTTPException(status.HTTP_412_PRECONDITION_FAILED)


WITHOUT_ROWS = {"limit": 0}
WITHOUT_FACETS = {"facets": []}


@router.get("/search")
async def search(request: Request) -> RedirectResponse:
    """Redirects to the root path for esgf-pyclient compatibility."""
    destination = request.url_for("root").include_query_params(**request.query_params)
    return RedirectResponse(destination, status_code=status.HTTP_308_PERMANENT_REDIRECT)


@router.get("/", name="root", response_model=ESGSearchResponse, dependencies=[CacheControlHeaders])
async def search_globus(request: Request, q: Annotated[ESGSearchQuery, Query()]) -> ESGSearchResponse:
    """Allows searching the ESGF Globus Index using the same query requests and responses as the old Solr based ESG Search application."""
    tags = {key: str(value) for key, value in q.model_dump(exclude_none=True).items()}
    trace.get_current_span().set_attributes(tags)
    with pyroscope.tag_wrapper(tags):
        globus_query = GlobusSearchQuery.from_esg_search_query(q)

        # Globus Search is orders of magnitude faster when searching for rows or facets only vs rows and facets.
        # Its faster to do two separate queries and combine the results
        rows_query = globus_query.model_copy(update=WITHOUT_FACETS)
        rows_response = await request.app.globus_client.search(rows_query)

        validate_cache_request_directives(rows_response, request.headers)

        response_json = rows_response.json()

        if globus_query.facets:
            facets_query = globus_query.model_copy(update=WITHOUT_ROWS)
            facets_response = await request.app.globus_client.search(facets_query)
            response_json["facet_results"] = facets_response.json()["facet_results"]

        globus_result = GlobusSearchResult.model_validate(response_json)

        return ESGSearchResponse.from_results(q, rows_response.extensions["globus_timings"]["total"], globus_result)
