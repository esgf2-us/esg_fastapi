from contextlib import nullcontext as does_not_raise
from http import HTTPStatus
from typing import ContextManager
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter
from starlette.requests import Request

from esg_fastapi import settings
from esg_fastapi.observability.metrics import FACET_LABELS, GLOBAL_LABELS, track_exceptions


@pytest.mark.parametrize(
    ("path", "exc_type",      "handlers",           "expectation"), [
    ("/foo",  Exception, {Exception: AsyncMock()}, does_not_raise(),),
    ("/bar",  KeyError,  {KeyError: AsyncMock()},  does_not_raise(),),
    ("/baz",  Exception, {},                       pytest.raises(Exception),),
    ("/qux",  KeyError,  {},                       pytest.raises(KeyError),),
    ],
)  # fmt: skip
@pytest.mark.asyncio()
async def test_track_exceptions(
    path: str,
    exc_type: Exception,
    handlers: dict[Exception, AsyncMock],
    expectation: ContextManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = MagicMock(spec=Request)
    request.method = "GET"
    request.url.path = path
    request.app.exception_handlers = handlers
    settings.app_id = "app_id"
    facet_labels = {field: request.query_params.get(field) for field in FACET_LABELS}
    request_labels = {
        "method": request.method,
        "path": request.url.path,
        "exception_type": exc_type,
        "app_name": "app_id",
    }
    registry = CollectorRegistry()
    mock_metric = Counter(
        name="exception_count", documentation="", labelnames=[*GLOBAL_LABELS, "exception_type"], registry=registry
    )
    monkeypatch.setattr("esg_fastapi.observability.metrics.EXCEPTIONS", mock_metric)
    with expectation:
        await track_exceptions(request, exc_type)

    assert mock_metric.labels(**facet_labels, **request_labels)._value.get() == 1
    if handlers:
        request.app.exception_handlers[exc_type].assert_awaited_once_with(request, exc_type)


def test_metrics_endpoint():
    # Create an instance of the HTTP client
    from esg_fastapi.observability.routes import app

    client = TestClient(app)

    # Send a GET request to the /metrics endpoint
    response = client.get("metrics")

    # Check if the response status code is 200 (OK)
    assert response.status_code == HTTPStatus.OK

    # Check if the response content type is set correctly
    assert response.headers["Content-Type"] == CONTENT_TYPE_LATEST

    # Check if the response content contains the expected metrics data
    assert "fastapi_responses_total" in response.text
    assert "fastapi_requests_total" in response.text
    assert "fastapi_request_processing_time" in response.text
    assert "fastapi_requests_in_progress" in response.text
