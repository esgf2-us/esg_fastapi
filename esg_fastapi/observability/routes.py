"""Routes related to the Observability component."""

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest
from prometheus_client.multiprocess import MultiProcessCollector

from .models import ProbeResponse

app = FastAPI(
    title="Observability",
    summary="Endpoints used for observability of the system.",
    description="# Long form CommonMark content\n---\nTODO: Create a discription for the Observability sub-service.",
    openapi_tags=[
        {
            "name": "Kubernetes",
            "description": "Provide information to the Kubernetes controller.",
            "externalDocs": {
                "description": "Kubernetes Probe Documentation",
                "url": "https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/",
            },
        },
    ],
)

app.router.tags = ["Observability"]


@app.get("/healthz/liveness", tags=["Kubernetes"])
async def liveness_probe() -> ProbeResponse:
    """Reports liveness status to Kubernetes controller.

    Returns:
        ProbeResponse: {'status': 'live'}
    """
    return ProbeResponse(status="live")


@app.get("/healthz/readiness", tags=["Kubernetes"])
async def readiness_probe() -> ProbeResponse:
    """Reports liveness status to Kubernetes controller.

    Returns:
        ProbeResponse: {'status': 'ready'}
    """
    return ProbeResponse(status="ready")


@app.get("/metrics")
def metrics_route(request: Request, response: Response) -> Response:
    """Endpoint that serves Prometheus metrics."""
    ephemeral_registry = CollectorRegistry()
    MultiProcessCollector(ephemeral_registry)
    return Response(
        content=generate_latest(ephemeral_registry),
        headers={"Content-Type": CONTENT_TYPE_LATEST},
    )
