import asyncio
from unittest.mock import MagicMock

import httpx
import pytest
from pytest_mock import MockFixture
from respx import MockRouter

from esg_fastapi import settings
from esg_fastapi.api.globus import (
    ThinSearchClient,
    find_search_token,
)
from esg_fastapi.api.main import app_factory
from esg_fastapi.api.models import GlobusSearchQuery
from esg_fastapi.api.types import GlobusToken, GlobusTokenResponse
from tests.conftest import TestClient


@pytest.fixture
def globus_client() -> ThinSearchClient:
    """Provides a ThinSearchClient instance for testing."""
    return ThinSearchClient()


@pytest.mark.asyncio
async def test_globus_timing_headers_parsing() -> None:
    """Ensure Globus Search timing headers are parsed and added to response extensions."""
    expected_timings = {
        "authorization": 170,
        "establish_es_session": 72250,
        "query_exec_build_query": 61300,
        "raw_query_exec_1": 541840,
        "query_exec_invoke": 542090,
        "postfilter_query_result": 100,
        "query_execution": 603800,
        "overall": 676550,
        "schemadump": 220,
        "response_compression": 30,
        "total": 688350,
    }

    globus_client = ThinSearchClient()
    response = await globus_client.client.post(globus_client.search_url)

    assert response.extensions["globus_timings"] == expected_timings


@pytest.mark.asyncio
async def test_auth_header(globus_client: ThinSearchClient) -> None:
    """Ensure the auth_header property provides an appropriate Authorization header."""
    globus_client.access_token = "test_token"
    assert globus_client.auth_header == {"Authorization": "Bearer test_token"}


