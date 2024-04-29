from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from starlette.routing import Mount

from esg_fastapi.observability.main import observe


def app_factory() -> FastAPI:
    api = FastAPI(
        title="ESGF FastAPI",
        summary="An adapter service to translate and execute ESGSearch queries on a Globus Search Index.",
        description="# Long form CommonMark content\n---\nTODO: source this from the same place as the python package description?",
    )

    FastAPIInstrumentor.instrument_app(app=api)

    from .versions.v1.routes import app_factory as v1_app_factory

    versions = [v1_app_factory]
    for app_factory in versions:
        app = app_factory()
        api.mount(f"/{app.version}", app)

    for route in api.routes:
        if isinstance(route, Mount) and isinstance(route.app, FastAPI):
            api.router.include_router(route.app.router)
            api.router.tags.extend(route.app.router.tags)

    observe(api)
    return api
