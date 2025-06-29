"""Step definitions for Behave/Cucumber style tests."""

from typing import Literal, TypedDict

from fastapi.testclient import TestClient
from httpx._models import Response
from opentelemetry import propagate, trace
from opentelemetry.sdk.trace import TracerProvider
from pytest_bdd import given, scenarios, then, when
from pytest_bdd.parsers import parse
from respx import MockRouter

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
def send_request(endpoint: str, test_client: TestClient) -> ProbeResponse:
    """Send request to ESG FastAPI and return its response as a fixture."""
    return ProbeResponse.model_validate(test_client.get(endpoint).json())


@then(parse("it should return a positive {status}"))
def compare_responses(status: Literal["ready", "live"], probe_response: ProbeResponse) -> None:
    """Ensure the expected response is returned for the probe."""
    assert status == probe_response.status


@given("the client provides a trace header", target_fixture="trace_header")
def set_trace_header() -> dict[str, str]:
    """Generate a `traceparent` header."""
    return {"traceparent": "00-418206ee4c0156a2f61ceffee287d692-6de132c5f8346556-01"}


@when("a request is sent upstream")
def send_upstream(mock_globus_search: MockRouter):
    pass


@when("a response is returned to the client", target_fixture="response")
def return_response(test_client: TestClient, trace_header: dict[str, str]) -> Response:
    """Get a response to test with the `traceparent` header set."""
    trace.set_tracer_provider(TracerProvider())
    return test_client.get("/", headers=trace_header)


@then("the response should include the same trace header")
def validate_response_trace_header(trace_header: dict[str, str], response: Response) -> None:
    """Ensure the `trace_id` of the `traceparent` header returned in the response matches the one sent by the client."""
    expected_ctx = propagate.extract(carrier=trace_header)
    expected_trace_id = trace.get_current_span(expected_ctx).get_span_context().trace_id

    response_ctx = propagate.extract(carrier=response.headers)
    response_trace_id = trace.get_current_span(response_ctx).get_span_context().trace_id

    assert expected_trace_id == response_trace_id


@then("upstream requests should include the same trace header")
def validate_upstream_request_trace_header(mock_globus_search: MockRouter, trace_header: dict[str, str]) -> None:
    """Ensure the `trace_id` of the `traceparent` header sent upstream matches the one sent by the client."""
    expected_ctx = propagate.extract(carrier=trace_header)
    expected_trace_id = trace.get_current_span(expected_ctx).get_span_context().trace_id

    request_ctx = propagate.extract(carrier=mock_globus_search.routes["post_search"].calls[0].request.headers)
    request_trace_id = trace.get_current_span(request_ctx).get_span_context().trace_id

    assert expected_trace_id == request_trace_id
