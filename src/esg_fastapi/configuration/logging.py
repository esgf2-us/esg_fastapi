"""This module configures logging for the ESGF FastAPI application, integrating with OpenTelemetry for enhanced tracing.

It defines a custom log record factory to include trace context in log messages, and sets up
structured logging using Pydantic models for configuration. The module provides a centralized
and type-safe way to manage logging formatters, handlers, and loggers, ensuring consistent
and informative logging across the application.
"""

import logging
from enum import Enum
from typing import Self

from opentelemetry import trace
from opentelemetry.instrumentation.logging import DEFAULT_LOGGING_FORMAT
from pydantic_loggings.base import Formatter, Handler
from pydantic_loggings.base import Logger as LoggerModel
from pydantic_loggings.base import Logging as LoggingConfig
from pydantic_loggings.types_ import OptionalModel, OptionalModelDict

from esg_fastapi.utils import metadata

LogLevels = Enum("LogLevels", logging.getLevelNamesMapping())

default_log_record_factory = logging.getLogRecordFactory()


def record_factory[**P](*args: P.args, **kwargs: P.kwargs) -> logging.LogRecord:
    """A factory function to create custom log records that include OpenTelemetry context.

    This function retrieves the current span context from OpenTelemetry and adds
    the service name, span ID, trace ID, and trace sampled flag to the log record.

    Args:
        *args: Variable length argument list.  Passed to the default log record factory.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        logging.LogRecord: A log record with added OpenTelemetry context attributes.
    """
    span = trace.get_current_span()
    ctx = span.get_span_context()
    record = default_log_record_factory(*args, **kwargs)

    record.otelServiceName = metadata["name"]
    record.otelSpanID = format(ctx.span_id, "016x")
    record.otelTraceID = format(ctx.trace_id, "032x")
    record.otelTraceSampled = ctx.trace_flags.sampled

    return record


class ESGFLogging(LoggingConfig):
    """Python's logging DictConfig represented as a typed and validated Pydantic model.

    This class extends `pydantic_loggings.base.Logging` to provide a structured
    configuration for Python's logging system, leveraging Pydantic for validation
    and type safety. It includes predefined formatters, handlers, and loggers tailored
    for the ESGF project, with specific attention to OpenTelemetry integration.

    Attributes:
        formatters (OptionalModelDict[Formatter]): A dictionary of log formatter configurations.
            Includes a default formatter "otel" that incorporates OpenTelemetry context.
        handlers (OptionalModelDict[Handler]): A dictionary of log handler configurations.
            Includes handlers "stdout" and "stderr" that use the "otel" formatter.
        loggers (OptionalModelDict[LoggerModel]): A dictionary of logger configurations.
            Configures "uvicorn" and "hishel.controller" loggers to use the "stdout" handler.
        root (OptionalModel[LoggerModel]): The root logger configuration, set to log to "stdout"
            at the INFO level and propagate logs to other loggers.
    """

    formatters: OptionalModelDict[Formatter] = {
        "otel": Formatter.model_validate(
            {
                "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
                "style": "%",
                "format": DEFAULT_LOGGING_FORMAT,
            },
        ),
    }
    handlers: OptionalModelDict[Handler] = {
        "stdout": Handler.model_validate({"formatter": "otel", "stream": "ext://sys.stdout"}),
        "stderr": Handler.model_validate({"formatter": "otel", "stream": "ext://sys.stderr"}),
    }
    loggers: OptionalModelDict[LoggerModel] = {
        "uvicorn": {"handlers": ["stdout"]},
        "hishel.controller": {"handlers": ["stdout"], "level": "INFO"},
        "httpcore": {"handlers": ["stdout"], "level": "INFO"},
    }
    root: OptionalModel[LoggerModel] = LoggerModel.model_validate(
        {"handlers": ["stdout"], "level": "DEBUG", "propagate": True},
    )

    def model_post_init(self: Self, __context) -> None:
        """Ensure the logger is configured as soon as the model is validated."""
        self.configure()
        logging.setLogRecordFactory(record_factory)
