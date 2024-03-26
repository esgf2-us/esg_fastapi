from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal, TypeGuard, cast

from annotated_types import T
from fastapi import Query
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    SerializeAsAny,
    StringConstraints,
)
from pydantic_core import Url


def ensure_list(value: Any):
    return value if isinstance(value, list) else [value]


def one_or_list(value: list[str]) -> str | list[str]:
    if is_list(value) and len(value) == 1:
        return value[0]
    return value


MultiValued = Annotated[list[T], BeforeValidator(ensure_list), Query()]
BoolStr = Annotated[T, BeforeValidator(lambda x: str(x).lower())]
IntStr = Annotated[T, BeforeValidator(lambda x: str(x))]
SolrFQ = Annotated[T, BeforeValidator(one_or_list)]


def is_list(value: Any) -> TypeGuard[list]:
    return isinstance(value, list)


class ESGSearchQuery(BaseModel):
    model_config = ConfigDict(validate_default=True)

    access: MultiValued[str] | None = None
    activity: MultiValued[str] | None = None
    activity_drs: MultiValued[str] | None = None
    activity_id: MultiValued[str] | None = None
    atmos_grid_resolution: MultiValued[str] | None = None
    branch_method: MultiValued[str] | None = None
    campaign: MultiValued[str] | None = None
    Campaign: MultiValued[str] | None = None
    catalog_version: MultiValued[str] | None = None
    cf_standard_name: MultiValued[str] | None = None
    cmor_table: MultiValued[str] | None = None
    contact: MultiValued[str] | None = None
    Conventions: MultiValued[str] | None = None
    creation_date: MultiValued[str] | None = None
    data_node: MultiValued[str] | None = None
    data_specs_version: MultiValued[str] | None = None
    data_structure: MultiValued[str] | None = None
    data_type: MultiValued[str] | None = None
    dataset_category: MultiValued[str] | None = None
    dataset_status: MultiValued[str] | None = None
    dataset_version: MultiValued[str] | None = None
    dataset_version_number: MultiValued[str] | None = None
    datetime_end: MultiValued[str] | None = None
    deprecated: MultiValued[str] | None = None
    directory_format_template_: MultiValued[str] | None = None
    ensemble: MultiValued[str] | None = None
    ensemble_member: MultiValued[str] | None = None
    ensemble_member_: MultiValued[str] | None = None
    experiment: MultiValued[str] | None = None
    experiment_family: MultiValued[str] | None = None
    experiment_id: MultiValued[str] | None = None
    experiment_title: MultiValued[str] | None = None
    forcing: MultiValued[str] | None = None
    frequency: MultiValued[str] | None = None
    grid: MultiValued[str] | None = None
    grid_label: MultiValued[str] | None = None
    grid_resolution: MultiValued[str] | None = None
    height_units: Annotated[MultiValued[str], Query(alias="height-units")] | None = None
    index_node: MultiValued[str] | None = None
    institute: MultiValued[str] | None = None
    institution: MultiValued[str] | None = None
    institution_id: MultiValued[str] | None = None
    instrument: MultiValued[str] | None = None
    land_grid_resolution: MultiValued[str] | None = None
    master_gateway: MultiValued[str] | None = None
    member_id: MultiValued[str] | None = None
    metadata_format: MultiValued[str] | None = None
    mip_era: MultiValued[str] | None = None
    model: MultiValued[str] | None = None
    _model_cohort: Annotated[MultiValued[str], Query(alias="model_cohort")] | None = (
        None
    )
    _model_version: Annotated[MultiValued[str], Query(alias="model_version")] | None = (
        None
    )
    nominal_resolution: MultiValued[str] | None = None
    ocean_grid_resolution: MultiValued[str] | None = None
    Period: MultiValued[str] | None = None
    period: MultiValued[str] | None = None
    processing_level: MultiValued[str] | None = None
    product: MultiValued[str] | None = None
    project: MultiValued[str] | None = None
    quality_control_flags: MultiValued[str] | None = None
    range: MultiValued[str] | None = None
    realm: MultiValued[str] | None = None
    realm_drs: MultiValued[str] | None = None
    region: MultiValued[str] | None = None
    regridding: MultiValued[str] | None = None
    run_category: MultiValued[str] | None = None
    Science_Driver: Annotated[
        MultiValued[str] | None, Query(alias="Science Driver")
    ] = None
    science_driver_: Annotated[
        MultiValued[str] | None, Query(alias="science driver")
    ] = None
    science_driver: MultiValued[str] | None = None
    seaice_grid_resolution: MultiValued[str] | None = None
    set_name: MultiValued[str] | None = None
    short_description: MultiValued[str] | None = None
    source: MultiValued[str] | None = None
    source_id: MultiValued[str] | None = None
    source_type: MultiValued[str] | None = None
    source_version: MultiValued[str] | None = None
    source_version_number: MultiValued[str] | None = None
    status: MultiValued[str] | None = None
    sub_experiment_id: MultiValued[str] | None = None
    table: MultiValued[str] | None = None
    table_id: MultiValued[str] | None = None
    target_mip: MultiValued[str] | None = None
    target_mip_list: MultiValued[str] | None = None
    target_mip_listsource: MultiValued[str] | None = None
    target_mip_single: MultiValued[str] | None = None
    time_frequency: MultiValued[str] | None = None
    tuning: MultiValued[str] | None = None
    variable: MultiValued[str] | None = None
    variable_id: MultiValued[str] | None = None
    variable_label: MultiValued[str] | None = None
    variable_long_name: MultiValued[str] | None = None
    variant_label: MultiValued[str] | None = None
    version: MultiValued[str] | None = None
    versionnum: MultiValued[str] | None = None
    year_of_aggregation: MultiValued[str] | None = None
    query: Annotated[str, Query(description="a general search string")] = '""'
    format: Annotated[
        Literal["application/solr+xml", "application/solr+json"],
        Query(description="the type of data returned in the response"),
    ] = "application/solr+xml"
    type: Annotated[
        Literal["Dataset", "File", "Aggregation"],
        Query(description="the type of database record"),
    ] = "Dataset"
    bbox: Annotated[
        str | None,
        Query(description="the geospatial search box [west, south, east, north]"),
    ] = None
    start: Annotated[
        datetime | None,
        Query(description="beginning of the temporal coverage in the dataset"),
    ] = None
    end: Annotated[
        datetime | None,
        Query(description="ending of the temporal coverage in the dataset"),
    ] = None
    _from: Annotated[
        datetime | None,
        Query(
            alias="from",
            description="return records last modified after this timestamp",
        ),
    ] = None
    to: Annotated[
        datetime | None,
        Query(description="return records last modified before this timestamp"),
    ] = None
    offset: Annotated[
        int,
        Query(ge=0, description="the number of records to skip"),
    ] = 0
    limit: Annotated[
        int,
        Query(ge=0, description="the number of records to return"),
    ] = 0
    replica: Annotated[
        bool | None,
        Query(description="enable to include replicas in the search results"),
    ] = None
    latest: Annotated[
        bool | None, Query(description="enable to only return the latest versions")
    ] = None
    distrib: Annotated[
        bool | None, Query(description="enable to search across all federated nodes")
    ] = None
    facets: (
        Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"\w+(,\w+)*?")]
        | None
    ) = None

    # @field_validator("facets")
    # def csv_to_list(value: str) -> list[str]:
    #     return ensure_list(value.split(","))


