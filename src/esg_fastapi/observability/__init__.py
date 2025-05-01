"""Elevate the observability app for ease of import."""

from .main import observe
from .routes import app

__all__ = ["app", "observe"]
