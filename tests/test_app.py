import json
from unittest.mock import MagicMock

from httpx import HTTPStatusError, Request, Response
import pytest
from fastapi.testclient import TestClient
from starlette import status


@pytest.mark.asyncio
async def test_globus_search_timeout_error_handling(
    test_client: TestClient, mocker: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Ensure that a timeout error from the Globus Search client is handled gracefully."""
    mocker.patch.object(test_client.app.globus_client.client, "post", side_effect=TimeoutError("Connection timed out"))
    mocker.patch("esg_fastapi.api.versions.v1.globus.get_current_trace_id", return_value=8675309)
    caplog.set_level("ERROR", logger="esg_fastapi.api.versions.v1.globus")
    expected_response = {
        "type": "TimeoutError",
        "title": "Timeout While Connecting to Globus Search",
        "status": status.HTTP_504_GATEWAY_TIMEOUT,
        "detail": "Connection timed out",
        "trace_id": 8675309,
    }

    response = test_client.get("/")

    assert caplog.records[0].message == json.dumps(expected_response)
    assert response.status_code == status.HTTP_504_GATEWAY_TIMEOUT
    assert response.json() == expected_response


@pytest.mark.asyncio
async def test_globus_search_http_status_error_handling(
    test_client: TestClient, mocker: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Ensure that a non-200 status from the Globus Search client is handled gracefully."""
    mock_request = MagicMock(spec=Request)
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
    mocker.patch.object(test_client.app.globus_client.client, "post", side_effect=HTTPStatusError("HTTP Status Error", request=mock_request, response=mock_response))
    mocker.patch("esg_fastapi.api.versions.v1.globus.get_current_trace_id", return_value=8675309)
    caplog.set_level("ERROR", logger="esg_fastapi.api.versions.v1.globus")
    expected_response = {
        "type": "HTTPStatusError",
        "title": "HTTP Status Error While Connecting to Globus Search",
        "status": status.HTTP_429_TOO_MANY_REQUESTS,
        "detail": "HTTP Status Error",
        "trace_id": 8675309,
    }

    response = test_client.get("/")

    assert caplog.records[0].message == json.dumps(expected_response)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.json() == expected_response


def test_search_redirects_to_root(test_client: TestClient) -> None:
    response = test_client.get("/search", follow_redirects=False)
    assert response.status_code == status.HTTP_308_PERMANENT_REDIRECT
    assert response.headers["location"] == "/"
