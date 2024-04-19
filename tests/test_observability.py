"""Step definitions for Behave/Cucumber style tests."""

from typing import Literal, TypedDict

from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when
from pytest_bdd.parsers import parse

from esg_fastapi import api
from esg_fastapi.observability.models import ProbeResponse

scenarios("Observability")


class RequestResponseFixture(TypedDict):
    """Type hint for example request/response fixtures loaded from JSON files."""

    request: dict
    globus_response: dict
    esgsearch_response: dict


class ComparisonFixture(RequestResponseFixture):
    """RequestResponseFixture with fastapi_response populated."""

    fastapi_response: dict


@given(parse("a {probe_type}"))
def load_example(probe_type: Literal["ready", "live"]) -> None:
    """Handle the type of probe to be tested (Currently unused)."""


@when(parse("its {endpoint} is querried"), target_fixture="probe_response")
def send_request(endpoint: str) -> ProbeResponse:
    """Send request to ESG FastAPI and return its response as a fixture.

    Notes:
    - We use the TestClient from FastAPI to send the request to the ESG FastAPI service
      which currently raises a Warning until the next release of FastAPI.
      ref: https://github.com/encode/starlette/issues/2524
    """
    client = TestClient(api.wsgi_factory())

    return ProbeResponse.model_validate(client.get(endpoint).json())


@then(parse("it should return a positive {status}"))
def compare_responses(status: Literal["ready", "live"], probe_response: ProbeResponse) -> None:
    """Ensure the expected response is returned for the probe."""
    assert status == probe_response.status
