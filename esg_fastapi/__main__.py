"""Entry point for running the API with the embedded Gunicorn server."""

from typing import Self

from fastapi import FastAPI
from gunicorn.app.base import BaseApplication
from gunicorn.arbiter import Arbiter

from esg_fastapi import settings

from . import api


class Server(BaseApplication):
    """Wrapper around a WSGI app that Gunicorn's Arbiter can manage."""

    def load_config(self: Self) -> None:
        """Transfer settings from our settings module to the Gunicorn settings object."""
        for field in settings.gunicorn.model_fields:
            # TODO: until we can fully build the model dynamically, we only set
            # settings from model_fields that are named in the native Gunicorn
            # settings object, that way we can use other properties on the model
            # without Gunicorn throwing unknown setting errors. For example, having
            # `host` and `port` properties used to build the `bind` property.
            if field in self.cfg.settings:
                self.cfg.set(field, getattr(settings.gunicorn, field))

    def load(self: Self) -> FastAPI:
        """Instantiate the app from the factory function.

        We use a factory function instead of importing an instantiated app so that Gunicorn can reload
        the app on the fly as needed.
        """
        return api.wsgi_factory()


Arbiter(Server()).run()
