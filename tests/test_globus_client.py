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
    find_search_token,
    keep_token_fresh,
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
            "server-timing": 'authorization=0.17; "authorization",establish_es_session=72.25; "establish_es_session",query_exec_build_query=61.3; "query_exec_build_query",raw_query_exec_1=541.84; "raw_query_exec_1",query_exec_invoke=542.09; "query_exec_invoke",postfilter_query_result=0.1; "postfilter_query_result",query_execution=603.8; "Query Execution Time",overall=676.55; "overall",schemadump=0.22; "schemadump",response_compression=0.03; "response_compression",total=688.358675309; "total"'
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
        "total": 688358,
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
async def test_keep_token_fresh(respx_mock: MockRouter, mocker: MagicMock, test_client: TestClient) -> None:
    """keep_token_fresh sets the access token on the globus_client."""
    mocker.patch.object(settings.globus, "client_id", "client_id")
    mocker.patch.object(settings.globus, "client_secret", "client_secret")
    globus_token: GlobusTokenResponse = {
        "access_token": "search_access_token",
        "expires_in": 12345,
        "id_token": "main_id_token",
        "resource_server": "search.api.globus.org",
        "scope": "main_scope",
        "state": "main_state",
        "token_type": "bearer",
        "other_tokens": [],
    }
    respx_mock.post("https://auth.globus.org/v2/oauth2/token").return_value = httpx.Response(200, json=globus_token)
    app = test_client.app

    await keep_token_fresh(app)

    assert app.globus_client.access_token == "search_access_token"


@pytest.mark.asyncio
async def test_token_requests_are_never_cached(
    mocker: MagicMock, test_client: TestClient, respx_mock: MockRouter
) -> None:
    """The token requests should never be cached."""
    mocker.patch.object(settings.globus, "client_id", "some_client_id")
    mocker.patch.object(settings.globus, "client_secret", "some_client_secret")
    spy = mocker.spy(test_client.app.globus_client.client, "post")
    respx_mock.post("https://auth.globus.org/v2/oauth2/token").return_value = httpx.Response(
        200,
        json={
            "access_token": "search_access_token",
            "expires_in": 12345,
            "resource_server": "search.api.globus.org",
        },
    )

    await keep_token_fresh(test_client.app)

    spy.assert_called_once_with(
        url="https://auth.globus.org/v2/oauth2/token",
        auth=("some_client_id", "some_client_secret"),
        data={"grant_type": "client_credentials", "scope": "urn:globus:auth:scope:search.api.globus.org:search"},
        extensions={"cache_disabled": True},
    )


@pytest.mark.asyncio
async def test_token_renewal_watchdog_with_credentials(mocker: MagicMock) -> None:
    """Watchdog renews the access token and schedules the next renewal 1min before expiration."""
    mocker.patch.object(settings.globus, "client_id", "client_id")
    mocker.patch.object(settings.globus, "client_secret", "client_secret")
    mock_renewer = mocker.patch("esg_fastapi.api.versions.v1.globus.keep_token_fresh")
    mock_app = MagicMock(spec=FastAPIWithSearchClient, globus_client=MagicMock(spec=ThinSearchClient))
    mock_scheduler = mocker.patch("esg_fastapi.api.versions.v1.globus.asyncio.create_task")

    async with token_renewal_watchdog(mock_app):
        pass

    mock_scheduler.assert_called_once()
    mock_renewer.assert_called_once_with(mock_app)


@pytest.mark.asyncio
async def test_token_renewal_watchdog_without_credentials(mocker: MagicMock) -> None:
    """Watchdog does not attempt to renew if app credentials are not set."""
    mocker.patch.object(settings.globus, "client_id", None)
    mocker.patch.object(settings.globus, "client_secret", None)
    mock_renewer = mocker.patch("esg_fastapi.api.versions.v1.globus.keep_token_fresh")
    mock_app = MagicMock(spec=FastAPIWithSearchClient, globus_client=MagicMock(spec=ThinSearchClient))
    mock_scheduler = mocker.patch("esg_fastapi.api.versions.v1.globus.asyncio.create_task")

    async with token_renewal_watchdog(mock_app):
        pass

    mock_renewer.assert_not_called()
    mock_scheduler.assert_not_called()
