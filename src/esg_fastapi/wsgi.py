"""Entry point for running the API with the embedded Gunicorn server."""

import pyroscope
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SpanExporter
from pyroscope.otel import PyroscopeSpanProcessor

from esg_fastapi import settings

from .api.main import app_factory

EXPORTER_CLASS_MAP: dict[str, type[SpanExporter]] = {
    "otlp": OTLPSpanExporter,
    "console": ConsoleSpanExporter,
}

# TODO: more accurate init: https://opentelemetry-python.readthedocs.io/en/latest/api/trace.html#opentelemetry.trace.TracerProvider
provider = TracerProvider()
trace.set_tracer_provider(provider)
pyroscope.configure(**settings.pyroscope.model_dump(mode="json"))

if exporter := EXPORTER_CLASS_MAP.get(settings.otel.otel_traces_exporter):
    provider.add_span_processor(PyroscopeSpanProcessor())

    span_processor = BatchSpanProcessor(exporter())
    provider.add_span_processor(span_processor)

app = app_factory()
