"""Pydantic models used by v1 of the API and its inheritants.

The models in this module are used to define the structure of the API requests and responses.

They are organized into two main sections:
1. **Models for the ESG Search API**
2. **Models for the Globus Search API**

This provides an easy way to validate and serialize the API requests and responses, ensuring that they conform to the specified structure.
"""

from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import (
    Annotated,
    Any,
    Literal,
    Self,
    TypeGuard,
    cast,
    get_args,
)

from annotated_types import T
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
    validate_call,
)
from pydantic_core import Url

from esg_fastapi.api.types import (
    LowerCased,
    MultiValued,
    SolrDoc,
    SolrFQ,
    Stringified,
    SupportedAsFacets,
    SupportedAsFilters,
    SupportedAsFQ,
    SupportedAsSolrDocs,
)
from esg_fastapi.utils import (
    ensure_list,
    format_fq_field,
    one_or_list,
)

NON_QUERIABLE_FIELDS = {"query", "format", "limit", "offset", "replica", "distrib", "facets"}


class ESGSearchQuery(BaseModel):
    """Represents the query parameters accepted by the ESG Search API.

    TODO: Build this list dynamically from Solr's luke API to ensure all possible params are captured.
    """

    model_config = ConfigDict(validate_default=True)

    id: str | None = None
    dataset_id: str | None = None

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
    query: Annotated[str, Query(description="a general search string")] | None = "*:*"
    """A Solr search string."""
    format: Annotated[
        Literal["application/solr+xml", "application/solr+json"],
        Query(description="the type of data returned in the response"),
    ] = "application/solr+xml"
    """The format of the response."""
    type: Annotated[Literal["Dataset", "File", "Aggregation"], Query(description="the type of database record")] = (
        "Dataset"
    )
    """The type of record to search for."""
    bbox: Annotated[str | None, Query(description="the geospatial search box [west, south, east, north]")] = None
    """The geospatial search box [west, south, east, north]"""
    start: Annotated[datetime | None, Query(description="beginning of the temporal coverage in the dataset")] = None
    """Beginning of the temporal coverage in the dataset"""
    end: Annotated[datetime | None, Query(description="ending of the temporal coverage in the dataset")] = None
    """Ending of the temporal coverage in the dataset"""
    _from: Annotated[
        datetime | None, Query(alias="from", description="return records last modified after this timestamp")
    ] = None
    """Return records last modified after this timestamp"""
    to: Annotated[datetime | None, Query(description="return records last modified before this timestamp")] = None
    """Return records last modified before this timestamp"""
    offset: Annotated[int, Query(ge=0, le=9999, description="the number of records to skip")] = 0
    """The number of records to skip. Globus Search allows from 0 to 9999, so we limit it to that range."""
    limit: Annotated[int, Query(ge=0, description="the number of records to return")] = 0
    """The number of records to return"""
    replica: Annotated[bool | None, Query(description="enable to include replicas in the search results")] = None
    """Enable to include replicas in the search results"""
    latest: Annotated[bool | None, Query(description="enable to only return the latest versions")] = None
    """Enable to only return the latest versions"""
    distrib: Annotated[bool | None, Query(description="enable to search across all federated nodes")] = None
    """Enable to search across all federated nodes"""
    facets: Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"\w+(,\w+)*?")] | None = None
    """A comma-separated list of field names to facet on."""

    @classmethod
    def _queriable_fields(cls) -> set[str]:
        """All fields that are queriable in Solr."""
        return {field for field in cls.model_fields if field not in NON_QUERIABLE_FIELDS}


class GlobusFilter(BaseModel):
    """Parent container model for Globus Search Filter Documents.

    TODO: range, geo_bounding_box, exists, not
    ref: https://docs.globus.org/api/search/reference/post_query/#gfilter
    """

    type: Literal["match_all", "match_any"]
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


def is_sequence_of(value: object, value_type: type[T]) -> TypeGuard[Sequence[T]]:
    """Check if a given value is a sequence of a specific type.

    Parameters:
    value (object): The value to be checked.
    value_type (type[T]): The type of the elements in the sequence.

    Returns:
    TypeGuard[Sequence[T]]: A type guard that returns `True` if the given value is a sequence of the specified type, and `False` otherwise.

    Raises:
    TypeError: If the `value_type` parameter is not a type.

    Example:
    ```python
    from typing import List, Dict

    # Check if a list is a sequence of integers
    is_sequence_of([1, 2, 3], int)  # Returns True

    # Check if a dictionary is a sequence of integers
    is_sequence_of({1: 'one', 2: 'two'}, int)  # Returns False
    ```
    """
    return isinstance(value, Sequence) and all(isinstance(i, value_type) for i in value)