class GlobusFilter(BaseModel):
    # TODO: range, geo_bounding_box, exists, not
    # ref: https://docs.globus.org/api/search/reference/post_query/#gfilter
    type: Literal["match_all", "match_any"]


class GlobusMatchFilter(GlobusFilter):
    type: Literal["match_all", "match_any"] = "match_any"
    field_name: str
    # TODO: restrict this to only known fields (maybe after refactor to pull fields live from Solr)
    values: Annotated[list[str | bool], BeforeValidator(ensure_list)]


class GlobusFacet(BaseModel):
    name: str
    # TODO: "date_histogram", "numeric_histogram", "sum", "avg"
    # ref: https://docs.globus.org/api/search/reference/post_query/#gfacet
    type: Literal["terms",] = "terms"
    field_name: str


class GlobusSearchQuery(BaseModel):
    q: str = ""
    advanced: bool = True
    limit: int
    offset: int
    bypass_visible_to: bool = False
    result_format_version: Literal["2019-08-27", "2017-09-01"] = "2019-08-27"
    filter_principal_sets: str | None = None
    filters: list[SerializeAsAny[GlobusFilter]] | None = None
    facets: list[GlobusFacet] | None = None

    # TODO: boosts and sorts


class GlobusMetaEntry(BaseModel):
    content: dict[str, Any]
    entry_id: str | None
    matched_principal_sets: list[str]


class GlobusMetaResult(BaseModel):
    subject: str
    entries: list[GlobusMetaEntry]


class GlobusBucket(BaseModel):
    value: str | dict[Literal["from", "to"], Any]
    count: int


class GlobusFacetResult(BaseModel):
    name: str
    value: float
    buckets: list[GlobusBucket]


class GlobusSearchResult(BaseModel):
    gmeta: list[GlobusMetaResult] | list
    facet_results: list[GlobusFacetResult] | None = None
    offset: int
    count: int
    total: int
    has_next_page: bool
    datatype: Literal["GSearchResult"] = Field(alias="@datatype")
    version: Literal["2017-09-01"] = Field(alias="@version")


class ESGSearchResultParams(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True, validate_default=True, coerce_numbers_to_str=True
    )

    facet_field: None | list[str] = Field(
        alias="facet.field", default=None, exclude=True
    )
    df: str = "text"
    q_alt: str = Field(alias="q.alt", default="*:*")
    indent: str = "true"
    echoParams: str = "all"
    fl: str = "*,score"
    start: Decimal
    fq: SolrFQ
    rows: Decimal = cast(Decimal, 10)
    q: str
    shards: Url = Url("esgf-data-node-solr-query:8983/solr/datasets")
    tie: Decimal = cast(Decimal, 0.01)
    facet_limit: Decimal = Field(alias="facet.limit", default=-1)
    qf: str = "text"
    facet_method: str = Field(alias="facet.method", default="enum")
    facet_mincount: IntStr = Field(alias="facet.mincount", default=1)
    facet: BoolStr = "true"
    wt: Literal["json", "xml"] = "json"
    facet_sort: str = Field(alias="facet.sort", default="lex")


class ESGSearchHeader(BaseModel):
    status: int = 0
    QTime: int
    params: ESGSearchResultParams


class ESGSearchResult(BaseModel):
    numFound: int
    start: int
    maxScore: float = 0.0
    docs: list[dict[str, Any]]


class ESGFSearchFacetResult(BaseModel):
    facet_queries: dict = {}
    facet_fields: dict[str, list] = {}
    facet_ranges: dict = {}
    facet_intervals: dict = {}
    facet_heatmaps: dict = {}


class ESGSearchResponse(BaseModel):
    responseHeader: ESGSearchHeader
    response: ESGSearchResult
    facet_counts: ESGFSearchFacetResult = ESGFSearchFacetResult()
