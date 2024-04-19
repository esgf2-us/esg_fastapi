import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from esg_fastapi import api
from esg_fastapi.api.versions.v1.routes import SearchParityFixture


@pytest.fixture()
def json_example() -> SearchParityFixture:
    """Loads a JSON fixture file with an example request and Globus response.

    Returns:
        SearchParityFixture: A dictionary with the example request and Globus response.
    """
    fixture_path = Path("tests", "fixtures", "metagrid_default_request.json")
    with fixture_path.open() as fixture:
        return json.load(fixture)


def test_fixture_generation(json_example: SearchParityFixture, mocker: MockerFixture) -> None:
    """Ensure that generated fixture format is the same given the same query responses."""
    client = TestClient(api.wsgi_factory())
    mocker.patch(
        "esg_fastapi.api.versions.v1.routes.SearchClient.post_search",
        return_value=mocker.Mock(data=json_example["globus_response"]),
    )
    mocker.patch(
        "esg_fastapi.api.versions.v1.routes.requests.get",
        return_value=mocker.Mock(json=mocker.Mock(return_value=json_example["esg_search_response"])),
    )
    response = client.get(
        url="/make_fixture",
        params=json_example["request"],
    ).json()

    assert response == json_example
