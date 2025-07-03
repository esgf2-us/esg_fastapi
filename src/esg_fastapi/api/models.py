"""Pydantic models used by v1 of the API and its inheritants.

The models in this module are used to define the structure of the API requests and responses.

They are organized into two main sections:
1. **Models for the ESG Search API**
2. **Models for the Globus Search API**

This provides an easy way to validate and serialize the API requests and responses, ensuring that they conform to the specified structure.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import (
    Annotated,
    Any,
    Literal,
    Self,
    get_args,
)

from fastapi import Query
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    SerializeAsAny,
    StringConstraints,
    computed_field,
    field_validator,
)
from pydantic_core import PydanticUndefined, Url

from esg_fastapi.api.types import (
    ESGSearchFacetField,
    LowerCased,
    MultiValued,
    SolrDoc,
    SolrFQ,
    Stringified,
    SupportedAsFacets,
    SupportedAsFilters,
)
from esg_fastapi.utils import (
    ensure_list,
    fq_field_from_esg_search_query,
    is_sequence_of,
    solr_docs_from_globus_meta_results,
)


class ESGSearchQueryBase(BaseModel):
    """Defines all the meta-fields that aren't part of the data itself, but control the query results."""

    model_config = ConfigDict(
        validate_default=True,
        extra="forbid",
        serialize_by_alias=True,
        populate_by_name=True,
        use_attribute_docstrings=True,
    )

    query: str | None = None
    """A Solr search string."""
    format: Literal["application/solr+xml", "application/solr+json"] = "application/solr+json"
    """The format of the response."""
    bbox: str | None = None
    """The geospatial search box [west, south, east, north]"""
    offset: Annotated[int, Query(ge=0, le=9999)] | None = 0
    """The number of records to skip. Globus Search only allows from 0 to 9999, so we limit it to that range."""
    limit: Annotated[int, Query(ge=0)] | None = 10
    """The number of records to return"""
    replica: bool | None = None
    """Enable to include replicas in the search results"""
    distrib: bool | None = None
    """Enable to search across all federated nodes"""
    facets: Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"\w+(,\w+)*?")] | None = None
    """A comma-separated list of field names to facet on."""

    min_version: int | None = None
    """Constrain query results to `version` field after this date."""
    max_version: int | None = None
    """Constrain query results to `version` field before this date."""

    from_: datetime | None = Query(None, alias="from")
    """Return records last modified after this timestamp"""
    to: datetime | None = None
    """Return records last modified before this timestamp"""


