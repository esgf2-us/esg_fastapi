import logging
from enum import Enum
from functools import partial
from typing import Self

from opentelemetry import trace
from pydantic_loggings.base import Formatter, Handler
from pydantic_loggings.base import Logger as LoggerModel
from pydantic_loggings.base import Logging as LoggingConfig
from pydantic_loggings.types_ import OptionalModel, OptionalModelDict

LogLevels = Enum("LogLevels", logging.getLevelNamesMapping())

default_log_record_factory = logging.getLogRecordFactory()


def record_factory(*args, **kwargs) -> logging.LogRecord:
    span = trace.get_current_span()
    ctx = span.get_span_context()
    record = default_log_record_factory(*args, **kwargs)

    record.otelServiceName = kwargs["service_name"]
    record.otelSpanID = format(ctx.span_id, "016x")
    record.otelTraceID = format(ctx.trace_id, "032x")
    record.otelTraceSampled = ctx.trace_flags.sampled

    return record


class ESGFLogging(LoggingConfig):
    """Python's logging DictConfig represented as a typed and validated Pydantic model."""

    service_name: str

    formatters: OptionalModelDict[Formatter] = {
        "otel": Formatter.model_validate(
            {
                "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
                "style": "%",
                # based on opentelemetry.instrumentation.logging.DEFAULT_LOGGING_FORMAT but with a newline before the message to make
                # container logs more readable
                "format": "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s trace_sampled=%(otelTraceSampled)s]\n- %(message)s",
            }
        )
    }
    handlers: OptionalModelDict[Handler] = {
        "stdout": Handler.model_validate({"formatter": "otel", "stream": "ext://sys.stdout"}),
        "stderr": Handler.model_validate({"formatter": "otel", "stream": "ext://sys.stderr"}),
    }
    loggers: OptionalModelDict[LoggerModel] = {
        "uvicorn": {"handlers": ["stdout"]},
    }
    root: OptionalModel[LoggerModel] = LoggerModel.model_validate(
        {"handlers": ["stdout"], "level": "INFO", "propagate": True}
    )

    def model_post_init(self: Self, __context) -> None:
        """Ensure the logger is configured as soon as the model is validated."""
        self.configure()
        factory = partial(record_factory, service_name=self.service_name)
        logging.setLogRecordFactory(factory)
