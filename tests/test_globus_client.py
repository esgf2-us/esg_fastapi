import asyncio
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockFixture
from respx import MockRouter

from esg_fastapi import settings
from esg_fastapi.api.versions.v1.globus import (
    FastAPIWithSearchClient,
    ThinSearchClient,
    _renew_token,
    find_search_token,
    token_renewal_watchdog,
)
from esg_fastapi.api.versions.v1.models import GlobusMetaEntry, GlobusMetaResult, GlobusSearchQuery, GlobusSearchResult
from esg_fastapi.api.versions.v1.types import GlobusToken, GlobusTokenResponse


@pytest.fixture(autouse=True)
def mock_globus_search(respx_mock: MockRouter) -> MockRouter:
    """Mock the Globus Search API with a default response."""
    respx_mock.post(
        name="post_search",
        url__regex="https://search.api.globus.org/v1/index/(.+)/search",
    ).return_value = httpx.Response(
        status_code=200,
        headers={
            "server-timing": 'authorization=0.17; "authorization",establish_es_session=72.25; "establish_es_session",query_exec_build_query=61.3; "query_exec_build_query",raw_query_exec_1=541.84; "raw_query_exec_1",query_exec_invoke=542.09; "query_exec_invoke",postfilter_query_result=0.1; "postfilter_query_result",query_execution=603.8; "Query Execution Time",overall=676.55; "overall",schemadump=0.22; "schemadump",response_compression=0.03; "response_compression",total=688.35; "total"'
        },
        json=GlobusSearchResult(
            gmeta=[
                GlobusMetaResult(
                    subject="test",
                    entries=[
                        GlobusMetaEntry(content={}, entry_id="some_entry", matched_principal_sets=["some_principal"])
                    ],
                )
            ],
            offset=0,
            count=0,
            total=0,
            has_next_page=False,
        ).model_dump(),
    )
    return respx_mock


@pytest.fixture
def globus_client() -> ThinSearchClient:
    """Provides a ThinSearchClient instance for testing."""
    return ThinSearchClient()


@pytest.mark.asyncio
async def test_globus_timing_headers_parsing() -> None:
    """Ensure Globus Search timing headers are parsed and added to response extensions."""
    expected_timings = {
        "authorization": 170.0,
        "establish_es_session": 72250.0,
        "query_exec_build_query": 61300.0,
        "raw_query_exec_1": 541840.0,
        "query_exec_invoke": 542090.0,
        "postfilter_query_result": 100.0,
        "query_execution": 603800.0,
        "overall": 676550.0,
        "schemadump": 220.0,
        "response_compression": 30.0,
        "total": 688350.0,
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
        data=query.model_dump(exclude_none=True),
        headers={"Content-Type": "application/json"},
        extensions={"force_cache": True},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(("auth_token", "outcome"), [("test_token", True), (None, False)])
async def test_search_optional_authentication(
    globus_client: ThinSearchClient, mocker: MockFixture, auth_token: str, outcome: bool
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
        "refresh_token": "main_refresh_token",
        "id_token": "main_id_token",
        "resource_server": "search.api.globus.org",
        "scope": "main_scope",
        "state": "main_state",
        "token_type": "bearer",
        "other_tokens": [
            {
                "access_token": "some_access_token",
                "expires_in": 3600,
                "refresh_token": "some_refresh_token",
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
        "refresh_token": "some_refresh_token",
        "resource_server": "search.api.globus.org",
        "scope": "some_scope",
        "token_type": "bearer",
    }
    transfer_token: GlobusToken = {
        "access_token": "transfer_access_token",
        "expires_in": 3600,
        "refresh_token": "some_refresh_token",
        "resource_server": "transfer.api.globus.org",
        "scope": "some_scope",
        "token_type": "bearer",
    }

    globus_token: GlobusTokenResponse = {
        "access_token": "main_access_token",
        "expires_in": 3600,
        "refresh_token": "main_refresh_token",
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
        "refresh_token": "main_refresh_token",
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
async def test_renew_token(respx_mock: MockRouter, mocker: MagicMock, test_client: TestClient) -> None:
    """_renew_token sets the access and refresh tokens on the globus_client and returns their expiration time."""
    mocker.patch.object(settings.globus, "globus_client_id", "client_id")
    mocker.patch.object(settings.globus, "globus_client_secret", "client_secret")
    globus_token: GlobusTokenResponse = {
        "access_token": "search_access_token",
        "expires_in": 12345,
        "refresh_token": "search_refresh_token",
        "id_token": "main_id_token",
        "resource_server": "search.api.globus.org",
        "scope": "main_scope",
        "state": "main_state",
        "token_type": "bearer",
        "other_tokens": [],
    }
    respx_mock.post("https://auth.globus.org/v2/oauth2/token").return_value = httpx.Response(200, json=globus_token)
    app = test_client.app

    expiration = await _renew_token(app, ("some_client_id", "some_client_secret"))

    assert expiration == 12345
    assert app.globus_client.access_token == "search_access_token"
    assert app.globus_client.refresh_token == "search_refresh_token"


@pytest.mark.asyncio
async def test_token_requests_are_never_cached(
    mocker: MagicMock, test_client: TestClient, respx_mock: MockRouter
) -> None:
    """The token requests should never be cached."""
    spy = mocker.spy(test_client.app.globus_client.client, "post")
    respx_mock.post("https://auth.globus.org/v2/oauth2/token").return_value = httpx.Response(
        200,
        json={
            "access_token": "search_access_token",
            "expires_in": 12345,
            "refresh_token": "search_refresh_token",
            "resource_server": "search.api.globus.org",
        },
    )

    await _renew_token(test_client.app, ("some_client_id", "some_client_secret"))

    spy.assert_called_once_with(
        url="https://auth.globus.org/v2/oauth2/token",
        auth=("some_client_id", "some_client_secret"),
        extensions={"cache_disabled": True},
    )


@pytest.mark.asyncio
async def test_token_renewal_watchdog_with_credentials(mocker: MagicMock) -> None:
    """Watchdog renews the access token and schedules the next renewal 1min before expiration."""
    mocker.patch.object(settings.globus, "globus_client_id", "client_id")
    mocker.patch.object(settings.globus, "globus_client_secret", "client_secret")
    mock_renewer = mocker.patch("esg_fastapi.api.versions.v1.globus._renew_token", return_value=12345)
    mock_app = MagicMock(spec=FastAPIWithSearchClient, globus_client=MagicMock(spec=ThinSearchClient))
    loop = asyncio.get_event_loop()
    mock_scheduler = mocker.patch.object(loop, "call_later")

    await token_renewal_watchdog(mock_app)

    mock_renewer.assert_called_once()
    mock_scheduler.assert_called_once_with(12345 - 60, mock_renewer, mock_app, ("client_id", "client_secret"))


@pytest.mark.asyncio
async def test_token_renewal_watchdog_without_credentials(mocker: MagicMock) -> None:
    """Watchdog does not attempt to renew if app credentials are not set."""
    mocker.patch.object(settings.globus, "globus_client_id", None)
    mocker.patch.object(settings.globus, "globus_client_secret", None)
    mock_renewer = mocker.patch("esg_fastapi.api.versions.v1.globus._renew_token")
    mock_app = MagicMock(spec=FastAPIWithSearchClient, globus_client=MagicMock(spec=ThinSearchClient))
    loop = asyncio.get_event_loop()
    mock_scheduler = mocker.patch.object(loop, "call_later")

    await token_renewal_watchdog(mock_app)

    mock_renewer.assert_not_called()
    mock_scheduler.assert_not_called()
