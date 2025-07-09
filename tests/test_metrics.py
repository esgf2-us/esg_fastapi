from contextlib import AbstractContextManager
from contextlib import nullcontext as does_not_raise
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter
from starlette.requests import Request

from esg_fastapi.observability.metrics import track_exceptions


def test_cache_hits_are_tracked(test_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure the `esg_bridge_cache_hits_total` metric is incremented on cache hits."""
    mock_metric = Counter(
        name="esg_bridge_cache_hits_total",
        documentation="",
        registry=CollectorRegistry(),
    )
    monkeypatch.setattr("esg_fastapi.api.globus.CACHE_HITS", mock_metric)

    # Prime the cache
    _ = test_client.get("/")

    # Simulate a cache hit
    _ = test_client.get("/")

    assert mock_metric._value.get() == 1


@pytest.mark.parametrize(
    ("exc_type",      "handlers",           "expectation"), [
    (Exception, {Exception: AsyncMock()}, does_not_raise()),
    (KeyError,  {KeyError: AsyncMock()},  does_not_raise()),
    (Exception, {},                       pytest.raises(Exception)),
    (KeyError,  {},                       pytest.raises(KeyError)),
    ],
)  # fmt: skip
@pytest.mark.asyncio
async def test_track_exceptions(
    exc_type: Exception,
    handlers: dict[Exception, AsyncMock],
    expectation: AbstractContextManager,
    monkeypatch: pytest.MonkeyPatch,
    mocker: MagicMock,
) -> None:
    request = mocker.MagicMock(spec=Request)
    request.app.exception_handlers = handlers

    mock_metric = Counter(
        name="exception_count",
        documentation="",
        labelnames=["exception_type"],
        registry=CollectorRegistry(),
    )
    monkeypatch.setattr("esg_fastapi.observability.metrics.EXCEPTIONS", mock_metric)

    with expectation:
        await track_exceptions(request, exc_type)

    assert mock_metric.labels(exception_type=type(exc_type).__name__)._value.get() == 1

    if handlers:
        request.app.exception_handlers[exc_type].assert_awaited_once_with(request, exc_type)


def test_metrics_endpoint(test_client: TestClient) -> None:
    # Send a GET request to the /metrics endpoint
    response = test_client.get("/metrics")

    # Check if the response status code is 200 (OK)
    assert response.status_code == HTTPStatus.OK

    # Check if the response content type is set correctly
    assert response.headers["Content-Type"] == CONTENT_TYPE_LATEST

    # Check if the response content contains the expected metrics data
    assert "fastapi_responses_total" in response.text
    assert "fastapi_requests_total" in response.text
    assert "fastapi_request_processing_time" in response.text
    assert "fastapi_requests_in_progress" in response.text
