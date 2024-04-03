"""Step definitions for Behave/Cucumber style tests."""

import json
from pathlib import Path
from typing import TypedDict

from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when
from pytest_bdd.parsers import parse
from pytest_mock import MockerFixture

from esg_fastapi import api

scenarios("ESGSearch_Parity")


class RequestResponseFixture(TypedDict):
    """Type hint for example request/response fixtures loaded from JSON files."""

    request: dict
    globus_response: dict
    esgsearch_response: dict


class ComparisonFixture(RequestResponseFixture):
    """RequestResponseFixture with fastapi_response populated."""

    fastapi_response: dict


@given(parse("a {query_example}"), target_fixture="json_example")
def load_example(query_example: Path) -> RequestResponseFixture:
    """Load RequestResponseFixture from JSON file."""
    fixture_path = Path("tests", "fixtures", query_example)
    with fixture_path.open() as fixture:
        return json.load(fixture)


@when("the request is sent to ESG FastAPI", target_fixture="responses")
def send_request(
    json_example: RequestResponseFixture, mocker: MockerFixture
) -> ComparisonFixture:
    """Send request to ESG FastAPI and add its response to the fixture.

    Notes:
    - We use the TestClient from FastAPI to send the request to the ESG FastAPI service
      which currently raises a Warning until the next release of FastAPI.
      ref: https://github.com/encode/starlette/issues/2524
    """
    client = TestClient(api)
    mocker.patch(
        "esg_fastapi.api.versions.v1.routes.SearchClient.post_search",
        return_value=mocker.Mock(data=json_example["globus_response"]),
    )
    return {**json_example, "fastapi_response": client.get("/").json()}


@then("the ESG Fast API response should be the same as the ESG Search response")
def compare_responses(responses: ComparisonFixture) -> None:
    """Compare the ESG Fast API response to the ESG Search response to ensure that the responses are indistinguishable.

    Notes:
    - Before comparison, we copy the query time from the ESG Search response to the FastAPI response. We do that in the test
      so that we don't have to modify each test fixture to meet this expectation.
    """
    responses["fastapi_response"]["responseHeader"]["QTime"] = responses[
        "esgsearch_response"
    ]["responseHeader"]["QTime"]

    assert responses["esgsearch_response"] == responses["fastapi_response"]
