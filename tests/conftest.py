import pytest
from fastapi.testclient import TestClient

from esg_fastapi.api.main import app_factory


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


