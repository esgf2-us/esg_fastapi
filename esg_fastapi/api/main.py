from fastapi import FastAPI
from starlette.routing import Mount

from esg_fastapi.observability.main import observe


def app_factory() -> FastAPI:
    api = FastAPI(
        title="ESGF FastAPI",
        summary="An adapter service to translate and execute ESGSearch queries on a Globus Search Index.",
        description="# Long form CommonMark content\n---\nTODO: source this from the same place as the python package description?",
    )
    # Temporarily disable auto discovery while fixing circular imports
    # for version in discovered:
    #     api.mount("/" + version.app.version, version.app)

    from .versions.v1.routes import app_factory

    app = app_factory()
    api.mount("/" + app.version, app)
    # FastAPIInstrumentor.instrument_app(app)

    for route in api.routes:
        if isinstance(route, Mount):
            api.router.include_router(route.app.router)

    observe(api)
    # FastAPIInstrumentor.instrument_app(api)
    return api