class GlobusSearchQuery(BaseModel):
    """Container model to describe the fields of a Globus Search Query Document.

    TODO: boosts and sorts
    """

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

    @field_validator("q")
    @staticmethod
    def convert_esg_seach_q_field_default(value: str | None) -> str | None:
        """Convert the default ESG Search query to the default Globus Search query.

        ESG Search (read: Solr)'s default query is '*:*' for 'all values in all fields'.
        Globus Search doesn't handle this format, so we have to convert it to empty string for 'all.'

        TODO: Globus docs say q is only required if there are no filters: https://docs.globus.org/api/search/reference/post_query/#gsearchrequest
            Once the model can distinguish "queryable" fields from others (like limit, offset, etc),
            set a @model_validator() to set q appropriately where there are/aren't filters.
        """
        return None if value in ("", "*", "*:*") else value

    @field_validator("filters", mode="before")
    @staticmethod
    @validate_call
    def convert_esg_seach_filters_field(value: SupportedAsFilters) -> Sequence[GlobusFilter]:
        """Convert an ESG Search style fields dict to a list of GlobusFilter objects.

        Parameters:
        value (dict | list[GlobusFilter]): The input value to be converted. If it is a dictionary, it should have field
            names as keys and values as lists of strings. If it is a list, it should contain instances of `GlobusFilter`.

        Returns:
        list[GlobusFilter]: A list of `GlobusFilter` objects, each representing a filter condition.

        Raises:
        ValueError: If the input value is neither a dictionary nor a list.

        Note:
        This method is used to convert the filters field in the ESG Search Query into a list of `GlobusFilter` objects.
        It does not perform any actual search operations.
        """
        if is_sequence_of(value, GlobusFilter):
            return value
        elif isinstance(value, dict):
            built_filters = []
            for field, field_value in value.items():
                # This is a serialized model
                if isinstance(field_value, str):
                    # If it's a comma separated string, split it and pass that as the values, otherwise a single-valued list of strings
                    # Set the `type` to `match_any` so match result in the csv
                    built_filters.append(
                        GlobusMatchFilter(type="match_any", field_name=field, values=field_value.split(","))
                    )
                else:
                    # If it's not a string, it Should(TM) already be a list, pass it as a `match_all` filter
                    built_filters.append(GlobusMatchFilter(field_name=field, values=field_value))
            return built_filters
        else:
            raise ValueError(  # pragma: no cover TODO: pytest.raises() masks this line so coverage doesn't think it was executed
                f"Expected input convertible to list[GlobusFilter] one of {get_args(SupportedAsFilters)}, got {type(value)}"
            )

    @classmethod
    def from_esg_search_query(cls, query: ESGSearchQuery) -> Self:
        """Create a new instance of `GlobusSearchResult` from an `ESGSearchQuery`.

        Parameters:
        query (ESGSearchQuery): The `ESGSearchQuery` instance to use for creating the new instance.

        Returns:
        GlobusSearchResult: A new instance of `GlobusSearchResult` created from the provided `ESGSearchQuery`.

        Raises:
        ValueError: If the `query` instance is not valid.

        Note:
        This method converts the `query` instance into a `GlobusSearchResult` instance by extracting the relevant fields and parameters. It does not perform any actual search operations.
        """
        return cls(
            q=query.query,
            advanced=True,
            limit=query.limit,
            offset=query.offset,
            filters=query.model_dump(exclude_none=True, include=query._queriable_fields()),
            facets=query.facets,
        )

    version_: Literal["query#1.0.0"] = Field(default="query#1.0.0", alias="@version")
    """The version of the query format."""
    q: str | None = None
    """The search query."""
    advanced: bool = True
    """Whether or not to use advanced search."""
    limit: int
    """The maximum number of results to return."""
    offset: int
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
    """Represents a bucket in a Globus Search result.

    Attributes:
        value (str | dict[Literal["from", "to"], Any]): The value of the bucket.
        count (int): The count of items in the bucket.
    """

    value: str | dict[Literal["from", "to"], Any]
    """The value of the bucket."""
    count: int
    """The count of items in the bucket."""


