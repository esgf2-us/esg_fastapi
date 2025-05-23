"""Ensure that the settings module works as intended."""

import logging
import os
from typing import Self

import pytest
from pytest_mock import MockFixture


def test_settings_is_usable() -> None:
    """Ensure that the settings module can be imported and provides at least one setting."""
    from esg_fastapi import settings

    assert settings.globus.search_index is not None


# TODO: move this somewhere sensible
def test_app_factory_instruments_app() -> None:
    """The created app is marked as insturmented by the FastAPIInstrumentor."""
    from esg_fastapi.api.versions.v1.routes import app_factory

    app = app_factory()
    assert app._is_instrumented_by_opentelemetry is True


def test_OTELSettings_instruments_logger(mocker: MockFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    """Logging is intrumented by settings."""
    mock_record_factory = mocker.Mock()
    mock_record_factory_setter = mocker.Mock()
    fake_service_name = "foo"
    monkeypatch.setattr("esg_fastapi.configuration.logging.record_factory", mock_record_factory)
    monkeypatch.setattr("esg_fastapi.configuration.logging.logging.setLogRecordFactory", mock_record_factory_setter)
    from esg_fastapi.configuration.logging import ESGFLogging

    ESGFLogging(service_name=fake_service_name)
    assert mock_record_factory_setter.call_args.args[0].func == mock_record_factory
    assert mock_record_factory_setter.call_args.args[0].keywords["service_name"] == fake_service_name


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
        assert len(caplog.records) or log_level == logging.NOTSET, "No logs produced"
        for record in caplog.records:
            assert "span_id" in root_formatter.format(record)
            assert "trace_id" in root_formatter.format(record)


# TODO: extract the entry point mocking into a fixture
def test_OTEL_env_vars_on_generated_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """Variables specified by OTEL env var entry point are created as fields on the generated base model."""

    class FakeEntrypoint:
        def load(self: Self) -> type:
            return type("FakeModule", (), {"OTEL_TEST_VAR": "preset"})

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
            return type("FakeModule", (), {"OTEL_TEST_VAR": "preset"})

    def mock_entry_points(group: str = "ignored") -> list[FakeEntrypoint]:
        return [FakeEntrypoint()]

    monkeypatch.setattr("esg_fastapi.configuration.opentelemetry.entry_points", mock_entry_points)
    from esg_fastapi.configuration.opentelemetry import GeneratedOTELBase

    class TestClass(GeneratedOTELBase()): ...

    TestClass.model_validate({"otel_test_var": "fizzbang"})
    assert os.environ["OTEL_TEST_VAR"] == "fizzbang"
