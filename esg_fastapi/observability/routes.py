"""Routes related to the Observability component."""

from fastapi import FastAPI

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