class ESGSearchQuery(ESGSearchQueryBase):
    """Represents the query parameters accepted by the ESG Search API."""

    id: str | None = None
    dataset_id: str | None = None
    type: Literal["Dataset", "File"] = "Dataset"
    """The type of record to search for."""

    access: MultiValued[str] | None = None
    """Access level of the dataset."""
    activity: MultiValued[str] | None = None
    """Activity of the dataset."""
    activity_drs: MultiValued[str] | None = None
    """Activity DRS of the dataset."""
    activity_id: MultiValued[str] | None = None
    """Activity ID of the dataset."""
    atmos_grid_resolution: MultiValued[str] | None = None
    """Atmospheric grid resolution of the dataset."""
    branch_method: MultiValued[str] | None = None
    """Branch method of the dataset."""
    campaign: MultiValued[str] | None = None
    """Campaign of the dataset."""
    Campaign: MultiValued[str] | None = None
    """Campaign of the dataset."""
    catalog_version: MultiValued[str] | None = None
    """Catalog version of the dataset."""
    cf_standard_name: MultiValued[str] | None = None
    """CF standard name of the dataset."""
    cmor_table: MultiValued[str] | None = None
    """CMOR table of the dataset."""
    contact: MultiValued[str] | None = None
    """Contact of the dataset."""
    Conventions: MultiValued[str] | None = None
    """Conventions of the dataset."""
    creation_date: MultiValued[str] | None = None
    """Creation date of the dataset."""
    data_node: MultiValued[str] | None = None
    """Data node of the dataset."""
    data_specs_version: MultiValued[str] | None = None
    """Data specs version of the dataset."""
    data_structure: MultiValued[str] | None = None
    """Data structure of the dataset."""
    data_type: MultiValued[str] | None = None
    """Data type of the dataset."""
    dataset_category: MultiValued[str] | None = None
    """Dataset category of the dataset."""
    dataset_status: MultiValued[str] | None = None
    """Dataset status of the dataset."""
    dataset_version: MultiValued[str] | None = None
    """Dataset version of the dataset."""
    dataset_version_number: MultiValued[str] | None = None
    """Dataset version number of the dataset."""
    datetime_end: MultiValued[str] | None = None
    """Datetime end of the dataset."""
    deprecated: MultiValued[str] | None = None
    """Deprecated of the dataset."""
    directory_format_template_: MultiValued[str] | None = None
    """Directory format template of the dataset."""
    ensemble: MultiValued[str] | None = None
    """Ensemble of the dataset."""
    ensemble_member: MultiValued[str] | None = None
    """Ensemble member of the dataset."""
    ensemble_member_: MultiValued[str] | None = None
    """Ensemble member of the dataset."""
    experiment: MultiValued[str] | None = None
    """Experiment of the dataset."""
    experiment_family: MultiValued[str] | None = None
    """Experiment family of the dataset."""
    experiment_id: MultiValued[str] | None = None
    """Experiment ID of the dataset."""
    experiment_title: MultiValued[str] | None = None
    """Experiment title of the dataset."""
    forcing: MultiValued[str] | None = None
    """Forcing of the dataset."""
    frequency: MultiValued[str] | None = None
    """Frequency of the dataset."""
    grid: MultiValued[str] | None = None
    """Grid of the dataset."""
    grid_label: MultiValued[str] | None = None
    """Grid label of the dataset."""
    grid_resolution: MultiValued[str] | None = None
    """Grid resolution of the dataset."""
    height_units: MultiValued[str] | None = Query(alias="height-units", default=None)
    """Height units of the dataset."""
    index_node: MultiValued[str] | None = None
    """Index node of the dataset."""
    institute: MultiValued[str] | None = None
    """Institute of the dataset."""
    institution: MultiValued[str] | None = None
    """Institution of the dataset."""
    institution_id: MultiValued[str] | None = None
    """Institution ID of the dataset."""
    instrument: MultiValued[str] | None = None
    """Instrument of the dataset."""
    land_grid_resolution: MultiValued[str] | None = None
    """Land grid resolution of the dataset."""
    master_gateway: MultiValued[str] | None = None
    """Master gateway of the dataset."""
    member_id: MultiValued[str] | None = None
    """Member ID of the dataset."""
    metadata_format: MultiValued[str] | None = None
    """Metadata format of the dataset."""
    mip_era: MultiValued[str] | None = None
    """MIP era of the dataset."""
    model: MultiValued[str] | None = None
    """Model of the dataset."""
    _model_cohort: Annotated[MultiValued[str], Query(alias="model_cohort")] | None = None
    """Model cohort of the dataset."""
    _model_version: Annotated[MultiValued[str], Query(alias="model_version")] | None = None
    """Model version of the dataset."""
    nominal_resolution: MultiValued[str] | None = None
    """Nominal resolution of the dataset."""
    ocean_grid_resolution: MultiValued[str] | None = None
    """Ocean grid resolution of the dataset."""
    Period: MultiValued[str] | None = None
    """Period of the dataset."""
    period: MultiValued[str] | None = None
    """Period of the dataset."""
    processing_level: MultiValued[str] | None = None
    """Processing level of the dataset."""
    product: MultiValued[str] | None = None
    """Product of the dataset."""
    project: str | None = None
    """Project of the dataset."""
    quality_control_flags: MultiValued[str] | None = None
    """Quality control flags of the dataset."""
    range: MultiValued[str] | None = None
    """Range of the dataset."""
    realm: MultiValued[str] | None = None
    """Realm of the dataset."""
    realm_drs: MultiValued[str] | None = None
    """Realm DRS of the dataset."""
    region: MultiValued[str] | None = None
    """Region of the dataset."""
    regridding: MultiValued[str] | None = None
    """Regridding of the dataset."""
    run_category: MultiValued[str] | None = None
    """Run category of the dataset."""
    Science_Driver: Annotated[MultiValued[str] | None, Query(alias="Science Driver")] = None
    """Science Driver of the dataset."""
    science_driver_: Annotated[MultiValued[str] | None, Query(alias="science driver")] = None
    """Science driver of the dataset."""
    science_driver: MultiValued[str] | None = None
    """Science driver of the dataset."""
    seaice_grid_resolution: MultiValued[str] | None = None
    """Sea ice grid resolution of the dataset."""
    set_name: MultiValued[str] | None = None
    """Set name of the dataset."""
    short_description: MultiValued[str] | None = None
    """Short description of the dataset."""
    source: MultiValued[str] | None = None
    """Source of the dataset."""
    source_id: MultiValued[str] | None = None
    """Source ID of the dataset."""
    source_type: MultiValued[str] | None = None
    """Source type of the dataset."""
    source_version: MultiValued[str] | None = None
    """Source version of the dataset."""
    source_version_number: MultiValued[str] | None = None
    """Source version number of the dataset."""
    status: MultiValued[str] | None = None
    """Status of the dataset."""
    sub_experiment_id: MultiValued[str] | None = None
    """Sub experiment ID of the dataset."""
    table: MultiValued[str] | None = None
    """Table of the dataset."""
    table_id: MultiValued[str] | None = None
    """Table ID of the dataset."""
    target_mip: MultiValued[str] | None = None
    """Target MIP of the dataset."""
    target_mip_list: MultiValued[str] | None = None
    """Target MIP list of the dataset."""
    target_mip_listsource: MultiValued[str] | None = None
    """Target MIP listsource of the dataset."""
    target_mip_single: MultiValued[str] | None = None
    """Target MIP single of the dataset."""
    time_frequency: MultiValued[str] | None = None
    """Time frequency of the dataset."""
    tuning: MultiValued[str] | None = None
    """Tuning of the dataset."""
    variable: MultiValued[str] | None = None
    """Variable of the dataset."""
    variable_id: MultiValued[str] | None = None
    """Variable ID of the dataset."""
    variable_label: MultiValued[str] | None = None
    """Variable label of the dataset."""
    variable_long_name: MultiValued[str] | None = None
    """Variable long name of the dataset."""
    variant_label: MultiValued[str] | None = None
    """Variant label of the dataset."""
    version: MultiValued[str] | None = None
    """Version of the dataset."""
    versionnum: MultiValued[str] | None = None
    """Version number of the dataset."""
    year_of_aggregation: MultiValued[str] | None = None
    """Year of aggregation of the dataset."""
    start: datetime | None = None
    """Beginning of the temporal coverage in the dataset"""
    end: datetime | None = None
    """Ending of the temporal coverage in the dataset"""
    latest: bool | None = None
    """Enable to only return the latest versions"""

    @classmethod
    def _queriable_fields(cls) -> set[str]:
        """All fields that are queriable in Solr."""
        return cls.model_fields.keys() - ESGSearchQueryBase.model_fields.keys()


