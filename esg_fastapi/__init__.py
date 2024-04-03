"""A REST API for Globus-based searches that mimics esg-search.

This API is so that community tools that are based on the esg-search
RESTful API need not change to be compatible with the new Globus indices.
If you are designing a new project, you should look to use the globus-sdk
directly and this is only a small wrapper around the `post_search`
functionality. The standalone script does not need installed. You will
need FastAPI on which it is based and the Globus sdk.

python -m pip install fastapi[all] globus_sdk

This will also install Uvicorn (an ASGI web server implementation for Python).
This allows you to test this locally with:

uvicorn concept:app --reload


Questions:
- format: do we need to be able to return the two formats?
- distrib: how should this behave?
- latest: does not work with CMIP3
"""

from fastapi import FastAPI
from starlette.routing import Mount

from .api import versions
from .observability import app as observability_app

__all__ = ["api"]

api = FastAPI(
    title="ESGF FastAPI",
    summary="An adapter service to translate and execute ESGSearch queries on a Globus Search Index.",
    description="# Long form CommonMark content\n---\nTODO: source this from the same place as the python package description?",
)
api.mount("/observability", observability_app)

for version in versions.discovered:
    api.mount("/" + version.app.version, version.app)

for route in api.routes:
    if isinstance(route, Mount):
        api.router.include_router(route.app.router)
