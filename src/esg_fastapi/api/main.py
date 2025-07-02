"""This module defines the main FastAPI application factory."""

from httpx import HTTPStatusError
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from esg_fastapi.api.globus import FastAPIWithSearchClient, handle_upstream_http_status_error, handle_upstream_timeout, token_renewal_watchdog
from esg_fastapi.observability.main import observe
from esg_fastapi.api.routes import router

def app_factory() -> FastAPIWithSearchClient:
    """Create the FastAPI application and mount the sub-applications."""
    api = FastAPIWithSearchClient(
        title="ESGF FastAPI",
        summary="An adapter service to translate and execute ESGSearch queries on a Globus Search Index.",
        description="# Long form CommonMark content\n---\nTODO: source this from the same place as the python package description?",
        lifespan=token_renewal_watchdog,
    )

    api.include_router(router, tags=["Search"])
    FastAPIInstrumentor.instrument_app(app=api)

    api.add_exception_handler(TimeoutError, handle_upstream_timeout)
    api.add_exception_handler(HTTPStatusError, handle_upstream_http_status_error)

    observe(api)
    return api
