"""Entry point for running the API with the embedded Gunicorn server."""

import pyroscope
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pyroscope.otel import PyroscopeSpanProcessor

from esg_fastapi import settings

from .api.main import app_factory

# TODO: more accurate init: https://opentelemetry-python.readthedocs.io/en/latest/api/trace.html#opentelemetry.trace.TracerProvider
provider = TracerProvider()
provider.add_span_processor(PyroscopeSpanProcessor())

otlp_exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(span_processor)

trace.set_tracer_provider(provider)
pyroscope.configure(**settings.pyroscope.model_dump(mode="json"))

app = app_factory()
