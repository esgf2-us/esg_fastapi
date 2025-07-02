import httpx
import pytest
from fastapi.testclient import TestClient
from respx import MockRouter

from esg_fastapi.api.main import app_factory
from esg_fastapi.api.models import GlobusMetaEntry, GlobusMetaResult, GlobusSearchResult


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


@pytest.fixture
def test_client() -> TestClient:
    """Returns a TestClient instance for testing the FastAPI application.

        This fixture is used to create a test client that can send requests to the FastAPI application
        defined by the `app_factory` function. It is intended to be used in testing scenarios where
        you need to simulate HTTP requests to your application endpoints.

    Returns:
            TestClient: An instance of TestClient configured to interact with the FastAPI application.
    """
    return TestClient(app_factory())
