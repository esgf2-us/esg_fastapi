"""Ensure that the settings module works as intended."""

import logging
import os
from typing import Self

import pytest
from pytest_mock import MockFixture


def test_settings_is_usable() -> None:
    """Ensure that the settings module can be imported and provides at least one setting."""
    from esg_fastapi import settings

    assert settings.globus_search_index is not None


def test_Gunicorn_bind_takes_precedence() -> None:
    """The `bind` setting takes precedence over host and port."""
    from esg_fastapi import settings

    cls = type(settings.gunicorn)
    gs = cls(bind="127.0.0.1:9999", host="1.1.1.1", port=1111)

    assert gs.bind == "127.0.0.1:9999"


def test_Gunicorn_bind_from_host_and_port() -> None:
    """If empty, build `bind` from `host` and `port`."""
    from esg_fastapi import settings

    cls = type(settings.gunicorn)
    gs = cls(host="1.1.1.1", port=1111)

    assert gs.bind == "1.1.1.1:1111"


def test_Gunicorn_no_bind_host_and_port_required() -> None:
    """If `bind` is empty, `host` and `port` are required."""
    from esg_fastapi.configuration.gunicorn import GunicornSettings

    with pytest.raises(ValueError):
        GunicornSettings(host=None, port=None)


# TODO: move this somewhere sensible
def test_app_factory_instruments_app(mocker: MockFixture) -> None:
    """The created app is marked as insturmented by the FastAPIInstrumentor."""
    from esg_fastapi.api.versions.v1.routes import app_factory

    app = app_factory()
    assert app._is_instrumented_by_opentelemetry is True


def test_OTELSettings_instruments_logger(monkeypatch: pytest.MonkeyPatch, mocker: MockFixture) -> None:
    """Logging is intrumented by settings."""
    from esg_fastapi.configuration.logging import ESGFLogging, record_factory

    fake_set_log_factory = mocker.Mock()
    monkeypatch.setattr("esg_fastapi.configuration.logging.logging.setLogRecordFactory", fake_set_log_factory)
    ESGFLogging()
    assert fake_set_log_factory.called_once_with(record_factory)


@pytest.mark.parametrize(
    ("log_level"),
    logging.getLevelNamesMapping().values(),
    ids=logging.getLevelNamesMapping().keys(),
)
def test_root_logger_has_OTEL_span_id_and_trace_id(caplog: pytest.LogCaptureFixture, log_level: int) -> None:
    """At all log levels, root logger includes OTEL trace and span ids."""
    root_formatter = logging.root.handlers[0].formatter
    with caplog.at_level(log_level):
        logger = logging.getLogger()
        logger.log(log_level, "test")
        for record in caplog.records:
            assert "span_id" in root_formatter.format(record)
            assert "trace_id" in root_formatter.format(record)


# TODO: extract the entry point mocking into a fixture
def test_OTEL_env_vars_on_generated_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """Variables specified by OTEL env var entry point are created as fields on the generated base model."""

    class FakeEntrypoint:
        def load(self: Self) -> type:
            return type("FakeModule", tuple(), {"OTEL_TEST_VAR": "preset"})

    def mock_entry_points(group: str = "ignored") -> list[FakeEntrypoint]:
        return [FakeEntrypoint()]

    monkeypatch.setattr("esg_fastapi.configuration.opentelemetry.entry_points", mock_entry_points)
    from esg_fastapi.configuration.opentelemetry import GeneratedOTELBase

    ModelClass = GeneratedOTELBase()
    assert hasattr(ModelClass(), "otel_test_var")


def test_OTELSettings_exports_set_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Generated fields with subsequent values set are exported to the environment."""

    class FakeEntrypoint:
        def load(self: Self) -> type:
            return type("FakeModule", tuple(), {"OTEL_TEST_VAR": "preset"})

    def mock_entry_points(group: str = "ignored") -> list[FakeEntrypoint]:
        return [FakeEntrypoint()]

    monkeypatch.setattr("esg_fastapi.configuration.opentelemetry.entry_points", mock_entry_points)
    from esg_fastapi.configuration.opentelemetry import GeneratedOTELBase

    class TestClass(GeneratedOTELBase()): ...

    TestClass.model_validate({"otel_test_var": "fizzbang"})
    assert os.environ["OTEL_TEST_VAR"] == "fizzbang"
