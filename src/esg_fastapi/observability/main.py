from fastapi import FastAPI
from prometheus_client import make_asgi_app
from starlette.middleware.base import BaseHTTPMiddleware

from .metrics import track_exceptions, track_prometheus_metrics
from .routes import app as observability_app


def observe(measured_app: FastAPI) -> FastAPI:
    measured_app.add_middleware(BaseHTTPMiddleware, dispatch=track_prometheus_metrics)
    measured_app.add_exception_handler(Exception, track_exceptions)
    measured_app.mount("/observability", observability_app)
    measured_app.mount("/metrics", make_asgi_app())
    measured_app.router.include_router(observability_app.router)
    return measured_app
