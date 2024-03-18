"""
A REST API for Globus-based searches that mimics esg-search.
This API is so that community tools that are based on the esg-search
RESTful API need not change to be compatible with the new Globus indices.
If you are designing a new project, you should look to use the globus-sdk
directly and this is only a small wrapper around the `post_search`
functionality. The standalone script does not need installed. You will
need FastAPI on which it is based and the Globus sdk.

python -m pip install fastapi[all] globus_sdk

This will also install Uvicorn (an ASGI web server implementation for Python).
This allows you to test this locally with:

uvicorn concept:app --reload


Questions:
- format: do we need to be able to return the two formats?
- distrib: how should this behave?
- latest: does not work with CMIP3
"""

import time
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import FastAPI, Query
from globus_sdk import SearchClient, SearchQuery

INDEX_ID = "ea4595f4-7b71-4da7-a1f0-e3f5d8f7f062"  # ORNL holdings

app = FastAPI()


def form_globus_query(search: dict[str, Any]) -> SearchQuery:
    """Form a globus SearchQuery from a dictionary of search facets."""
    # remove these from the search, we need to decide how they should behave
    for d in ["format", "distrib"]:
        del search[d]

    # Build up a query, first we handle the non-general search facets...
    query = SearchQuery(search.pop("query") if "query" in search else "")
    query.set_limit(search.pop("limit"))
    query.set_offset(search.pop("offset"))

    # ...and if facets are desired...
    if "facets" in search:
        facets = search.pop("facets")
        for facet in facets.split(","):
            facet = facet.strip()
            query.add_facet(facet, facet, size=1000)  # is that big enough?

    # ...and now all the filters.
    for key, value in search.items():
        if not value:
            continue
        if isinstance(value, str):
            value = [v.strip() for v in value.split(",")]
        if not isinstance(value, list):
            value = [value]
        query.add_filter(key, value, type="match_any")

    return query


def search_to_fq(search: dict[str, Any]) -> list[str]:
    """Convert the search to the `fq` field in the response."""
    skips = ["limit", "offset", "format", "facets", "latest"]
    fq = []
    for facet, value in search.items():
        if facet in skips:
            continue
        if isinstance(value, list) and len(value) == 1:
            value = value[0]
        if isinstance(value, str):
            value = [v.strip() for v in value.split(",")]
            fq.append(" || ".join([f'{facet}:"{val}"' for val in value]))
        else:
            fq.append(f"{facet}:{value}")
    return fq


def globus_response_to_solr(
    response: dict[str, Any], QTime: int = 0, search: dict = {}
) -> dict[str, Any]:
    """Convert the Globus search response to a Solr response.

    Parameters
    ----------
    QTime
        The optional query time in milliseconds. Unlike the Solr response, the QTime is
        not part of the Globus response and will include transfer times.
    search
        The dictionary containing the search. If given, we will use this to encode the
        `fq` field the header of the response.

    """
    # Unpack the response: facets and records (gmeta/docs)
    facet_map = {}
    facets = []
    if "facet_results" in response:
        fr = response["facet_results"]
        for x in fr:
            arr = []
            facets.append(x["name"])
            for y in x["buckets"]:
                arr.append(y["value"])
                arr.append(y["count"])
            facet_map[x["name"]] = arr

    # Unpack the dataset Records
    docs = []
    for x in response["gmeta"]:
        rec = x["entries"][0]["content"]
        rec["id"] = x["subject"]
        docs.append(rec)

    # Package the response
    ret = {
        "responseHeader": {
            "status": 0,
            "QTime": QTime,
            "params": {
                "facet.field": facets,
                "df": "text",
                "q.alt": "*:*",
                "indent": "true",
                "echoParams": "all",
                "fl": "*,score",
                "start": str(response["offset"]),
                "fq": search_to_fq(search),
                "rows": "1",
                "q": "*:*",
                "shards": "esgf-data-node-solr-query:8983/solr/datasets",
                "tie": "0.01",
                "facet.limit": "1000",  # -1 does not work for globus
                "qf": "text",
                "facet.method": "enum",
                "facet.mincount": "1",
                "facet": "true",
                "wt": "json",
                "facet.sort": "lex",
            },
        },
        "response": {
            "numFound": response["total"],
            "start": response["offset"],
            "maxScore": 1.0,  # ???
            "docs": docs,
        },
    }
    if len(facet_map) > 0:
        ret["facet_counts"] = {"facet_fields": facet_map}
        for category in ["queries", "ranges", "intervals", "heatmaps"]:  # ???
            ret["facet_counts"][f"facet_{category}"] = {}
    return ret


