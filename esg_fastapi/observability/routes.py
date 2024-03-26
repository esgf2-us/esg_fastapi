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
    return ProbeResponse(status="live")


@app.get("/healthz/readiness", tags=["Kubernetes"])
async def readiness_probe() -> ProbeResponse:
    return ProbeResponse(status="ready")
