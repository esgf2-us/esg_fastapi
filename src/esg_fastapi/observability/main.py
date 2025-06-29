from fastapi import FastAPI, Request, Response
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.propagate import inject
from prometheus_client import make_asgi_app
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from .metrics import track_exceptions, track_prometheus_metrics
from .routes import app as observability_app


async def return_trace_context(request: Request, call_next: RequestResponseEndpoint) -> Response:
    response: Response = await call_next(request)
    inject(response.headers)
    return response


def observe(measured_app: FastAPI) -> FastAPI:
    measured_app.add_middleware(BaseHTTPMiddleware, dispatch=return_trace_context)
    measured_app.add_middleware(BaseHTTPMiddleware, dispatch=track_prometheus_metrics)
    measured_app.add_exception_handler(Exception, track_exceptions)
    measured_app.mount("/observability", observability_app)
    measured_app.mount("/metrics", make_asgi_app())
    measured_app.router.include_router(observability_app.router)
    HTTPXClientInstrumentor().instrument()
    return measured_app
