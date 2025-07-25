import os
from importlib.metadata import entry_points
from typing import Annotated, Literal, Self

from annotated_types import T
from pydantic import BaseModel, Field, create_model

from esg_fastapi.utils import metadata

Exportable = Annotated[T, "Exportable"]


class ExportingModel(BaseModel):
    def model_post_init(self: Self, _) -> None:
        """Export any set model field values that are annotated with `Exportable` as environment variables.

        It iterates through the model fields, checks if the field is annotated with "Exportable",
        and if a value is set for the field, it sets the corresponding environment variable.
        OpenTelemetry is configured entirely through environment variables. Since they don't provide a way
        to set these options programmatically, we generate a model from all environment variables that
        they respect and during this post-init hook, export any that have values to the environment so that
        OpenTelemetry will see them and we can configure everything in one place and generate docs and etc.
        """
        for name, field in type(self).model_fields.items():
            if "Exportable" in field.metadata and (field_value := getattr(self, name)):
                os.environ[name.upper()] = str(field_value)


def GeneratedOTELBase() -> type[BaseModel]:
    """Generates a BaseModel class with fields for all OpenTelemetry environment variables.

    We use the same method (`importlib.metadata.entrypoints`) as OpenTelemetry's auto_instrumentation to
    gather the list of all environment variables that OpenTelemetry respects. All such discovered environment
    variables are `.lower()` and created as Fields on the generated model. They're also Annoted by the
    `Exportable` Generic Type so that they can be distinguished from types and properties on sub classes
    that we might not want to export to the environment.
    """
    return create_model(
        "OTELBase",
        __config__=None,
        __doc__=None,
        __base__=ExportingModel,
        __cls_kwargs__=None,
        __validators__=None,
        __module__=__name__,
        __slots__=None,
        **{
            var.lower(): (Exportable[str], Field(default=None))
            for ep in entry_points(group="opentelemetry_environment_variables")
            for var in dir(ep.load())
            if var.startswith("OTEL_")
        },
    )


class OTELSettings(GeneratedOTELBase()):
    """Settings class that exports all OpenTelemetry settings as environment variables.

    We inherit from the model produced by the GeneratedOTELBase class factory to keep that logic separate.
    The fields generated on that model all have a default value of `None` and the `model_post_init` hook
    will only export fields that have a value set, that way we don't need to know what all the OpenTelemetry
    settings env vars default to (it doesn't seem to be exposed anywhere).
    """

    otel_service_name: Exportable[str] = metadata["name"]
    otel_python_log_level: Exportable[str] = "info"
    otel_python_logging_auto_instrumentation_enabled: Exportable[str] = "true"
    otel_python_log_correlation: Exportable[str] = "true"
    otel_traces_exporter: Exportable[Literal["none", "otlp", "console"]] = Field(
        default="none",
        title="OTLP Traces",
        description="Trace exporter to be used. See https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/#exporter-selection",
    )