class GlobusFacetResult(BaseModel):
    """Represents a bucket in a Globus Search result.

    Attributes:
        name (str): The name of the facet.
        value (float): The value of the facet.
        buckets (list[GlobusBucket]]): A list of buckets associated with the facet.
    """

    name: str
    """The name of the facet."""

    value: float | None = None
    """The value of the facet.

    TODO: The docs aren't super clear that GFacetResult.value is only returned if the facet query was
          a sum or avg facet. We need to determine if ESG Search supports these types and thus
          whether we need to implement them.
          ref: https://docs.globus.org/api/search/reference/post_query/#gfacetresult
    """

    buckets: list[GlobusBucket]
    """A list of buckets associated with the facet."""


class GlobusSearchResult(BaseModel):
    """Represents a search result from the Globus platform.

    Ref: https://docs.globus.org/api/search/reference/post_query/#gsearchresult

    Attributes:
        gmeta (list[GlobusMetaResult]]): A list of metadata entries for the search result.
        facet_results (list[GlobusFacetResult]] | None = None): A list of facet results for the search result.
        offset (int): The offset of the search result.
        count (int): The count of items in the search result.
        total (int): The total number of items in the search result.
        has_next_page (bool): A flag indicating whether there is a next page of search results.
        datatype (Literal["GSearchResult"]): The data type of the search result.
        version (Literal["2017-09-01"]): The version of the search result.
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

    ### WARNING: these attributes are shown in the examples of the Globus SDK
    # docs (https://docs.globus.org/api/search/reference/post_query/#examples_10)
    # but are not documented as part of the "spec" (such as it is...)
    # They do not appear to return from SearchClient().post_query() so commenting them out for now.
    # datatype: Literal["GSearchResult"] = Field(alias="@datatype")
    """
    A string literal representing the data type of the search result. Its value is always `"GSearchResult"`.
    """

    # version: Literal["2017-09-01"] = Field(alias="@version")
    """
    A string literal representing the version of the search result. Its value is always `"2017-09-01"`.
    """


class ESGSearchResultParams(BaseModel):
    """Parameters for the ESG Search Result.

    Attributes:
        facet_field (None | list[str]): The field to use for faceting.
        df (str): The default field to use for searching.
        q_alt (str): The alternative query string.
        indent (str): A boolean flag indicating whether to indent the JSON response.
        echoParams (str): A boolean flag indicating whether to echo the parameters in the response.
        fl (str): A comma-separated list of fields to include in the response.
        start (Decimal): The starting index for the search results.
        fq (SolrFQ): The list of Solr Facet Queries.
        rows (Decimal): The maximum number of search results to return.
        q (str): The query string to use for searching.
        shards (Url): The URL of the Solr shards to use for searching.
        tie (Decimal): The tie-breaking parameter for Solr faceting.
        facet_limit (Decimal): The maximum number of facet values to return.
        qf (str): The query field to use for searching.
        facet_method (str): The method to use for faceting.
        facet_mincount (Stringified[int]): The minimum count required for a facet value to be included in the response.
        facet (LowerCased[Stringified[bool]]): A boolean flag indicating whether to include facet values in the response.
        wt (Literal["json", "xml"]): The format of the response.
        facet_sort (str): The sorting method to use for facet values.
    """

    model_config = ConfigDict(validate_default=True)

    @field_validator("fq", mode="before")
    @staticmethod
    def convert_and_validate_fq(value: SupportedAsFQ) -> SolrFQ:
        """Convert and validate the input for the `fq` field.

        Parameters:
        input (SupportedAsFQ): The input value to be converted and validated.

        Returns:
        SolrFQ: A SolrFQ object representing the list of Solr Facet Queries.

        Raises:
        ValueError: If the input value is not a list of Solr Facet Queries, or if it is not convertible to a SolrFQ object.

        Note:
        - If the input value is a string, it is split into a list of strings and then validated.
        - If the input value is a list of strings, it is validated as a SolrFQ object.
        - If the input value is an instance of `ESGSearchQuery`, it is converted to a SolrFQ object by first converting the queryable fields of the query into a list of strings, and then validating the resulting list.
        """
        if isinstance(value, str):
            value = [atom.strip() for atom in value.split(",")]
        if is_sequence_of(value, str):
            return one_or_list(value)
        elif isinstance(value, ESGSearchQuery):
            fq_fields = value.model_dump(exclude_none=True, include=value._queriable_fields())
            return one_or_list([format_fq_field(field) for field in fq_fields.items()])
        else:
            raise ValueError(  # pragma: no cover TODO: pytest.raises() masks this line so coverage doesn't think it was executed
                f"Expected input convertible to SolrFQ one of {get_args(SupportedAsFQ)}, got {type(value)}"
            )

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
    indent: LowerCased[Stringified[bool]] = True
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
    start: Decimal
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

    rows: Decimal = cast("Decimal", 10)
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
    tie: Decimal = cast("Decimal", 0.01)
    """
    The `tie` attribute is a float representing the tie-breaking parameter for Solr faceting. Its default value is `0.01`.
    """
    facet_limit: Decimal = Field(alias="facet.limit", default=cast("Decimal", -1))
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
    facet_mincount: Decimal = Field(alias="facet.mincount", default=cast("Decimal", 1))
    """
    The `facet_mincount` attribute is an integer representing the minimum count required for a facet value to be included in the response. Its default value is `1`.
    """
    facet: LowerCased[Stringified[bool]] = True
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

    @field_validator("docs", mode="before")
    @staticmethod
    def convert_to_docs(value: SupportedAsSolrDocs) -> Sequence[SolrDoc]:
        """Convert a list of GlobusMetaResults to a list of Solr docs."""
        if is_sequence_of(value, dict):
            return value
        elif is_sequence_of(value, GlobusMetaResult):
            # Globus Search doesn't return score, so fake it for consistency
            return [{**record.entries[0].content | {"id": record.subject, "score": 0.5}} for record in value]
        else:
            raise ValueError(  # pragma: no cover TODO: pytest.raises() masks this line so coverage doesn't think it was executed
                f"Expected input convertible to SolrDoc one of {get_args(SupportedAsSolrDocs)}, got {type(value)}"
            )

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
    facet_fields: dict[str, tuple[str | int, ...]] = {}
    """Facet fields for the facet result."""
    facet_ranges: dict = {}
    """Facet ranges for the facet result."""
    facet_intervals: dict = {}
    """Facet intervals for the facet result."""
    facet_heatmaps: dict = {}
    """Facet heatmaps for the facet result."""


class ESGSearchResponse(BaseModel):
    """Represents a response from ESG Search."""

    @field_validator("facet_counts", mode="before")
    @staticmethod
    def convert_to_esg_search_facet_counts(value: SupportedAsFacets) -> ESGFSearchFacetResult:
        """Convert a list of GlobusFacetResults to a list of ESGSearchFacetCounts.

        Parameters:
        value (list[dict[str, Any]] | list[GlobusFacetResult] | None): The input value to be converted.

        Returns:
        ESGFSearchFacetResult: A list of ESGSearchFacetCounts.

        Raises:
        ValueError: If the input value is not a list of GlobusFacetResults.

        Note:
        - If the input value is `None`, an empty ESGSearchFacetResult object is returned.
        - If the input value is a list of dictionaries, it is assumed that the list represents a list of facet results from Globus Search.
        """
        if isinstance(value, dict):
            return ESGFSearchFacetResult.model_validate(value)
        if isinstance(value, ESGFSearchFacetResult):
            return value
        if is_sequence_of(value, GlobusFacetResult):
            facet_fields = defaultdict(list)
            for facet in value:
                facet_fields[facet.name].extend(
                    [attr for bucket in facet.buckets for attr in (bucket.value, bucket.count)]
                )
            return ESGFSearchFacetResult.model_validate({"facet_fields": facet_fields})
        if value is None:
            # Globus facet_results can be `None` if there are no facets, but ESG Search
            # returns empty dicts if there are no facets.
            return ESGFSearchFacetResult()
        raise ValueError(
            f"Expected input convertible to ESGFSearchFacetResult one of {get_args(SupportedAsFacets)}, got {type(value)}"
        )

    responseHeader: ESGSearchHeader
    """Represents the response header for the ESG Search Response."""
    response: ESGSearchResult
    """Represents a search result from ESG Search."""
    facet_counts: ESGFSearchFacetResult = ESGFSearchFacetResult()
    """Represents a facet result from ESG Search."""
