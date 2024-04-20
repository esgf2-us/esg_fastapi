"""Ensure that the settings module works as intended."""

import logging
import os
from typing import Self

import pytest
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from pytest_mock import MockFixture

from esg_fastapi.utils import GeneratedOTELBase


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


def test_Gunicorn_bind_port_required() -> None:
    """If `bind` is empty, `host` and `port` are required."""
    from esg_fastapi import settings

    cls = type(settings.gunicorn)

    with pytest.raises(ValueError):
        cls(host=None, port=None)


# @patch.object(sys.modules["opentelemetry.instrumentation.auto_instrumentation.sitecustomize"], "initialize")
def test_Gunicorn_post_fork_instruments_app(mocker: MockFixture) -> None:
    """Calling the `post_fork` hook on an app causes OTEL to mark it as instrumented."""
    from esg_fastapi import settings

    arbiter = mocker.Mock()
    worker = mocker.MagicMock(
        app=mocker.Mock(
            _is_instrumented_by_opentelemetry=False,
        )
    )

    settings.gunicorn.post_fork(arbiter, worker)
    assert worker.app._is_instrumented_by_opentelemetry is True


def test_OTEL_Logging_is_instrumented() -> None:
    """OTEL instruments logging upon import."""
    import esg_fastapi

    assert LoggingInstrumentor()._is_instrumented_by_opentelemetry


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


def test_OTEL_env_vars_on_generated_model(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeEntrypoint:
        def load(self: Self) -> type:
            return type("FakeModule", tuple(), {"OTEL_TEST_VAR": "preset"})

    def mock_entry_points(group: str = "ignored") -> list[FakeEntrypoint]:
        return [FakeEntrypoint()]

    monkeypatch.setattr("esg_fastapi.utils.entry_points", mock_entry_points)
    ModelClass = GeneratedOTELBase()
    assert hasattr(ModelClass(), "otel_test_var")


def test_OTELSettings_exports_set_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeEntrypoint:
        def load(self: Self) -> type:
            return type("FakeModule", tuple(), {"OTEL_TEST_VAR": "preset"})

    def mock_entry_points(group: str = "ignored") -> list[FakeEntrypoint]:
        return [FakeEntrypoint()]

    monkeypatch.setattr("esg_fastapi.utils.entry_points", mock_entry_points)

    class TestClass(GeneratedOTELBase()): ...

    TestClass.model_validate({"otel_test_var": "fizzbang"})
    assert os.environ["OTEL_TEST_VAR"] == "fizzbang"
