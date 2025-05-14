"""Starting point/base for the ESG FastAPI service and it's versions and components."""

import logging
from collections.abc import Generator
from contextvars import ContextVar
from typing import Any

import pyroscope
import requests
from cachetools import TTLCache
from fastapi import APIRouter, Depends, FastAPI, Request
from globus_sdk import (
    AccessTokenAuthorizer,
    ClientApp,
    ConfidentialAppAuthClient,
    GlobusAppConfig,
    SearchClient
)
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from typing_extensions import TypedDict

from esg_fastapi import settings
from esg_fastapi.utils import Timer

from .models import (
    ESGSearchQuery,
    ESGSearchResponse,
    GlobusSearchQuery,
    GlobusSearchResult,
)

cache = TTLCache(maxsize=128, ttl=60)

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
    current_span: trace.Span = trace.get_current_span()
    tracing_tags.set({key: str(value) for key, value in query.model_dump(exclude_none=True).items()})
    current_span.set_attributes(tracing_tags.get())
    with pyroscope.tag_wrapper(tracing_tags.get()):
        yield query


TrackedESGSearchQuery: ESGSearchQuery = Depends(query_instrumentor)


def get_authorized_search_client() -> SearchClient:
    """Return a SearchClient authorized to search indicies."""
    app = ClientApp(
        "esg_search",
        client_id=settings.globus_client_id,
        client_secret=settings.globus_client_secret,
        config=GlobusAppConfig(token_storage="memory"),
    )
    return SearchClient(app=app)


@router.get("/")
def search_globus(q: ESGSearchQuery = TrackedESGSearchQuery) -> ESGSearchResponse:
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
    cache_key = q.model_dump_json()
    if cached_response := cache.get(cache_key):
        logger.debug("Returning response from cache")
        return ESGSearchResponse.model_validate(cached_response)

    # Globus Search is orders of magnitude faster when searching for rows or facets only vs rows and facets.
    # Its faster to do two separate queries and combine the results
    globus_query = GlobusSearchQuery.from_esg_search_query(q)
    globus_query_json = globus_query.model_dump(exclude_none=True)
    globus_rows_query = {**globus_query_json, "facets": []}  # request no facets
    globus_facets_query = {**globus_query_json, "limit": 0}  # request no rows

    globus_search_client = get_authorized_search_client()
    logger.debug(globus_query.model_dump(exclude_none=True))
    with Timer() as t:
        # TODO: OTEL will time this anyway -- can we get the time from it?
        tracer = trace.get_tracer("esg_fastapi")
        with tracer.start_as_current_span("globus_search"):
            with tracer.start_as_current_span("globus_rows_query"):
                rows_response = GlobusSearchResult.model_validate(
                    globus_search_client.post_search(settings.globus_search_index, globus_rows_query).data
                )
            with tracer.start_as_current_span("globus_rows_query"):
                facets_response = GlobusSearchResult.model_validate(
                    globus_search_client.post_search(settings.globus_search_index, globus_facets_query).data
                )

    esg_search_response = {
        "responseHeader": {
            "QTime": t.time,
            "params": {
                "q": q.query,
                "start": q.offset,
                "rows": q.limit,
                "fq": q,
                "shards": f"esgf-data-node-solr-query:8983/solr/{q.type.lower()}s",
            },
        },
        "response": {
            "numFound": rows_response.total,
            "start": rows_response.offset,
            "docs": rows_response.gmeta,
        },
        "facet_counts": facets_response.facet_results,
    }

    cache[cache_key] = esg_search_response
    return ESGSearchResponse.model_validate(esg_search_response)


class SearchParityFixture(TypedDict):
    """A dictionary containing the request, queries, and responses from both ESG and Globus searches.

    This allows us to test FastAPI version returns the same results as ESG Search, assuming the same result records
    were returned by the Globus search endpoint.

    Attributes:
        request (str): The raw HTTP query parameters used to generate the Globus and ESG Search responses.
        globus_query (GlobusSearchQuery): The Globus search query object constructed from the ESG query.
        globus_response (GlobusSearchResult): The response from the Globus search endpoint.
        esg_search_response (ESGSearchResponse): The response from the ESG search endpoint.
    """

    request: str
    globus_query: GlobusSearchQuery
    globus_response: GlobusSearchResult
    esg_search_response: ESGSearchResponse


@router.get("/make_fixture")
def make_fixture(raw_request: Request, q: ESGSearchQuery = TrackedESGSearchQuery) -> SearchParityFixture:
    """This function makes a fixture for comparing ESG and Globus search results.

    Parameters:
    - raw_request (Request): The raw HTTP request object.
    - q (ESGSearchQuery): The ESG search query object.

    Returns:
    - SearchParityFixture: A dictionary containing the request, queries, and responses from both ESG and Globus searches.

    The function first sends an HTTP GET request to the ESG search endpoint with the provided query parameters.
    It then constructs a Globus search query from the ESG query and sends a POST request to the Globus search endpoint.

    The function then constructs a theoretical response for the Globus search results, assuming that the ESG and Globus searches returned the same records.

    Finally, the function returns a dictionary containing the request, queries, and responses from both ESG and Globus searches.
    """
    esg_search_response = requests.get(  # noqa: S113 -- Only timeout if the globus call times out.
        "https://esgf-node.ornl.gov/proxy/search", params=q.model_dump(exclude_none=True)
    ).json()
    globus_query = GlobusSearchQuery.from_esg_search_query(q)
    globus_response = (
        SearchClient().post_search(settings.globus_search_index, globus_query.model_dump(exclude_none=True)).data
    )

    # Most test cases are unordered and so return different records between the globus and ESG searches.
    # Here, we throw away the actual globus results and construct a theoretical response of what it should
    # look like if the two searches had returned the same records.
    # TODO: would it be better to take the ESG result id's and add extra filters to the globus search to
    #       ensure it returns the same records?
    globus_response["gmeta"] = [
        {"subject": doc["id"], "entries": [{"content": doc, "entry_id": doc["type"], "matched_principal_sets": []}]}
        for doc in esg_search_response["response"]["docs"]
    ]

    return {
        "request": raw_request.scope["query_string"],
        "globus_query": GlobusSearchQuery.from_esg_search_query(q),
        "globus_response": globus_response,
        "esg_search_response": esg_search_response,
    }
