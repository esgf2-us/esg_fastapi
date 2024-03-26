import json
from pathlib import Path

from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when
from pytest_bdd.parsers import parse

from esg_fastapi import api

scenarios("Features")


@given(parse("a {query_example}"), target_fixture="json_example")
def load_example(query_example):
    fixture_path = Path("tests", "fixtures", query_example)
    with fixture_path.open() as fixture:
        return json.load(fixture)


@when("the request is sent to ESG FastAPI", target_fixture="responses")
def send_request(json_example, mocker):
    # Currently raises Warning until next release of FastAPI
    # ref: https://github.com/encode/starlette/issues/2524
    client = TestClient(api)
    mocker.patch(
        "esg_fastapi.api.versions.v1.routes.SearchClient.post_search",
        return_value=mocker.Mock(data=json_example["globus_response"]),
    )
    return {
        "esgsearch_response": json_example["esgsearch_response"],
        "fastapi_response": client.get("/").json(),
    }


@then("the ESG Fast API response should be the same as the ESG Search response")
def compare_responses(responses):
    # Don't test the query time here, give it the benefit of the doubt
    responses["fastapi_response"]["responseHeader"]["QTime"] = responses[
        "esgsearch_response"
    ]["responseHeader"]["QTime"]
    assert responses["esgsearch_response"] == responses["fastapi_response"]
