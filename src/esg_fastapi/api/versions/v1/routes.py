"""API routes for version 1 of the ESG search Bridge API."""

import logging
from collections.abc import Generator
from contextvars import ContextVar
from typing import Any

import httpx
import pyroscope
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
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


def app_factory() -> FastAPI:
    app = FastAPI(
        version="v1",
        title="title",
        summary="summary",
        description="description",
        openapi_tags=[
            {
                "name": "v1",
                "description": "description",
            },
        ],
    )
    app.include_router(router)
    app.router.tags = ["v1"]
    FastAPIInstrumentor().instrument_app(app)
    return app


tracing_tags = ContextVar("tracing_tags")


def query_instrumentor(query: ESGSearchQuery = Depends()) -> Generator[ESGSearchQuery, Any, None]:
    """Instruments the query with tracing tags and pyroscope tags."""
    current_span: trace.Span = trace.get_current_span()
    tracing_tags.set({key: str(value) for key, value in query.model_dump(exclude_none=True).items()})
    current_span.set_attributes(tracing_tags.get())
    with pyroscope.tag_wrapper(tracing_tags.get()):
        yield query


TrackedESGSearchQuery: ESGSearchQuery = Depends(query_instrumentor)


def cache_control_response(response: Response) -> None:
    """Set the cache-control directives for the response."""
    response.headers["cache-control"] = "public max-age=300 stale-while-revalidate=300 stale-if-error=300"


def validate_cache_request_directives(response: httpx.Response, headers: Headers) -> None:
    """If the response was cached, check for cache-control directives that have require responses."""
    if response.extensions["from_cache"]:
        logger.debug("Cached response found")
        if client_etag := headers.get("if-none-match"):
            logger.debug("Client sent if-none-match etag header")
            if response.extensions["cache_metadata"]["cache_key"] == client_etag:
                logger.debug("Client etag matched")
                raise HTTPException(status.HTTP_304_NOT_MODIFIED)

        elif client_etag := headers.get("if-match"):
            logger.debug("Client sent if-match etag header")
            logger.debug(f"{client_etag} vs {response.extensions['cache_metadata']['cache_key']}")
            if response.extensions["cache_metadata"]["cache_key"] != client_etag:
                logger.debug("Client etag did not match")
                raise HTTPException(status.HTTP_412_PRECONDITION_FAILED)


WITHOUT_ROWS = {"limit": 0}
WITHOUT_FACETS = {"facets": []}


@router.get("/search")
async def search() -> RedirectResponse:
    """Redirects to the root path esgf-pyclient compatibility."""
    return RedirectResponse("/", status_code=status.HTTP_308_PERMANENT_REDIRECT)


@router.get("/", response_model=ESGSearchResponse, dependencies=[Depends(cache_control_response)])
async def search_globus(request: Request, q: ESGSearchQuery = TrackedESGSearchQuery) -> ESGSearchResponse:
    """This function performs a search using the Globus API based on the provided ESG search query.

    Parameters:
    - q (ESGSearchQuery): The ESG search query object.

    Returns:
    - ESGSearchResponse: A response object containing the search results from the Globus API.

    The function first constructs a Globus search query from the ESG query. It then sends a POST request to the Globus search endpoint with the constructed query.

    The function then constructs a response object from the received data, adhering to the format returned by ESG Search.

    The response object contains the following fields:
    - responseHeader: Contains information about the search query and its execution, such as the query time and the number of returned results.
    - response: Contains the actual search results, including the total number of results, the starting offset, and the actual search results.
    - facet_counts: Contains the counts of distinct values for each facet in the search results.
    """
    logger.info("Starting query")

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

    return ESGSearchResponse.model_validate(
        {
            "responseHeader": {
                "QTime": rows_response.extensions["globus_timings"]["total"],
                "params": {
                    "q": q.query,
                    "start": q.offset,
                    "rows": q.limit,
                    "fq": q,
                    "shards": f"esgf-data-node-solr-query:8983/solr/{q.type.lower()}s",
                },
            },
            "response": {
                "numFound": globus_result.total,
                "start": globus_result.offset,
                "docs": globus_result.gmeta,
            },
            "facet_counts": globus_result.facet_results,
        }
    )
