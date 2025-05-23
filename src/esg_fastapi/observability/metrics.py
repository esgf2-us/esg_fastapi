"""Functions and classes related to gathering metrics from the API."""

import logging
from contextlib import ExitStack

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
)
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from esg_fastapi import settings
from esg_fastapi.api.versions.v1.models import ESGSearchQuery
from esg_fastapi.utils import get_current_trace_id

logger = logging.getLogger(__name__)

ESG_FASTAPI = Info("fastapi_app", "FastAPI application information.").info(
    {
        "app_name": settings.app_id,
        "version": str(settings.app_version),
    }
)
EXCEPTIONS = Counter(
    "fastapi_exceptions_total",
    "Total count of exceptions raised by exception type",
    ["exception_type"],
)
REQUESTS_IN_PROGRESS = Gauge(
    "fastapi_requests_in_progress",
    "Gauge of requests currently being processed",
)
REQUESTS = Counter(
    "fastapi_requests_total",
    "Total count of requests",
)
RESPONSES = Counter(
    "fastapi_responses_total",
    "Total count of responses by status code.",
    ["status_code"],
)
REQUESTS_PROCESSING_TIME = Histogram(
    "fastapi_request_processing_time",
    "Histogram of requests processing time (in seconds)",
)

QUERY_FACETS = Counter(
    "esg_bridge_faceted_queries_total",
    "Total count of queries by facet",
    [facet for facet in ESGSearchQuery._queriable_fields()],
)

CACHE_HITS = Counter(
    "esg_bridge_cache_hits_total",
    "Total count of cache hits",
)

async def track_prometheus_metrics(request: Request, call_next: RequestResponseEndpoint) -> Response:
    """A middleware function that tracks Prometheus metrics for incoming requests and responses.

    Args:
        request (Request): The incoming request.
        call_next (RequestResponseEndpoint): The function to call to get the response for the request.

    Returns:
        Response: The response for the request.
    """
    if request.url.path.replace(request.scope["root_path"], "") != "/":
        # Only track metrics for the root path.
        return await call_next(request)

    trace_id = get_current_trace_id()

    request_facets = {field: request.query_params.get(field) for field in ESGSearchQuery._queriable_fields()}
    QUERY_FACETS.labels(**request_facets).inc(exemplar={"TraceID": trace_id})

    REQUESTS.inc(exemplar={"TraceID": trace_id})
    with ExitStack() as stack:
        # Start a timer for the request.
        stack.enter_context(REQUESTS_PROCESSING_TIME.time())
        # Mark the request as in progress.
        stack.enter_context(REQUESTS_IN_PROGRESS.track_inprogress())

        # Call the next middleware in the stack.
        response = await call_next(request)

        # Mark the response as complete.
        RESPONSES.labels(status_code=response.status_code).inc(exemplar={"TraceID": trace_id})
        return response


async def track_exceptions(request: Request, exc: Exception) -> Response:
    """FastAPI exception handler for tracking excpetion types in Prometheus metrics.

    If a handler is set for the exception type, it will be passed on to that handler, otherwise it will be re-raised.

    Args:
        request (Request): The incoming request object.
        exc (Exception): The exception object raised by the application.

    Returns:
        None: This function does not return a value.

    Raises:
        Exception: If no handler is found for the raised exception, it will be re-raised.
    """
    EXCEPTIONS.labels(exception_type=type(exc).__name__).inc(exemplar={"TraceID": get_current_trace_id()})
    if handler := request.app.exception_handlers.get(exc):
        return await handler(request, exc)
    else:
        raise exc