@app.get("/")
async def query(
    access: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    activity: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    activity_drs: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    activity_id: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    atmos_grid_resolution: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    branch_method: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    campaign: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    Campaign: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    catalog_version: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    cf_standard_name: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    cmor_table: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    contact: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    Conventions: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    creation_date: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    data_node: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    data_specs_version: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    data_structure: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    data_type: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    dataset_category: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    dataset_status: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    dataset_version: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    dataset_version_number: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    datetime_end: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    deprecated: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    directory_format_template_: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    ensemble: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    ensemble_member: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    ensemble_member_: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    experiment: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    experiment_family: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    experiment_id: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    experiment_title: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    forcing: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    frequency: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    grid: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    grid_label: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    grid_resolution: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    height_units: Annotated[
        list[str] | None,
        Query(alias="height-units", description=""),
    ] = None,
    index_node: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    institute: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    institution: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    institution_id: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    instrument: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    land_grid_resolution: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    master_gateway: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    member_id: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    metadata_format: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    mip_era: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    model: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    model_cohort: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    model_version: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    nominal_resolution: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    ocean_grid_resolution: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    Period: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    period: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    processing_level: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    product: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    project: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    quality_control_flags: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    range: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    realm: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    realm_drs: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    region: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    regridding: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    run_category: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    Science_Driver: Annotated[
        list[str] | None,
        Query(alias="Science Driver", description=""),
    ] = None,
    science_driver_: Annotated[
        list[str] | None,
        Query(alias="science driver", description=""),
    ] = None,
    science_driver: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    seaice_grid_resolution: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    set_name: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    short_description: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    source: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    source_id: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    source_type: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    source_version: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    source_version_number: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    status: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    sub_experiment_id: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    table: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    table_id: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    target_mip: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    target_mip_list: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    target_mip_listsource: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    target_mip_single: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    time_frequency: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    tuning: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    variable: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    variable_id: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    variable_label: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    variable_long_name: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    variant_label: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    version: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    versionnum: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    year_of_aggregation: Annotated[
        list[str] | None,
        Query(description=""),
    ] = None,
    query: Annotated[
        str | None,
        Query(description="a general search string"),
    ] = None,
    format: Annotated[
        Literal["application/solr+xml", "application/solr+json"],
        Query(description="the type of data returned in the response"),
    ] = "application/solr+xml",
    type: Annotated[
        Literal["Dataset", "File", "Aggregation"],
        Query(description="the type of database record"),
    ] = "Dataset",
    bbox: Annotated[
        str | None,
        Query(description="the geospatial search box [west, south, east, north]"),
    ] = None,
    start: Annotated[
        datetime | None,
        Query(description="beginning of the temporal coverage in the dataset"),
    ] = None,
    end: Annotated[
        datetime | None,
        Query(description="ending of the temporal coverage in the dataset"),
    ] = None,
    _from: Annotated[
        datetime | None,
        Query(
            alias="from",  # because you can't call a argument `from`
            description="return records last modified after this timestamp",
        ),
    ] = None,
    to: Annotated[
        datetime | None,
        Query(description="return records last modified before this timestamp"),
    ] = None,
    offset: Annotated[
        int,
        Query(ge=0, description="the number of records to skip"),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=0, description="the number of records to return"),
    ] = 10,
    replica: Annotated[
        bool | None,
        Query(description="enable to include replicas in the search results"),
    ] = None,
    latest: Annotated[
        bool,
        Query(description="enable to only return the latest versions"),
    ] = True,
    distrib: Annotated[
        bool,
        Query(description="enable to search across all federated nodes"),
    ] = True,
    facets: Annotated[
        str | None,
        Query(description=""),
    ] = None,
):
    search = {
        key: value for key, value in locals().items() if value is not None
    }  # remove None's
    query = form_globus_query(search)
    response_time = time.time()
    globus_response = SearchClient().post_search(INDEX_ID, query)
    response_time = time.time() - response_time
    solr_response = globus_response_to_solr(
        globus_response,
        QTime=int(response_time * 100),
        search=search,
    )
    return solr_response
