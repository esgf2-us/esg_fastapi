"""The main package for the ESG FastAPI service."""

from fastapi import FastAPI
from starlette.routing import Mount

from esg_fastapi.api import versions
from esg_fastapi.observability.main import observe

# TODO: This doesn't _really_ belong in the init, but haven't found a better place yet


def wsgi_factory() -> FastAPI:
    api = FastAPI(
        title="ESGF FastAPI",
        summary="An adapter service to translate and execute ESGSearch queries on a Globus Search Index.",
        description="# Long form CommonMark content\n---\nTODO: source this from the same place as the python package description?",
    )
    for version in versions.discovered:
        api.mount("/" + version.app.version, version.app)

    for route in api.routes:
        if isinstance(route, Mount):
            api.router.include_router(route.app.router)

    observe(api)
    return api
