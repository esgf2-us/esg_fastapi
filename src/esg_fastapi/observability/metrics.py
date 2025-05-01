"""Functions and classes related to gathering metrics from the API."""

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

FACET_LABELS = ESGSearchQuery()._queriable_fields
GLOBAL_LABELS: list[str] = ["method", "path", "app_name", *FACET_LABELS]

ESG_FASTAPI = Info("fastapi_app_info", "FastAPI application information.").info(
    {
        "app_name": settings.app_id,
        "version": settings.app_version,
    }
)
EXCEPTIONS = Counter(
    "fastapi_exceptions_total",
    "Total count of exceptions raised by path and exception type",
    [*GLOBAL_LABELS, "exception_type"],
)
REQUESTS_IN_PROGRESS = Gauge(
    "fastapi_requests_in_progress",
    "Gauge of requests by method and path currently being processed",
    GLOBAL_LABELS,
)
REQUESTS = Counter(
    "fastapi_requests_total",
    "Total count of requests by method and path.",
    GLOBAL_LABELS,
)
RESPONSES = Counter(
    "fastapi_responses_total",
    "Total count of responses by method, path and status codes.",
    [*GLOBAL_LABELS, "status_code"],
)
REQUESTS_PROCESSING_TIME = Histogram(
    "fastapi_request_processing_time",
    "Histogram of requests processing time by path (in seconds)",
    GLOBAL_LABELS,
)


async def track_prometheus_metrics(request: Request, call_next: RequestResponseEndpoint) -> Response:
    """A middleware function that tracks Prometheus metrics for incoming requests and responses.

    Args:
        request (Request): The incoming request.
        call_next (RequestResponseEndpoint): The function to call to get the response for the request.

    Returns:
        Response: The response for the request.
    """
    request_labels = {"method": request.method, "path": request.url.path, "app_name": settings.app_id}
    request_facets = {field: request.query_params.get(field) for field in FACET_LABELS}
    stack = ExitStack()
    REQUESTS.labels(**request_labels, **request_facets).inc()
    with stack:
        # Start a timer for the request.
        stack.enter_context(REQUESTS_PROCESSING_TIME.labels(**request_labels, **request_facets).time())
        # Mark the request as in progress.
        stack.enter_context(REQUESTS_IN_PROGRESS.labels(**request_labels, **request_facets).track_inprogress())

        # Call the next middleware in the stack.
        response = await call_next(request)

        # Mark the response as complete.
        RESPONSES.labels(**request_labels, **request_facets, status_code=response.status_code).inc()
        return response


async def track_exceptions(request: Request, exc: Exception) -> None:
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
    request_labels = {
        "method": request.method,
        "path": request.url.path,
        "exception_type": exc,
        "app_name": settings.app_id,
    }
    request_facets = {field: request.query_params.get(field) for field in FACET_LABELS}
    EXCEPTIONS.labels(**request_labels, **request_facets).inc()
    if handler := request.app.exception_handlers.get(exc):
        return await handler(request, exc)
    else:
        raise exc
