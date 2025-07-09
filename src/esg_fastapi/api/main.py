"""This module defines the main FastAPI application factory."""

from fastapi import FastAPI
from httpx import HTTPStatusError, TimeoutException
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from esg_fastapi.api.globus import (
    ThinSearchClient,
    handle_upstream_http_status_error,
    handle_upstream_timeout,
    lifespan_manager,
)
from esg_fastapi.api.routes import router
from esg_fastapi.observability.main import observe


def app_factory() -> FastAPI:
    """Create the FastAPI application and mount the sub-applications."""
    api = FastAPI(
        title="ESGF 1.5 Bridge API",
        summary="An adapter service to translate and execute ESGSearch queries on a Globus Search Index.",
        lifespan=lifespan_manager,
    )
    api.state.globus_client = ThinSearchClient()
    api.include_router(router, tags=["Search"])
    FastAPIInstrumentor.instrument_app(app=api)

    api.add_exception_handler(TimeoutException, handle_upstream_timeout)
    api.add_exception_handler(HTTPStatusError, handle_upstream_http_status_error)

    observe(api)
    return api