class GlobusFilter(BaseModel):
    """Parent container model for Globus Search Filter Documents.

    TODO: range, geo_bounding_box, exists, not
    ref: https://docs.globus.org/api/search/reference/post_query/#gfilter
    """

    type: Literal["match_all", "match_any", "range"]
    """The type of filter to apply."""


class GlobusMatchFilter(GlobusFilter):
    """Globus Filter Specialization for Match type filters."""

    type: Literal["match_all", "match_any"] = "match_any"
    """The type of filter to apply."""
    field_name: str
    """The name of the field to filter on."""
    # TODO: restrict this to only known fields (maybe after refactor to pull fields live from Solr)
    values: Annotated[Sequence[str | bool], BeforeValidator(ensure_list)]
    """The values to filter on."""


class GlobusRange(BaseModel):
    """Represents a range in a `GlobusRangeFilter`."""

    model_config = ConfigDict(serialize_by_alias=True)

    from_: datetime | int | Literal["*"] = Field("*", serialization_alias="from")
    to: datetime | int | Literal["*"] = Field("*")


class GlobusRangeFilter(GlobusFilter):
    """Globus Filter Specialization for Range type filters."""

    type: Literal["range"] = "range"
    """The type of filter to apply."""
    field_name: str
    """The name of the field to filter on."""
    values: Sequence[GlobusRange]
    """The values to filter on."""


class GlobusFacet(BaseModel):
    """Represents a Globus Search Facet Document.

    TODO: "date_histogram", "numeric_histogram", "sum", "avg"
    ref: https://docs.globus.org/api/search/reference/post_query/#gfacet
    """

    name: str
    """The name of the facet."""
    type: Literal["terms",] = "terms"
    """The type of facet."""
    field_name: str
    """The name of the field to facet on."""
    size: int = 2_000_000_000  # Globus Search has an undocumented default of 10, no way to say "all". GS dies if too high, somewhere between 2_000_000_000 and 5_000_000_000
    """The number of distinct facet values (buckets) to return."""


