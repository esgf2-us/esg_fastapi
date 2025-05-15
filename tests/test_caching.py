from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from esg_fastapi.api.main import app_factory
from esg_fastapi.api.versions.v1.models import ESGSearchQuery


def test_search_globus_cache(mocker: MagicMock) -> None:
    """Ensure responses are cached."""
    app = app_factory()
    client = TestClient(app)

    # Mock the Globus Search client and its response
    mock_globus_search_client = mocker.patch("esg_fastapi.api.versions.v1.routes.SearchClient")
    mock_globus_search_client_instance = MagicMock()
    mock_globus_search_client.return_value = mock_globus_search_client_instance
    mock_globus_search_client_instance.post_search.return_value = MagicMock(
        data={"count": 0, "total": 1, "offset": 0, "has_next_page": True, "gmeta": []}
    )

    # Mock settings
    mocker.patch("esg_fastapi.api.versions.v1.routes.settings.globus_search_index", "test_index")
    mocker.patch("esg_fastapi.api.versions.v1.routes.settings.globus_client_id", "test_id")
    mocker.patch("esg_fastapi.api.versions.v1.routes.settings.globus_client_secret", "test_secret")

    # Create a sample ESGSearchQuery
    esg_query = ESGSearchQuery(query="test_query")

    # Mock cache
    mock_cache = {}
    mocker.patch("esg_fastapi.api.versions.v1.routes.cache", mock_cache)

    # First request
    response1 = client.get("/", params=esg_query.model_dump(exclude_none=True))
    assert response1.status_code == 200
    # Each incoming query is two globus search queries
    assert mock_globus_search_client_instance.post_search.call_count == 2
    assert len(mock_cache) == 1

    # Second request with the same query (should be served from cache)
    mock_globus_search_client_instance.post_search.reset_mock()  # Reset call count
    response2 = client.get("/", params=esg_query.model_dump(exclude_none=True))
    assert response2.status_code == 200
    mock_globus_search_client_instance.post_search.assert_not_called()  # Should not be called again

    # Verify that the responses are identical
    assert response1.json() == response2.json()
