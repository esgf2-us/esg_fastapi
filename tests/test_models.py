from contextlib import nullcontext as does_not_raise
from datetime import datetime

import pytest
from pytest import raises

from esg_fastapi.api.models import (
    ESGFSearchFacetResult,
    ESGSearchHeader,
    ESGSearchQuery,
    ESGSearchQueryBase,
    ESGSearchResponse,
    ESGSearchResult,
    ESGSearchResultParams,
    GlobusFacet,
    GlobusMatchFilter,
    GlobusSearchQuery,
)

test_attrs = ["activity_id", "data_node", "source_id"]
test_values = ["frogblast", "the vent", "cores"]
facet_str = ", ".join(test_attrs)
filter_dict = {attr: value for attr, value in zip(test_attrs, test_values)}
goal_globus_facets = [GlobusFacet(name=attr, field_name=attr) for attr in test_attrs]
goal_globus_filters = [GlobusMatchFilter(field_name=k, values=v) for k, v in zip(test_attrs, test_values)]
goal_fqs = [f'{k}:"{v}"' for k, v in zip(test_attrs, test_values)]


@pytest.mark.parametrize(
    ("attr",    "source",             "expectation",      "comparison"), [
    # ---------------------------------------------------------
    ("filters", goal_globus_filters, does_not_raise(),   goal_globus_filters),
    ("filters", object(),            raises(ValueError), goal_globus_filters),
    ("facets",  facet_str,           does_not_raise(),   goal_globus_facets),
    ("facets",  goal_globus_facets,  does_not_raise(),   goal_globus_facets),
    ("facets",  object(),            raises(ValueError), goal_globus_facets),
    ],
)  # fmt: skip
def test_GlobusSearchQuery_facet_creation(attr, source, expectation, comparison) -> None:
    """Ensure GlobusSearchQuery properly converts supported types and raises for non-supported."""
    with expectation:
        query = GlobusSearchQuery(**{attr: source}, limit=0, offset=0)
        assert getattr(query, attr) == comparison


@pytest.mark.parametrize(
    argnames="query_params",
    argvalues=[
        {"query": "frogblast:the vent:cores", "offset": 0, "limit": 0},
        {"query": "frogblast:the vent:cores", "offset": 867, "limit": 5309},
    ],
)
def test_GlobusSearchQuery_from_esg_search_query_meta_fields(query_params: dict) -> None:
    """Ensure `GlobusSearchQuery.from_esg_search_query` correctly maps meta fields from `ESGSearchQuery`."""
    esg_search_query = ESGSearchQuery(**query_params)
    globus_query = GlobusSearchQuery.from_esg_search_query(esg_search_query)

    assert globus_query.q == esg_search_query.query
    assert globus_query.offset == esg_search_query.offset
    assert globus_query.limit == esg_search_query.limit


@pytest.mark.parametrize(
    argnames=("name", "value", "expected_filter"),
    argvalues=[
        ("activity_id", "frogblast", {"type": "match_any", "field_name": "activity_id", "values": ["frogblast"]}),
        ("min_version", 0, {"type": "range", "field_name": "version", "values": [{"from": 0, "to": "*"}]}),
        ("max_version", 1, {"type": "range", "field_name": "version", "values": [{"from": "*", "to": 1}]}),
        ("from_", 0, {"type": "range", "field_name": "_timestamp", "values": [{"from": datetime.fromisoformat("1970-01-01T00:00:00Z"), "to": "*"}]}),
        ("to", 1, {"type": "range", "field_name": "_timestamp", "values": [{"from": "*", "to": datetime.fromisoformat("1970-01-01T00:00:01Z")}]}),
    ],
)
def test_GlobusSearchQuery_from_esg_search_query_filter_fields(name: str, value: str, expected_filter: dict) -> None:
    """Ensure `GlobusSearchQuery.from_esg_search_query` correctly maps filter fields from `ESGSearchQuery`."""
    esg_search_query = ESGSearchQuery(**{name: value})
    filter = GlobusSearchQuery.from_esg_search_query(esg_search_query).filters[0]

    assert expected_filter == filter.model_dump()


@pytest.mark.parametrize(("query_string", "should_be_set"), [("*", False), ("*:*", True)])
def test_GlobusSearchQuery_from_esg_search_query_skips_star(query_string: str, should_be_set: bool) -> None:
    """Do not include query when constructing `GlobusSearchQuery` from `ESGSearchQuery` if query is `*`."""
    query = GlobusSearchQuery.from_esg_search_query(ESGSearchQuery(query=query_string))
    is_set = "q" in query.model_fields_set

    assert is_set == should_be_set


@pytest.mark.parametrize(
    ("attr",    "source",                                                  "expectation",             "comparison"), [
    # -----------------------------------------------------------------------------------------------------------------
    ("fq", 'activity_id:"frogblast"',                                     does_not_raise(),  'activity_id:"frogblast"'),
    ("fq", ['activity_id:"frogblast"', 'data_node:"the vent"'],           does_not_raise(), ['activity_id:"frogblast"', 'data_node:"the vent"']),
    ],
)  # fmt: skip
def test_ESGSearchResult_creation(attr, source, expectation, comparison) -> None:
    """Ensure GlobusSearchQuery properly converts supported types and raises for non-supported."""
    with expectation:
        query = ESGSearchResultParams(fq=source, start=0, q="")
        assert getattr(query, attr) == comparison


@pytest.mark.parametrize(
    (            'source',                     'output',         'expectation'), [
    #------------------------------------------------------------------------------
    ({'facet_fields': {'a':['b',0,'c',1]}}, {'a':('b',0,'c',1)}, does_not_raise()),
    (ESGFSearchFacetResult(),               {},                  does_not_raise()),
    (object(),                              {},                  raises(ValueError)),
    ],
)  # fmt: skip
def test_ESGSearchResponse_facet_counts_creation(source, output, expectation) -> None:
    """Ensure ESGSearchResponse properly converts supported types and raises for non-supported."""
    with expectation:
        response = ESGSearchResponse(
            response=ESGSearchResult(numFound=0, start=0, docs=[]),
            responseHeader=ESGSearchHeader(QTime=1, params=ESGSearchResultParams(start=0, q="", fq="")),
            facet_counts=source,
        )
        assert response.facet_counts.facet_fields == output


def test_queriable_fields() -> None:
    """Non-queriable fields should be excluded from the property."""
    assert all(field not in ESGSearchQuery._queriable_fields() for field in ESGSearchQueryBase.model_fields)
