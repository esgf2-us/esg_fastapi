"""Starting point/base for the ESG FastAPI service and it's versions and components."""

import time
from types import TracebackType
from typing import Optional, Self, Type

from fastapi import Depends, FastAPI
from globus_sdk import SearchClient

from esg_fastapi import settings

from .models import (
    ESGSearchQuery,
    ESGSearchResponse,
    GlobusFacet,
    GlobusMatchFilter,
    GlobusSearchQuery,
    GlobusSearchResult,
)

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
app.router.tags = ["v1"]

dependency_injector = Depends()


@app.get("/")
async def query_by_facets(
    esg_search_query: ESGSearchQuery = dependency_injector,
) -> ESGSearchResponse:
    """Search the ESGF Globus Search endpoint with a query and response compatible with the ESG Search API.

    Args:
        esg_search_query (ESGSearchQuery): A model instance representing the search query parameters.

    Returns:
        ESGSearchResponse: A model instance representing the search results, including the response header.
    """
    globus_query_args = {
        "q": esg_search_query.query,
        "limit": esg_search_query.limit,
        "offset": esg_search_query.offset,
    }

    if esg_search_query.facets:
        globus_query_args["facets"] = [
            GlobusFacet(name=facet, field_name=facet)
            for facet in esg_search_query.facets.split(",")
        ]

    globus_query_args["filters"] = [
        GlobusMatchFilter(field_name=key, values=value)
        for key, value in esg_search_query.model_dump(
            exclude_none=True,
            exclude={
                # These aren't treated as facets
                "query",
                "limit",
                "offset",
                "facets",
                # We haven't decided how to handle these yet
                "format",
                "distrub",
            },
        ).items()
    ]
    globus_query = GlobusSearchQuery.model_validate(globus_query_args)

    with Timer() as t:
        raw_globus_response = (
            SearchClient()
            .post_search(
                settings.globus_search_index, globus_query.model_dump(exclude_none=True)
            )
            .data
        )
        globus_response = GlobusSearchResult.model_validate(raw_globus_response)
    response_data = {
        "responseHeader": {
            "QTime": t.time,
            "params": {
                "q": esg_search_query.query,
                "start": globus_response.offset,
                "fq": [
                    f"{facet}:{value}"
                    for facet, value in esg_search_query.model_dump(
                        exclude_none=True,
                        exclude={
                            "query",
                            "limit",
                            "offset",
                            "format",
                            "facets",
                            "latest",
                        },
                    ).items()
                ],
            },
        },
        "response": {
            "numFound": globus_response.total,
            "start": globus_response.offset,
            "docs": [
                {**record.entries[0].content | {"id": record.subject}}
                for record in globus_response.gmeta
            ],
        },
    }

    if globus_response.facet_results is not None:
        response_data["responseHeader"]["params"]["facet_field"] = [
            result.name for result in globus_response.facet_results
        ]

    return ESGSearchResponse.model_validate(response_data)


class Timer:
    """Context manager for timing the seconds elapsed during a context.

    The `Timer` context manager is used to measure the time taken for a block of code to execute.

    Attributes:
        start_time (int): The start time of the context in nanoseconds.
        end_time (int): The end time of the context in nanoseconds.
        time (int): The time taken by the context in seconds.
    """

    def __enter__(self: Self) -> Self:
        """Open the context and start the timer.

        Returns:
            Timer: Exposes the start, end, and delta in seconds of the context.
        """
        self.start_time = time.monotonic_ns()
        return self

    def __exit__(
        self: Self,
        ex_typ: Optional[Type[BaseException]],
        ex_val: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Close the context and stop the timer."""
        self.end_time = time.monotonic_ns()
        self.time = int((self.end_time - self.start_time) // 1e9)