class GlobusSearchQuery(BaseModel):
    """Container model to describe the fields of a Globus Search Query Document."""

    model_config = ConfigDict(
        serialize_by_alias=True,  # serialize fields by alias (e.g. "_version" -> "@version")
    )

    @field_validator("facets", mode="before")
    @staticmethod
    def convert_esg_seach_facets_field(value: SupportedAsFacets | None) -> Sequence[GlobusFacet] | None:
        """Convert a comma-and-space-separated list of Globus Facets to a list of GlobusFacet objects.

        Example: "activity_id, data_node, source_id, institution_id, source_type, experiment_id, sub_experiment_id, nominal_resolution, variant_label, grid_label, table_id, frequency, realm, variable_id, cf_standard_name"
        """
        if value is None or is_sequence_of(value, GlobusFacet):
            return value
        elif isinstance(value, str):
            return [
                GlobusFacet(name=facet.strip(), field_name=facet.strip(), type="terms") for facet in value.split(",")
            ]
        else:
            raise ValueError(
                f"Expected input convertible to Sequence[GlobusFacet] one of {get_args(SupportedAsFacets)}, got {type(value)}"
            )

    @classmethod
    def from_esg_search_query(cls, query: ESGSearchQuery) -> Self:
        """Create a new instance of `GlobusSearchResult` from an `ESGSearchQuery`."""
        built_filters: list[GlobusFilter] = []

        if {"min_version", "max_version"} & query.model_fields_set:
            lower_bound = query.min_version if query.min_version is not None else PydanticUndefined
            upper_bound = query.max_version if query.max_version is not None else PydanticUndefined
            built_filters.append(
                GlobusRangeFilter(
                    field_name="version",
                    values=[GlobusRange(from_=lower_bound, to=upper_bound)],
                )
            )

        if {"from_", "to"} & query.model_fields_set:
            built_filters.append(
                GlobusRangeFilter(
                    field_name="_timestamp", values=[GlobusRange(from_=query.from_ or "*", to=query.to or "*")]
                )
            )

        for field, field_value in query.model_dump(exclude_unset=True, include=query._queriable_fields()).items():
            if isinstance(field_value, str):
                # "foo,bar.baz" -> ["foo", "bar", "baz"]  --  "foo" -> ["foo"]
                field_value: list[str] = field_value.split(",")

            # If it's not a string, it Should(TM) already be a list
            built_filters.append(GlobusMatchFilter(field_name=field, values=field_value))

        constructed_fields = {}
        if built_filters:
            constructed_fields["filters"] = built_filters

        for attr in ["limit", "offset", "facets"]:
            attr_value = getattr(query, attr, None)
            if attr_value is not None:
                constructed_fields[attr] = attr_value

        # Although valid, Globus Search crashes with Metagrid's default query of `*`
        # Only set the query if it's not `*`
        if query.query and query.query != "*":
            constructed_fields["q"] = query.query

        return cls(**constructed_fields)

    version_: Literal["query#1.0.0"] = Field(default="query#1.0.0", alias="@version")
    """The version of the query format."""
    q: str | None = None
    """The search query."""
    advanced: bool = True
    """Whether or not to use advanced search."""
    limit: int = 10
    """The maximum number of results to return."""
    offset: int = Field(0, ge=0, le=9999)
    """The number of results to skip."""

    filters: SerializeAsAny[SupportedAsFilters] | None = None
    """A list of filters to apply to the query.
        Note: Globus Filters is a parent model for the specific types of filters that Globus supports.
            The `SerializeAsAny` type annotation is necessary for Pydantic to include attributes defined
            in the child model, but not in the parent model, while still allowing any subtype to be used.
    """

    facets: SupportedAsFacets | None = None
    """A list of facets to apply to the query."""

    # filter_principal_sets: str | None = None
    """A comma-separated list of principal sets to filter on.
       Note: Globus Search wont accept this for an unauthenticated search, so commented out for now.
    """

    # bypass_visible_to: bool = False
    """Whether or not to bypass the visible_to filter.
        Note: Globus Search accepts this one but ignores it for unauthenticated searches,
        so commented out for now to make parsing easier.
    """


class GlobusMetaEntry(BaseModel):
    """Parent container model for Globus GMeta Entries."""

    content: dict[str, Any]
    """The content of the metadata entry."""
    entry_id: str | None
    """The ID of the metadata entry."""
    matched_principal_sets: list[str]
    """A list of principal sets that matched the metadata entry."""


