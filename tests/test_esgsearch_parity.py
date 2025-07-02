"""Step definitions for Behave/Cucumber style tests."""

import json
from pathlib import Path
from typing import TypedDict

from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when
from pytest_bdd.parsers import parse
from respx import MockRouter

from esg_fastapi.api.models import ESGSearchResponse, GlobusSearchQuery, GlobusSearchResult

scenarios("ESGSearch_Parity")


class SearchParityFixture(TypedDict):
    """Type hint for example request/response fixtures loaded from JSON files."""

    request: str
    globus_query: GlobusSearchQuery
    globus_response: GlobusSearchResult
    esg_search_response: ESGSearchResponse


class ComparisonFixture(SearchParityFixture):
    """RequestResponseFixture with fastapi_response populated."""

    fastapi_response: dict


@given(parse("a {query_example}"), target_fixture="json_example")
def load_example(query_example: Path) -> SearchParityFixture:
    """Load RequestResponseFixture from JSON file."""
    fixture_path = Path("tests", "fixtures", query_example)
    with fixture_path.open() as fixture:
        return json.load(fixture)


@when("the request is sent to ESG FastAPI", target_fixture="responses")
def send_request(
    json_example: SearchParityFixture, mock_globus_search: MockRouter, test_client: TestClient
) -> ComparisonFixture:
    """Send request to ESG FastAPI and add its response to the fixture."""
    mock_globus_search.routes["post_search"].respond(200, json=json_example["globus_response"], headers={"server-timing": 'total=111.84; "total"'})

    response = test_client.get(url="/", params=json_example["request"]).json()
    return {
        **json_example,
        "fastapi_response": response,
    }


@then("the ESG Fast API response should be the same as the ESG Search response")
def compare_responses(responses: ComparisonFixture) -> None:
    """Compare the ESG Fast API response to the ESG Search response to ensure that the responses are indistinguishable.

    Notes:
    - We modify the fixtures during the test so that we don't have to remember for each fixture
    """
    for source in ["fastapi_response", "esg_search_response"]:
        # Sort the fq and facet_fields lists before comparison
        if isinstance(responses[source]["responseHeader"]["params"]["fq"], list):
            responses[source]["responseHeader"]["params"]["fq"].sort()
        responses[source]["facet_counts"]["facet_fields"] = sorted(responses[source]["facet_counts"]["facet_fields"])

        # Query time is expected to vary
        responses[source]["responseHeader"]["QTime"] = 1

        # Scoring is expected to vary
        responses[source]["response"]["maxScore"] = 1
        for doc in responses[source]["response"]["docs"]:
            doc["score"] = 1

    assert responses["esg_search_response"] == responses["fastapi_response"]