@pytest.mark.asyncio
async def test_search_accepts_globus_search_query(globus_client: ThinSearchClient, mocker: MockFixture) -> None:
    """Ensure the search method accepts a GlobusSearchQuery model object."""
    query = GlobusSearchQuery(limit=0, offset=0)
    spy = mocker.spy(globus_client.client, "post")
    await globus_client.search(query)
    spy.assert_called_once_with(
        url=globus_client.search_url,
        content=query.model_dump_json(exclude_none=True),
        headers={"Content-Type": "application/json"},
        extensions={"force_cache": True},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(("auth_token", "outcome"), [("test_token", True), (None, False)])
async def test_search_optional_authentication(
    globus_client: ThinSearchClient,
    mocker: MockFixture,
    auth_token: str,
    outcome: bool,
) -> None:
    """Ensure Authorization header is set only if an access_token is set."""
    globus_client.access_token = auth_token
    post_mock = mocker.patch.object(globus_client.client, "post")
    await globus_client.search(GlobusSearchQuery(limit=0, offset=0))
    assert ("Authorization" in post_mock.call_args[1]["headers"]) == outcome


@pytest.mark.asyncio
async def test_find_search_token_in_main_response() -> None:
    """Ensure find_search_token can locate the search token when it is the main response."""
    globus_token: GlobusTokenResponse = {
        "access_token": "main_access_token",
        "expires_in": 3600,
        "id_token": "main_id_token",
        "resource_server": "search.api.globus.org",
        "scope": "main_scope",
        "state": "main_state",
        "token_type": "bearer",
        "other_tokens": [
            {
                "access_token": "some_access_token",
                "expires_in": 3600,
                "resource_server": "groups.api.globus.org",
                "scope": "some_scope",
                "token_type": "bearer",
            },
        ],
    }

    assert find_search_token(globus_token) == globus_token


@pytest.mark.asyncio
async def test_find_search_token_in_other_tokens() -> None:
    """Ensure find_search_token can locate the search token when it is in `other_tokens`."""
    search_token: GlobusToken = {
        "access_token": "search_access_token",
        "expires_in": 3600,
        "resource_server": "search.api.globus.org",
        "scope": "some_scope",
        "token_type": "bearer",
    }
    transfer_token: GlobusToken = {
        "access_token": "transfer_access_token",
        "expires_in": 3600,
        "resource_server": "transfer.api.globus.org",
        "scope": "some_scope",
        "token_type": "bearer",
    }

    globus_token: GlobusTokenResponse = {
        "access_token": "main_access_token",
        "expires_in": 3600,
        "id_token": "main_id_token",
        "resource_server": "groups.api.globus.org",
        "scope": "main_scope",
        "state": "main_state",
        "token_type": "bearer",
        "other_tokens": [search_token, transfer_token],
    }

    assert find_search_token(globus_token) == search_token


@pytest.mark.asyncio
async def test_find_search_token_missing_raises() -> None:
    """find_search_token raises when there is no search token in the response."""
    globus_token: GlobusTokenResponse = {
        "access_token": "main_access_token",
        "expires_in": 3600,
        "id_token": "main_id_token",
        "resource_server": "groups.api.globus.org",
        "scope": "main_scope",
        "state": "main_state",
        "token_type": "bearer",
        "other_tokens": [],
    }
    with pytest.raises(RuntimeError):
        find_search_token(globus_token)


@pytest.mark.asyncio
async def test_token_refreshing(respx_mock: MockRouter, mocker: MagicMock, test_client: TestClient) -> None:
    """keep_token_fresh sets the access token on the globus_client."""
    mocker.patch.object(settings.globus, "client_id", "some_client_id")
    mocker.patch.object(settings.globus, "client_secret", "some_client_secret")
    mocker.patch.object(settings.globus, "token_renewal_interval", 0.1)
    first_globus_token: GlobusTokenResponse = {
        "access_token": "first_access_token",
        "expires_in": 12345,
        "id_token": "main_id_token",
        "resource_server": "search.api.globus.org",
        "scope": "main_scope",
        "state": "main_state",
        "token_type": "bearer",
        "other_tokens": [],
    }
    second_globus_token: GlobusTokenResponse = {
        "access_token": "second_access_token",
        "expires_in": 12345,
        "id_token": "main_id_token",
        "resource_server": "search.api.globus.org",
        "scope": "main_scope",
        "state": "main_state",
        "token_type": "bearer",
        "other_tokens": [],
    }
    respx_mock.post("https://auth.globus.org/v2/oauth2/token", name="refresh_token").side_effect = [
        httpx.Response(200, json=first_globus_token),
        httpx.Response(200, json=second_globus_token),
    ]

    spy = mocker.spy(test_client.app.state.globus_client.client, "post")

    with test_client as client:
        # Initializing the app (via context manager) should call the refresh endpoint
        assert respx_mock.routes["refresh_token"].call_count == 1
        # The access token should be set on the globus_client
        assert client.app.state.globus_client.access_token == "first_access_token"
        # The request to the token endpoint should disable cached responses
        spy.assert_called_with(
            url="https://auth.globus.org/v2/oauth2/token",
            auth=("some_client_id", "some_client_secret"),
            data={"grant_type": "client_credentials", "scope": "urn:globus:auth:scope:search.api.globus.org:search"},
            extensions={"cache_disabled": True},
        )

        await asyncio.sleep(0.2)  # Allow the token to be refreshed

        # After the sleep, the token should have been refreshed again
        assert respx_mock.routes["refresh_token"].call_count == 2
        # And set with the new access token
        assert client.app.state.globus_client.access_token == "second_access_token"
        # And still not cached
        spy.assert_called_with(
            url="https://auth.globus.org/v2/oauth2/token",
            auth=("some_client_id", "some_client_secret"),
            data={"grant_type": "client_credentials", "scope": "urn:globus:auth:scope:search.api.globus.org:search"},
            extensions={"cache_disabled": True},
        )


@pytest.mark.asyncio
async def test_token_renewal_watchdog_with_credentials(mocker: MagicMock) -> None:
    """Watchdog schedules a task to keep the token fresh if app credentials are set."""
    mocker.patch.object(settings.globus, "client_id", "some_client_id")
    mocker.patch.object(settings.globus, "client_secret", "some_client_secret")

    mock_renewer = mocker.patch("esg_fastapi.api.globus.keep_token_fresh")
    mock_scheduler = mocker.patch("esg_fastapi.api.globus.asyncio.create_task")

    app = app_factory()
    with TestClient(app):
        mock_scheduler.assert_called_once()
        mock_renewer.assert_called_once_with(app)


@pytest.mark.asyncio
async def test_token_renewal_watchdog_without_credentials(mocker: MagicMock) -> None:
    """Watchdog does not attempt to renew if app credentials are not set."""
    mocker.patch.object(settings.globus, "client_id", None)
    mocker.patch.object(settings.globus, "client_secret", None)

    mock_renewer = mocker.patch("esg_fastapi.api.globus.keep_token_fresh")
    mock_scheduler = mocker.patch("esg_fastapi.api.globus.asyncio.create_task")

    app = app_factory()
    with TestClient(app):
        mock_scheduler.assert_not_called()
        mock_renewer.assert_not_called()