class GlobusMetaResult(BaseModel):
    """Parent container for a group of Globus Search results for a Subject."""

    subject: str
    """The ID of the subject."""
    entries: list[GlobusMetaEntry]
    """A list of metadata entries for the subject."""


class GlobusBucket(BaseModel):
    """Represents a bucket in a Globus Search result."""

    value: str
    """The value of the bucket."""
    count: int
    """The count of items in the bucket."""


class GlobusFacetResult(BaseModel):
    """Represents a facet result in a Globus Search result."""

    name: str
    """The name of the facet."""

    value: float | None = None
    """The value of the facet. Only returned if for `sum` and `avg` queries, which ESG Search doesn't support."""

    buckets: list[GlobusBucket]
    """A list of buckets associated with the facet."""


class GlobusSearchResult(BaseModel):
    """Represents a search result from the Globus platform.

    Ref: https://docs.globus.org/api/search/reference/post_query/#gsearchresult
    """

    gmeta: list[GlobusMetaResult]
    """
    A list of `GlobusMetaResult` objects. These objects represent metadata entries for the search result.
    """

    facet_results: list[GlobusFacetResult] | None = None
    """
    A list of `GlobusFacetResult` objects. These objects represent facet results for the search result. This attribute is optional and can be `None`.
    """

    offset: int
    """
    An integer representing the offset of the search result.
    """

    count: int
    """
    An integer representing the count of items in the search result.
    """

    total: int
    """
    An integer representing the total number of items in the search result.
    """

    has_next_page: bool
    """
    A boolean flag indicating whether there is a next page of search results.
    """


class ESGSearchResultParams(BaseModel):
    """Represents the `params` field of an ESGSearch result."""

    model_config = ConfigDict(validate_default=True)

    facet_field: None | list[str] = Field(alias="facet.field", default=None, exclude=True)
    """
    The `facet_field` attribute is a list of strings representing the fields to use for faceting. If `None`, no faceting will be performed.
    """
    df: str = "text"
    """
    The `df` attribute is a string representing the default field to use for searching. Its default value is "text".
    """
    q_alt: str = Field(alias="q.alt", default="*:*")
    """The `q_alt` attribute is an optional string parameter that represents a Solr "alternative query" string. This attribute is used to provide an additional query string for the search operation. If not provided, the default value is "*:*", which means that all documents will be returned."""
    indent: LowerCased[bool] = True
    """
    The `indent` attribute is a boolean flag indicating whether to indent the JSON response. Its default value is `"true"`.
    """
    echoParams: str = "all"
    """
    A boolean flag indicating whether to echo the parameters in the response. Its default value is "all".
    """
    fl: str = "*,score"
    """
    The `fl` attribute is a comma-separated list of fields to include in the response. Its default value is `"*,score"`.
    """
    start: Stringified[int]
    """
    The `start` attribute is an integer representing the starting index for the search results. Its default value is `0`.
    """
    fq: SolrFQ
    """
    The `fq` attribute is a `SolrFQ` object representing the list of Solr Facet Queries.
    Note: The project field seems to be "special" in the ESG Search Response. It comes back wrapped in
        literal quotes, at least Dataset and Latest do not, ie:
        ```
        "fq":[
            "type:Dataset",
            "project:\"CMIP6\"",
            "latest:true"
        ]
        ```
    """
    rows: Stringified[int] = 10
    """
    The `rows` attribute is an integer representing the maximum number of search results to return. Its default value is `10`.
    """
    q: str
    """
    The `q` attribute is a string representing the query string to use for searching.
    """
    shards: Url = Url("esgf-data-node-solr-query:8983/solr/datasets")
    """
    The `shards` attribute is a `Url` object representing the URL of the Solr shards to use for searching. Its default value is `"esgf-data-node-solr-query:8983/solr/datasets"`.
    """
    tie: Stringified[float] = 0.01
    """
    The `tie` attribute is a float representing the tie-breaking parameter for Solr faceting. Its default value is `0.01`.
    """
    facet_limit: Stringified[int] = Field(alias="facet.limit", default=-1)
    """
    The `facet_limit` attribute is an integer representing the maximum number of facet values to return. Its default value is `-1`, which means that all facet values will be returned.
    """
    qf: str = "text"
    """
    The `qf` attribute is a string representing the query field to use for searching. Its default value is `"text"`.
    """
    facet_method: str = Field(alias="facet.method", default="enum")
    """
    The `facet_method` attribute is a string representing the method to use for faceting. Its default value is `"enum"`.
    """
    facet_mincount: Stringified[int] = Field(alias="facet.mincount", default=1)
    """
    The `facet_mincount` attribute is an integer representing the minimum count required for a facet value to be included in the response. Its default value is `1`.
    """
    facet: LowerCased[bool] = True
    """
    The `facet` attribute is a boolean flag indicating whether to include facet values in the response. Its default value is `"true"`.
    """
    wt: Literal["json", "xml"] = "json"
    """
    The `wt` attribute is a string literal representing the format of the response. Its default value is `"json"`.
    """
    facet_sort: str = Field(alias="facet.sort", default="lex")
    """
    The `facet_sort` attribute is a string literal representing the sorting method to use for facet values. Its default value is `"lex"`.
    """


