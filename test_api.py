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


def compare_response(r1, r2) -> bool:
    """Are these reponses the 'same'?"""
    assert not set(r1.keys()) ^ set(r2.keys())


q = {"project": "CMIP3", "time_frequency": "mon"}
r1 = esg_search(SOLR_BASE, **q)
r2 = esg_search(LOCAL_BASE, **q)
compare_response(r1, r2)
