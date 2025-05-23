from typing import Literal

import httpx
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when
from pytest_bdd.parsers import parse
from pytest_mock import MockFixture
from respx import MockRouter

from esg_fastapi.api.versions.v1.models import GlobusMetaEntry, GlobusMetaResult, GlobusSearchResult

scenarios("Caching")


@pytest.fixture(autouse=True)
def mock_globus_search(respx_mock: MockRouter) -> MockRouter:
    """Mock the Globus Search API endpoint for testing purposes.

    Args:
        respx_mock (MockRouter): The respx mock router to register the mock endpoint.

    Returns:
        MockRouter: The respx mock router with the Globus Search API endpoint mocked.
    """
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


EtagMatchType = Literal["if-none-match", "if-match"]
EtagHeader = dict[EtagMatchType, str]


@given(parse("that the client provides an <{header_match}> etag"), target_fixture="etag_header")
def create_request(header_match: EtagMatchType) -> EtagHeader:
    """Creates an ETag header dict with the value of the default empty query."""
    return {header_match: "751ef835d1fcb35932af51f937204956"}


@when("the result for that etag is cached")
@when("the Globus Search response is already in the cache")
@when("the API sends a response", target_fixture="basic_response")
def cached_request(test_client: TestClient) -> httpx.Response:
    """Cache the default query."""
    return test_client.get(url="/")


@when("the cache_key does not match the provided etag", target_fixture="etag_header")
def mismatch_etag(etag_header: EtagHeader) -> EtagHeader:
    """Make the ETag header mismatch with the cached query."""
    return {key: "some_other_cache_key" for key in etag_header}


@then(parse("it should return status code <{status_attr}>"))
def check_return_status(status_attr: str, etag_header: EtagHeader, test_client: TestClient) -> None:
    """Ensure the API response status matches the expected result."""
    response = test_client.get(url="/", headers=etag_header)
    assert response.status_code == getattr(status, status_attr)


@given("that the client sends a query")
@given("that users can still make use of stale results")
@given("that publication syncronization only runs every 5 minutes")
@given("that all ESGF data is public")
def noop() -> None:
    """Holder for Cucumber directives that don't require any actions."""
    pass


@then("the <public> cache control directive should be set")
def is_response_public(basic_response: httpx.Response) -> None:
    """Ensure the cache-control header marks the request as publicly cachable."""
    assert "public" in basic_response.headers["cache-control"]


@then(parse("the <{directive}> directive should be set to <{value}> seconds"))
def check_directive(basic_response: httpx.Response, directive: str, value: int) -> None:
    """Ensure the given cache-control directive is set to the given value."""
    assert f"{directive}={value}" in basic_response.headers["cache-control"]


@then("the Globus Search response should be added to the local cache")
def verify_cached(test_client: TestClient, mocker: MockFixture) -> None:
    """Verify the response was served from the cache."""
    spy = mocker.spy(test_client.app.globus_client, name="search")

    test_client.get(url="/")

    assert spy.spy_return.extensions["from_cache"]


@then("the server should not query Globus Search again")
def check_globus_search_calls(mock_globus_search: MockRouter) -> None:
    """Ensure the Globus Search service isn't called for cached responses."""
    assert mock_globus_search.routes["post_search"].call_count == 1
