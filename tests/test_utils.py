"""Test suite for the utils module.

This module contains various utility functions that do not fit well in other modules.
"""

import pytest

from esg_fastapi.api.models import ESGSearchQuery


def test_one_or_list_single_item() -> None:
    """Given a list of len() > 1, return the list unchanged."""
    from esg_fastapi.utils import one_or_list

    assert one_or_list([1, 2, 3]) == [1, 2, 3]


def test_one_or_list_single_item_in_list() -> None:
    """Unwrap a length 1 list[int]."""
    from esg_fastapi.utils import one_or_list

    assert one_or_list([1]) == 1


def test_one_or_list_string() -> None:
    """Unwrap a length 1 list[int]."""
    from esg_fastapi.utils import one_or_list

    assert one_or_list("hello") == "hello"


def test_one_or_list_empty_list() -> None:
    """Empty list is unchanged.

    TODO: is this the correct behavior?
    """
    from esg_fastapi.utils import one_or_list

    assert one_or_list([]) == []


def test_ensure_list_empty_list() -> None:
    """Empty list is unchanged."""
    from esg_fastapi.utils import ensure_list

    assert ensure_list([]) == []


def test_ensure_list_empty_str() -> None:
    """Empty string is wrapped in a list."""
    from esg_fastapi.utils import ensure_list

    assert ensure_list("") == [""]


def test_ensure_list_populated_list() -> None:
    """Populated list is unchanged."""
    from esg_fastapi.utils import ensure_list

    assert ensure_list([1, 2, 3, 4]) == [1, 2, 3, 4]


def test_get_current_trace_id() -> None:
    """Test that the current trace ID is returned correctly."""
    from opentelemetry import trace

    from esg_fastapi.utils import get_current_trace_id

    # Create a mock span with a known trace ID
    mock_span = trace.get_current_span()
    mock_span_context = mock_span.get_span_context()
    mock_trace_id = mock_span_context.trace_id

    # Set the current span context
    trace.set_span_in_context(mock_span)

    # Call the function and check the result
    assert get_current_trace_id() == trace.format_trace_id(mock_trace_id)


@pytest.mark.parametrize(
    ("search_query", "expectation"),
    [
        ({"type": "Dataset", "project": "CMIP6", "latest": True}, ["type:Dataset", 'project:"CMIP6"', "latest:True"]),
        ({"type": "Dataset"}, "type:Dataset"),
        (
            {
                "type": "Dataset",
                "project": "CMIP6",
                "data_node": "esgf-data1.llnl.gov,esgf-node.ornl.gov,eagle.alcf.anl.gov",
            },
            [
                "type:Dataset",
                'project:"CMIP6"',
                'data_node:"esgf-data1.llnl.gov" || data_node:"esgf-node.ornl.gov" || data_node:"eagle.alcf.anl.gov"',
            ],
        ),
    ],
)
def test_fq_field_from_esg_search_query(search_query, expectation) -> None:
    from esg_fastapi.utils import fq_field_from_esg_search_query

    q = ESGSearchQuery(**search_query)
    assert sorted(fq_field_from_esg_search_query(q)) == sorted(expectation)