class ESGSearchHeader(BaseModel):
    """Represents the response header for the ESG Search Result."""

    status: int = 0
    """Status of the response."""
    QTime: int
    """Time taken to process the request."""
    params: ESGSearchResultParams
    """Parameters for the ESG Search Result."""


class ESGSearchResult(BaseModel):
    """Represents a search result from ESG Search."""

    numFound: int
    """Number of documents found."""
    start: int
    """Starting index for the search results."""
    docs: list[SolrDoc]
    """List of documents found."""

    @computed_field
    @property
    def maxScore(self: Self) -> float | None:
        """Maximum score for the search results."""
        return max((record.get("score", 0) for record in self.docs), default=None)


class ESGFSearchFacetResult(BaseModel):
    """Represents a facet result from ESG Search."""

    facet_queries: dict = {}
    """Facet queries for the facet result."""
    facet_fields: ESGSearchFacetField = {}
    """Facet fields for the facet result."""
    facet_ranges: dict = {}
    """Facet ranges for the facet result."""
    facet_intervals: dict = {}
    """Facet intervals for the facet result."""
    facet_heatmaps: dict = {}
    """Facet heatmaps for the facet result."""

    @classmethod
    def from_globus_facet_result(cls, globus_facets: list[GlobusFacetResult] | None) -> Self:
        """Instantiate this class from a list of `GlobusFacetResult`s."""
        facet_fields: ESGSearchFacetField = {}

        # When no facets are requested, Globus doesn't return the field -- `or []` avoids iterating over None
        for facet in globus_facets or []:
            facet_fields[facet.name] = tuple(attr for bucket in facet.buckets for attr in (bucket.value, bucket.count))
        return cls(facet_fields=facet_fields)


class ESGSearchResponse(BaseModel):
    """Represents a response from ESG Search."""

    @classmethod
    def from_results(cls, q: ESGSearchQuery, q_time: int, result: GlobusSearchResult) -> Self:
        """Instantiate this class from an `ESGSearchQuery`, query time, and `GlobusSearchResult`."""
        constraints = []

        if q.query:
            constraints.append(q.query)
        if q.from_ or q.to:
            lower_bound = q.from_.strftime("%Y-%m-%dT%H:%M:%SZ") if q.from_ else "*"
            upper_bound = q.to.strftime("%Y-%m-%dT%H:%M:%SZ") if q.to else "*"
            constraints.append(f"_timestamp:[{lower_bound} TO {upper_bound}]")
        if q.min_version:
            constraints.append(f"version:[{q.min_version} TO *]")
        if q.max_version:
            constraints.append(f"version:[* TO {q.max_version}]")

        return cls(
            responseHeader=ESGSearchHeader(
                QTime=q_time,
                params=ESGSearchResultParams(
                    q=" AND ".join(constraints) or "*:*",
                    start=q.offset,
                    rows=q.limit,
                    fq=fq_field_from_esg_search_query(q),
                    shards=Url(f"esgf-data-node-solr-query:8983/solr/{q.type.lower()}s"),
                ),
            ),
            response=ESGSearchResult(
                numFound=result.total,
                start=result.offset,
                docs=solr_docs_from_globus_meta_results(result.gmeta),
            ),
            facet_counts=ESGFSearchFacetResult.from_globus_facet_result(result.facet_results),
        )

    responseHeader: ESGSearchHeader
    """Represents the response header for the ESG Search Response."""
    response: ESGSearchResult
    """Represents a search result from ESG Search."""
    facet_counts: ESGFSearchFacetResult = ESGFSearchFacetResult()
    """Represents a facet result from ESG Search."""
