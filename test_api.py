import pytest
import requests

SOLR_BASE = "http://esgf-node.ornl.gov/esg-search/search"
LOCAL_BASE = "http://127.0.0.1:8000"


def esg_search(base_url, **search):
    """Return an esg-search response as a dictionary."""
    if "format" not in search:
        search["format"] = "application/solr+json"
    response = requests.get(base_url, params=search)
    response.raise_for_status()
    return response.json()


def compare_facets(r1, r2):
    """Same facets and counts?"""

    def _parse_facets(response):
        """Extract facets and counts into a easier structure to compare."""
        facets = response["facet_counts"]["facet_fields"]
        out = {}
        for key, value in facets.items():
            out[key] = {label: count for label, count in zip(value[::2], value[1::2])}
        return out

    f1 = _parse_facets(r1)
    f2 = _parse_facets(r2)
    assert not f1.keys() ^ f2.keys()
    for f in f1.keys() & f2.keys():
        assert not f1[f].keys() ^ f2[f].keys()
        for key, value in f1[f].items():
            assert value == f2[f][key]


def compare_basic(r1, r2):
    """Basic info?"""
    # general structure checks
    assert not r1.keys() ^ r2.keys()
    assert r1["response"]["numFound"] == r2["response"]["numFound"]


@pytest.mark.parametrize(
    "query",
    [
        {
            "facets": "project",
            "limit": 0,
        },
        {
            "project": "CMIP3",
            "time_frequency": "mon",
            "facets": "experiment,realm",
            "type": "File",
            "latest": True,
        },
        {
            "project": "CMIP6",
            "time_frequency": "day",
            "facets": "experiment,model",
            "replica": False,
        },
    ],
)
def test_queries(query):
    r1 = esg_search(SOLR_BASE, **query)
    r2 = esg_search(LOCAL_BASE, **query)
    compare_basic(r1, r2)
    compare_facets(r1, r2)
