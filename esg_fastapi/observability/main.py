from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from .routes import app as observability_app


def observe(measured_app: FastAPI) -> None:
    metrics = Instrumentator()
    metrics.instrument(measured_app)
    metrics.expose(observability_app)
    measured_app.mount("/observability", observability_app)
    measured_app.router.include_router(observability_app.router)
