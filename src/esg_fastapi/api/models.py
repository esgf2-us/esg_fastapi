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
from pydantic.json_schema import SkipJsonSchema
from pydantic_core import PydanticUndefined, Url

from esg_fastapi.api.types import (
    ESGSearchFacetField,
    LowerCased,
    MultiValued,
    OptionalParam,
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

    query: OptionalParam[str] = None
    """A Solr search string."""
    format: Literal["application/solr+xml", "application/solr+json"] = "application/solr+json"
    """The format of the response."""
    bbox: OptionalParam[str] = None
    """The geospatial search box [west, south, east, north]"""
    offset: OptionalParam[int] = Query(0, ge=0, le=9999)
    """The number of records to skip. Globus Search only allows from 0 to 9999, so we limit it to that range."""
    limit: OptionalParam[int] =  Query(10, ge=0)
    """The number of records to return"""
    replica: OptionalParam[bool] = None
    """Enable to include replicas in the search results"""
    distrib: OptionalParam[bool] = None
    """Enable to search across all federated nodes"""
    facets: OptionalParam[Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"\w+(,\w+)*?")]] = None
    """A comma-separated list of field names to facet on."""

    min_version: OptionalParam[int] = None
    """Constrain query results to `version` field after this date."""
    max_version: OptionalParam[int] = None
    """Constrain query results to `version` field before this date."""

    from_: OptionalParam[datetime] = Query(None, alias="from")
    """Return records last modified after this timestamp"""
    to: OptionalParam[datetime] = None
    """Return records last modified before this timestamp"""


class ESGSearchQuery(ESGSearchQueryBase):
    """Represents the query parameters accepted by the ESGF Search API.

    These fields are used to filter and retrieve climate model output and observational data from various PCMDI projects like CMIP5,
    CMIP6, and Obs4MIPs. The structure builds upon earlier efforts like CMIP3, which demonstrated the value of structured and uniform
    archiving. <sup>1</sup>

    <small><sup>1</sup>: [IPCC Standard Output Requirements](https://pcmdi.github.io/ipcc/IPCC_output_requirements.htm),
    Overview</small>
    """

    id: OptionalParam[str] = Query(
        None,
        title="Record ID",
        description="Unique identifier for a dataset or file record in the ESGF archive. This can be a `dataset_id` or a `file ID`. "
        "<sup>1</sup><br><br><small><sup>1</sup>: [ESGF Search Documentation](https://esgf-node.llnl.gov/esgf_docs/search_api.html)</small>",
        openapi_examples={
            "CMIP5 Example": {
                "summary": "CMIP5 Record ID",
                "description": "An example of a CMIP5 dataset ID.",
                "value": "cmip5.output1.BCC.bcc-csm1-1.historical.mon.atmos.Amon.r1i1p1.tas.20120709",
            },
            "CMIP6 Example": {
                "summary": "CMIP6 Record ID",
                "description": "An example of a CMIP6 file ID.",
                "value": "CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.tas.gr.v20190801"
                ".tas_Amon_IPSL-CM6A-LR_historical_r1i1p1f1_gr_185001-201412.nc",
            },
            "obs4MIPs Example": {
                "summary": "obs4MIPs Record ID",
                "description": "An example of an obs4MIPs dataset ID.",
                "value": "obs4MIPs.NASA-GSFC.GPCP-Monthly-3-2.mon.pr.gn.v20231205|esgf-data2.llnl.gov",
            },
        },
    )
    dataset_id: OptionalParam[str] = Query(
        None,
        title="Dataset ID",
        description=(
            "Unique identifier for a publication-level dataset. In CMIP5, it followed the pattern `activity.product.institute.model."
            "experiment.frequency.modeling realm.MIP table.ensemble member` <sup>1</sup>. For CMIP6, it's part of the directory "
            "structure and includes version information <sup>2</sup>. For Obs4MIPs, it's derived from `source_label` and "
            "`source_version_number` <sup>3</sup>.<br><br>"
            "<small><sup>1</sup>: [CMIP5 Data Reference Syntax (DRS)]"
            "(https://pcmdi.llnl.gov/mips/cmip5/docs/cmip5_data_reference_syntax.pdf), Section 3.4</small><br>"
            "<small><sup>2</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Section 'Directory structure template'</small><br>"
            "<small><sup>3</sup>: [Obs4MIPs Data Specifications 2.5 (ODS2.5)](https://doi.org/10.5281/zenodo.11500474), "
            "Appendix 2</small>"
        ),
        openapi_examples={
            "CMIP5 Example": {
                "summary": "CMIP5 Dataset ID",
                "description": "An example of a CMIP5 dataset ID.",
                "value": "cmip5.output1.BCC.bcc-csm1-1.historical.mon.atmos.Amon.r1i1p1",
            },
            "CMIP6 Example": {
                "summary": "CMIP6 Dataset ID",
                "description": "An example of a CMIP6 dataset ID.",
                "value": "CMIP6.CMIP.IPSL.IPSL-CM6A-LR.historical.r1i1p1f1.Amon.tas.gr.v20190801",
            },
            "Obs4MIPs Example": {
                "summary": "Obs4MIPs Dataset ID",
                "description": "An example of an Obs4MIPs dataset ID.",
                "value": "obs4MIPs.NASA-GSFC.IMERG-v06B-Final.3hr.pr.2x2.v20210812",
            },
        },
    )
    type: Literal["Dataset", "File"] = Query(
        "Dataset",
        title="Record Type",
        description="The `type` of record to search for: `Dataset` for publication-level datasets or `File` for individual data files. "
        "<sup>1</sup><br><br><small><sup>1</sup>: [ESGF Search Documentation](https://esgf-node.llnl.gov/esgf_docs/search_api.html)</small>",
        openapi_examples={
            "Dataset Type": {"summary": "Search for Datasets", "description": "Retrieve publication-level datasets.", "value": "Dataset"},
            "File Type": {"summary": "Search for Files", "description": "Retrieve individual data files.", "value": "File"},
        },
    )
    access: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Access Protocols",
        description=(
            "The data access `protocols` available for retrieving the dataset's files, such as through a direct HTTP download, "
            "OPeNDAP, or Globus. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [ESGF Search Documentation](https://esgf-node.llnl.gov/esgf_docs/search_api.html)</small>"
        ),
        openapi_examples={
            "HTTPServer": {"summary": "HTTPServer", "description": "Datasets available via direct HTTP download.", "value": "HTTPServer"},
            "Globus": {"summary": "Globus", "description": "Datasets available via Globus file transfer.", "value": "Globus"},
            "OPENDAP": {"summary": "OPeNDAP", "description": "Datasets available via OPeNDAP.", "value": "OPENDAP"},
            "GridFTP": {"summary": "GridFTP", "description": "Datasets available via GridFTP.", "value": "GridFTP"},
        },
    )
    activity: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Activity (CMIP5)",
        description=(
            "Identifies the model intercomparison `activity`. For CMIP5, this was the primary identifier for the project (e.g., `CMIP5`, "
            "`TAMIP`, `CFMIP`, `PMIP`) <sup>1</sup>. In CMIP6, this role is largely taken over by `activity_id` and `mip_era`.<br><br>"
            "<small><sup>1</sup>: [CMIP5 Data Reference Syntax (DRS)]"
            "(https://pcmdi.llnl.gov/mips/cmip5/docs/cmip5_data_reference_syntax.pdf), Section 2.3</small>"
        ),
        openapi_examples={
            "CMIP5": {"summary": "CMIP5", "description": "Data from CMIP5 activity.", "value": "CMIP5"},
            "TAMIP": {"summary": "TAMIP", "description": "Data from TAMIP activity.", "value": "TAMIP"},
            "CFMIP": {"summary": "CFMIP", "description": "Data from CFMIP activity.", "value": "CFMIP"},
            "PMIP": {"summary": "PMIP", "description": "Data from PMIP activity.", "value": "PMIP"},
        },
    )
    activity_drs: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Activity DRS (CMIP6)",
        description="`Activity` identifier as used in the CMIP6 Data Reference Syntax (DRS) for constructing file paths and IDs. <sup>1</sup>"
        "<br><br><small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
        "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf)</small>",
        openapi_examples={
            "DCPP": {"summary": "DCPP", "description": "Activity identifier for DCPP.", "value": "DCPP"},
            "PAMIP": {"summary": "PAMIP", "description": "Activity identifier for PAMIP.", "value": "PAMIP"},
            "ScenarioMIP": {"summary": "ScenarioMIP", "description": "Activity identifier for ScenarioMIP.", "value": "ScenarioMIP"},
        },
    )
    activity_id: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Activity ID (CMIP6, Obs4MIPs)",
        description=(
            "Identifies the specific `activity` or MIP associated with the dataset (e.g., `CMIP`, `PMIP`, `DCPP`, `obs4MIPs`). It "
            "replaces the broader `activity` field from CMIP5 and can be a space-separated list in CMIP6 <sup>1, 2</sup>.<br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1, Note 3</small><br>"
            "<small><sup>2</sup>: [Obs4MIPs Data Specifications 2.5 (ODS2.5)](https://doi.org/10.5281/zenodo.11500474), Table 1</small>"
        ),
        openapi_examples={
            "DCPP": {"summary": "DCPP Activity", "description": "Data for DCPP activity.", "value": "DCPP"},
            "PAMIP": {"summary": "PAMIP Activity", "description": "Data for PAMIP activity.", "value": "PAMIP"},
            "ScenarioMIP": {"summary": "ScenarioMIP Activity", "description": "Data for ScenarioMIP activity.", "value": "ScenarioMIP"},
            "CMIP": {"summary": "CMIP Activity", "description": "Data for CMIP activity.", "value": "CMIP"},
        },
    )
    atmos_grid_resolution: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Atmospheric Grid Resolution",
        description=(
            "Describes the resolution of the `atmospheric grid` in model output. Often a free-form string (e.g., `100km`). <sup>1</sup>"
            "<br><br><small><sup>1</sup>: [CMIP5 Model Output Requirements]"
            "(https://pcmdi.llnl.gov/mips/cmip5/CMIP5_output_metadata_requirements.pdf), "
            "Section 'Requirements for output variables' examples</small>"
        ),
        openapi_examples={"100km": {"summary": "100km Grid", "description": "Atmospheric grid resolution 100km.", "value": "100km"}},
    )
    branch_method: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Branching Method (CMIP6)",
        description=(
            "Procedure used to `branch` a simulation. In CMIP6, this can include details about spin-ups or other non-standard "
            "procedures. If no parent, it can be omitted or `no parent` <sup>1</sup>.<br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1, Note 4</small>"
        ),
        openapi_examples={
            "Standard": {"summary": "Standard", "description": "Standard branching method.", "value": "standard"},
            "No Parent": {"summary": "No Parent", "description": "Simulation without a parent run.", "value": "no parent"},
        },
    )
    campaign: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Campaign (Obs4MIPs)",
        description="Identifies the observational `campaign` or project the data belongs to within Obs4MIPs. <sup>1</sup><br><br>"
        "<small><sup>1</sup>: [Obs4MIPs Data Specifications 2.5 (ODS2.5)](https://doi.org/10.5281/zenodo.11500474)</small>",
        openapi_examples={
            "Satellite": {"summary": "Satellite Campaign", "description": "Data from a satellite campaign.", "value": "satellite_campaign"},
            "Ground-based": {
                "summary": "Ground-based Campaign",
                "description": "Data from a ground-based campaign.",
                "value": "ground_based",
            },
        },
    )
    Campaign: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Campaign (Alternative)",
        description="Alternative capitalization for the `Campaign` field to identify the observational `campaign` or project within "
        "Obs4MIPs. <sup>1</sup><br><br><small><sup>1</sup>: [Obs4MIPs Data Specifications 2.5 (ODS2.5)]"
        "(https://doi.org/10.5281/zenodo.11500474)</small>",
        openapi_examples={
            "Satellite (Alt)": {
                "summary": "Satellite (Alt)",
                "description": "Satellite campaign (alt capitalization).",
                "value": "SATELLITE",
            },
            "Ground (Alt)": {"summary": "Ground (Alt)", "description": "Ground-based campaign (alt capitalization).", "value": "GROUND"},
        },
    )
    catalog_version: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Catalog Version",
        description="The `version` of the data catalog from which the dataset originated. <sup>1</sup><br><br><small><sup>1</sup>: "
        "[ESGF Search Documentation](https://esgf-node.llnl.gov/esgf_docs/search_api.html)</small>",
        openapi_examples={
            "v1.0": {"summary": "Catalog Version 1.0", "description": "Data from catalog version 1.0.", "value": "1.0"},
            "v2.1": {"summary": "Catalog Version 2.1", "description": "Data from catalog version 2.1.", "value": "2.1"},
        },
    )
    cf_standard_name: OptionalParam[MultiValued[str]] = Query(
        None,
        title="CF Standard Name",
        description=(
            "The Climate and Forecast (CF) convention `standard name` for the variable, providing a unique and unambiguous "
            "identification of the physical quantity. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP5 Model Output Requirements]"
            "(https://pcmdi.llnl.gov/mips/cmip5/CMIP5_output_metadata_requirements.pdf), Section 'Required attributes for variables'</small>"
        ),
        openapi_examples={
            "Air Temp": {"summary": "Air Temperature", "description": "CF standard name for air temperature.", "value": "air_temperature"},
            "Precip Flux": {
                "summary": "Precipitation Flux",
                "description": "CF standard name for precipitation.",
                "value": "precipitation_flux",
            },
            "East Wind": {"summary": "Eastward Wind", "description": "CF standard name for eastward wind.", "value": "eastward_wind"},
        },
    )
    cmor_table: OptionalParam[MultiValued[str]] = Query(
        None,
        title="CMOR Table (CMIP5)",
        description=(
            "In CMIP5, identified the CMOR `table` defining variable properties, often implying frequency and realm (e.g., `Amon`, `Omon`) "
            "<sup>1</sup>. In CMIP6, this is `table_id`.<br><br>"
            "<small><sup>1</sup>: [CMIP5 Data Reference Syntax (DRS)]"
            "(https://pcmdi.llnl.gov/mips/cmip5/docs/cmip5_data_reference_syntax.pdf), Section 2.3</small>"
        ),
        openapi_examples={
            "day": {"summary": "day Table", "description": "CMOR table day.", "value": "day"},
            "Amon": {"summary": "Amon Table", "description": "CMOR table Amon.", "value": "Amon"},
            "Omon": {"summary": "Omon Table", "description": "CMOR table Omon.", "value": "Omon"},
            "LImon": {"summary": "LImon Table", "description": "CMOR table LImon.", "value": "LImon"},
        },
    )
    contact: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Contact Information",
        description=(
            "`Contact` information for the data provider. Required in CMIP5 <sup>1</sup>, but optional in CMIP6 (use `further_info_url`) "
            "<sup>2</sup>. Still required in Obs4MIPs <sup>3</sup>.<br><br>"
            "<small><sup>1</sup>: [CMIP5 Model Output Requirements]"
            "(https://pcmdi.llnl.gov/mips/cmip5/CMIP5_output_metadata_requirements.pdf), Section 'Required global attributes'</small><br>"
            "<small><sup>2</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small><br>"
            "<small><sup>3</sup>: [Obs4MIPs Data Specifications 2.5 (ODS2.5)](https://doi.org/10.5281/zenodo.11500474), Table 1</small>"
        ),
        openapi_examples={
            "Meinshausen": {
                "summary": "Malte Meinshausen",
                "description": "Contact email for Malte Meinshausen.",
                "value": "malte.meinshausen@unimelb.edu.au",
            },
            "Smith": {"summary": "Steven J. Smith", "description": "Contact email for Steven J. Smith.", "value": "ssmith@pnnl.gov"},
        },
    )
    Conventions: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Conventions",
        description=(
            "Metadata `conventions` adhered to. In CMIP5, `CF-1.4` was typical <sup>1</sup>. In CMIP6/Obs4MIPs, this can be a list like "
            "`CF-1.7 CMIP-6.2` or `CF-1.11 ODS-2.5` <sup>2, 3</sup>. For CMIP3, `CF-1.0` was specified <sup>4</sup>.<br><br>"
            "<small><sup>1</sup>: [CMIP5 Model Output Requirements]"
            "(https://pcmdi.llnl.gov/mips/cmip5/CMIP5_output_metadata_requirements.pdf), Section 'Required global attributes'</small><br>"
            "<small><sup>2</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small><br>"
            "<small><sup>3</sup>: [Obs4MIPs Data Specifications 2.5 (ODS2.5)](https://doi.org/10.5281/zenodo.11500474), Table 1</small><br>"
            "<small><sup>4</sup>: [IPCC Standard Output Requirements](https://pcmdi.github.io/ipcc/IPCC_output_requirements.htm), "
            "Section 'Recommended attributes'</small>"
        ),
        openapi_examples={
            "CF-1.6": {"summary": "CF-1.6", "description": "Climate and Forecast Convention v1.6.", "value": "CF-1.6"},
            "CF-1.7": {"summary": "CF-1.7", "description": "Climate and Forecast Convention v1.7.", "value": "CF-1.7"},
            "CMIP6": {"summary": "CMIP6 Conventions", "description": "CMIP6 specific conventions.", "value": "CF-1.7 CMIP-6.2"},
        },
    )
    creation_date: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Creation Date",
        description=(
            "The `date and time` of file creation, in ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`). Consistent across CMIP5 <sup>1</sup>, "
            "CMIP6 <sup>2</sup>, and Obs4MIPs <sup>3</sup>.<br><br>"
            "<small><sup>1</sup>: [CMIP5 Model Output Requirements]"
            "(https://pcmdi.llnl.gov/mips/cmip5/CMIP5_output_metadata_requirements.pdf), Section 'Required global attributes'</small><br>"
            "<small><sup>2</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small><br>"
            "<small><sup>3</sup>: [Obs4MIPs Data Specifications 2.5 (ODS2.5)](https://doi.org/10.5281/zenodo.11500474), Table 1</small>"
        ),
        openapi_examples={
            "2019-09-17": {"summary": "2019-09-17", "description": "Example creation date.", "value": "2019-09-17T11:15:28Z"},
            "2019-09-24": {"summary": "2019-09-24", "description": "A more recent example date.", "value": "2019-09-24T18:33:44Z"},
        },
    )
    data_node: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Data Node",
        description="The ESGF `data node` where the dataset is hosted. <sup>1</sup><br><br><small><sup>1</sup>: [ESGF Search Documentation]"
        "(https://esgf-node.llnl.gov/esgf_docs/search_api.html)</small>",
        openapi_examples={
            "ORNL": {"summary": "ORNL Data Node", "description": "ESGF data node at ORNL.", "value": "esgf-node.ornl.gov"},
            "ALCF": {"summary": "ALCF Data Node", "description": "ESGF data node at ALCF.", "value": "eagle.alcf.anl.gov"},
            "LLNL": {"summary": "LLNL Data Node", "description": "ESGF data node at LLNL.", "value": "esgf-data1.llnl.gov"},
        },
    )
    data_specs_version: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Data Specifications Version (CMIP6, Obs4MIPs)",
        description=(
            "Records the `version` of the data request/specifications. Used in CMIP6 (e.g., `01.00.00`) <sup>1</sup> and Obs4MIPs "
            "(e.g., `ODS-2.5`) <sup>2</sup>.<br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small><br>"
            "<small><sup>2</sup>: [Obs4MIPs Data Specifications 2.5 (ODS2.5)](https://doi.org/10.5281/zenodo.11500474), Table 1</small>"
        ),
        openapi_examples={
            "v01.00.31": {"summary": "Version 01.00.31", "description": "Data specs version 01.00.31.", "value": "01.00.31"},
            "v01.00.28": {"summary": "Version 01.00.28", "description": "Data specs version 01.00.28.", "value": "01.00.28"},
            "v01.00.29": {"summary": "Version 01.00.29", "description": "Data specs version 01.00.29.", "value": "01.00.29"},
        },
    )
    data_structure: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Data Structure",
        description=(
            "Describes the internal `structure` or organization of the data within files. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP5 Model Output Requirements]"
            "(https://pcmdi.llnl.gov/mips/cmip5/CMIP5_output_metadata_requirements.pdf), "
            "Section 'Data format, data structure, and file content requirements'</small>"
        ),
        openapi_examples={"Grid": {"summary": "Grid", "description": "Data structured as a grid.", "value": "grid"}},
    )
    data_type: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Data Type",
        description=(
            "Specifies the `type` of data, such as `model-output`. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP5 Model Output Requirements]"
            "(https://pcmdi.llnl.gov/mips/cmip5/CMIP5_output_metadata_requirements.pdf), "
            "Section 'Requirements for output variables'</small>"
        ),
        openapi_examples={
            "Model Output": {"summary": "Model Output", "description": "Data type is model-output.", "value": "model-output"}
        },
    )
    dataset_category: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Dataset Category",
        description="Categorization of the dataset, e.g., `GHGConcentrations`, `emissions`. <sup>1</sup><br><br><small><sup>1</sup>: "
        "[ESGF Search Documentation](https://esgf-node.llnl.gov/esgf_docs/search_api.html)</small>",
        openapi_examples={
            "GHG": {"summary": "GHGConcentrations", "description": "Dataset category: GHGConcentrations.", "value": "GHGConcentrations"},
            "Emissions": {"summary": "Emissions", "description": "Dataset category: emissions.", "value": "emissions"},
        },
    )
    dataset_status: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Dataset Status",
        description="Indicates the current `status` of the dataset, such as `latest`, `deprecated`. <sup>1</sup><br><br><small><sup>1</sup>: "
        "[ESGF Search Documentation](https://esgf-node.llnl.gov/esgf_docs/search_api.html)</small>",
        openapi_examples={
            "Latest": {"summary": "Latest", "description": "Dataset status: latest.", "value": "latest"},
            "Deprecated": {"summary": "Deprecated", "description": "Dataset status: deprecated.", "value": "deprecated"},
        },
    )
    dataset_version: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Dataset Version",
        description=(
            "The `version` of the dataset. In CMIP5, this was often `vN` <sup>1</sup>. In CMIP6 and Obs4MIPs, this is typically "
            "`vYYYYMMDD` <sup>2, 3</sup>.<br><br>"
            "<small><sup>1</sup>: [CMIP5 Data Reference Syntax (DRS)]"
            "(https://pcmdi.llnl.gov/mips/cmip5/docs/cmip5_data_reference_syntax.pdf), Section 2.3</small><br>"
            "<small><sup>2</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(httpshttps://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Section 'Directory structure template'</small><br>"
            "<small><sup>3</sup>: [Obs4MIPs Data Specifications 2.5 (ODS2.5)](https://doi.org/10.5281/zenodo.11500474), "
            "Section 'Directory structure template' notes</small>"
        ),
        openapi_examples={"v1": {"summary": "Version 1", "description": "Dataset version 1.", "value": "1"}},
    )
    dataset_version_number: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Dataset Version Number",
        description="A numerical representation of the dataset's `version`. <sup>1</sup><br><br><small><sup>1</sup>: [ESGF Search "
        "Documentation](https://esgf-node.llnl.gov/esgf_docs/search_api.html)</small>",
        openapi_examples={"v1": {"summary": "Version 1 (Numeric)", "description": "Numerical dataset version 1.", "value": "1"}},
    )
    datetime_end: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Temporal Coverage End Date",
        description="The `end date` of the temporal coverage of the data, used for time-based filtering. <sup>1</sup><br><br>"
        "<small><sup>1</sup>: [ESGF Search Documentation](https://esgf-node.llnl.gov/esgf_docs/search_api.html)</small>",
        openapi_examples={
            "End 2001": {"summary": "End of 2001", "description": "Temporal coverage ends on 2001-05-16.", "value": "2001-05-16T12:00:00Z"},
            "End 2000": {
                "summary": "Start of 2000",
                "description": "Temporal coverage ends on 2000-01-17.",
                "value": "2000-01-17T12:00:00Z",
            },
        },
    )
    deprecated: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Deprecated Status",
        description=(
            "Indicates if the dataset is `deprecated`. <sup>1</sup> This is also implicit in the Obs4MIPs versioning system <sup>2</sup>."
            "<br><br><small><sup>1</sup>: [ESGF Search Documentation](https://esgf-node.llnl.gov/esgf_docs/search_api.html)</small><br>"
            "<small><sup>2</sup>: [Obs4MIPs Data Specifications 2.5 (ODS2.5)](https://doi.org/10.5281/zenodo.11500474), "
            "Appendix 2 Note</small>"
        ),
        openapi_examples={
            "True": {"summary": "Is Deprecated", "description": "Dataset is deprecated.", "value": "true"},
            "False": {"summary": "Not Deprecated", "description": "Dataset is not deprecated.", "value": "false"},
        },
    )
    directory_format_template_: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Directory Format Template",
        description=(
            "The `template string` used to construct the directory path for the dataset in the archive. <sup>1, 2, 3</sup>.<br><br>"
            "<small><sup>1</sup>: [CMIP5 Data Reference Syntax (DRS)]"
            "(https://pcmdi.llnl.gov/mips/cmip5/docs/cmip5_data_reference_syntax.pdf), Section 3.2</small><br>"
            "<small><sup>2</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Section 'Directory structure template'</small><br>"
            "<small><sup>3</sup>: [Obs4MIPs Data Specifications 2.5 (ODS2.5)](https://doi.org/10.5281/zenodo.11500474), "
            "Section 'Directory structure template'</small>"
        ),
        openapi_examples={
            "CMIP6": {
                "summary": "CMIP6 Template",
                "description": "Directory format template for CMIP6.",
                "value": "%(root)s/%(mip_era)s/%(activity_drs)s/%(institution_id)s/%(source_id)s/%(experiment_id)s/%(member_id)s"
                "/%(table_id)s/%(variable_id)s/%(grid_label)s/%(version)s",
            },
            "input4MIPs": {
                "summary": "input4MIPs Template",
                "description": "Directory format template for input4MIPs.",
                "value": "%(root)s/%(activity_id)s/%(mip_era)s/%(target_mip)s/%(institution_id)s/%(source_id)s/%(realm)s"
                "/%(frequency)s/%(variable_id)s/%(grid_label)s/%(version)s",
            },
        },
    )
    ensemble: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Ensemble (CMIP5)",
        description=(
            "In CMIP5, distinguished simulations via `r<N>i<M>p<L>` format <sup>1</sup>. In CMIP6, this is broken down into "
            "`realization_index`, `initialization_index`, `physics_index`, `forcing_index`, which form `variant_label`.<br><br>"
            "<small><sup>1</sup>: [CMIP5 Data Reference Syntax (DRS)]"
            "(https://pcmdi.llnl.gov/mips/cmip5/docs/cmip5_data_reference_syntax.pdf), Section 2.3</small>"
        ),
        openapi_examples={
            "r1i1p1": {"summary": "Ensemble r1i1p1", "description": "Ensemble member r1i1p1.", "value": "r1i1p1"},
            "r2i1p1": {"summary": "Ensemble r2i1p1", "description": "Ensemble member r2i1p1.", "value": "r2i1p1"},
            "r3i1p1": {"summary": "Ensemble r3i1p1", "description": "Ensemble member r3i1p1.", "value": "r3i1p1"},
        },
    )
    ensemble_member: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Ensemble Member (CMIP5)",
        description=(
            "In CMIP5, the `r<N>i<M>p<L>` triad distinguishing simulations <sup>1</sup>. This is `variant_label` in CMIP6 and Obs4MIPs."
            "<br><br><small><sup>1</sup>: [CMIP5 Data Reference Syntax (DRS)]"
            "(https://pcmdi.llnl.gov/mips/cmip5/docs/cmip5_data_reference_syntax.pdf), Section 2.3</small>"
        ),
        openapi_examples={
            "r1i1p1": {"summary": "CMIP5 Ensemble r1i1p1", "description": "Ensemble member r1i1p1 for CMIP5.", "value": "r1i1p1"},
            "r2i1p1": {"summary": "CMIP5 Ensemble r2i1p1", "description": "Ensemble member r2i1p1 for CMIP5.", "value": "r2i1p1"},
        },
    )
    ensemble_member_: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Ensemble Member (CMIP5 Alternative)",
        description=(
            "Alternative for `ensemble_member` from CMIP5, the `r<N>i<M>p<L>` triad distinguishing simulations. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP5 Data Reference Syntax (DRS)]"
            "(https://pcmdi.llnl.gov/mips/cmip5/docs/cmip5_data_reference_syntax.pdf), Section 2.3</small>"
        ),
        openapi_examples={
            "r1i1p1 (Alt)": {"summary": "CMIP5 Ensemble r1i1p1 (Alt)", "description": "Alt ensemble member r1i1p1.", "value": "r1i1p1"},
            "r2i1p1 (Alt)": {"summary": "CMIP5 Ensemble r2i1p1 (Alt)", "description": "Alt ensemble member r2i1p1.", "value": "r2i1p1"},
        },
    )
    experiment: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Experiment Name",
        description=(
            "Descriptive `title` for the experiment. In CMIP5, this was a global attribute <sup>1</sup>. In CMIP6, it draws from a "
            "controlled vocabulary (e.g., `pre-industrial control`) <sup>2</sup>.<br><br>"
            "<small><sup>1</sup>: [CMIP5 Model Output Requirements]"
            "(https://pcmdi.llnl.gov/mips/cmip5/CMIP5_output_metadata_requirements.pdf), Section 'Required global attributes'</small><br>"
            "<small><sup>2</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small>"
        ),
        openapi_examples={
            "Historical": {"summary": "Historical", "description": "Historical experiment.", "value": "historical"},
            "piControl": {"summary": "Pre-Industrial Control", "description": "Pre-industrial control experiment.", "value": "piControl"},
            "1pctCO2": {"summary": "1% CO2 Increase", "description": "1% per year CO2 increase experiment.", "value": "1pctCO2"},
        },
    )
    experiment_family: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Experiment Family (CMIP6)",
        description=(
            "In CMIP6, identifies the broader `family` of experiments (e.g., `historical`, `dcpp`, `idealized`). <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small>"
        ),
        openapi_examples={
            "DCPP": {"summary": "DCPP Family", "description": "DCPP experiment family.", "value": "DCPP"},
            "PAMIP": {"summary": "PAMIP Family", "description": "PAMIP experiment family.", "value": "PAMIP"},
            "ScenarioMIP": {"summary": "ScenarioMIP Family", "description": "ScenarioMIP experiment family.", "value": "ScenarioMIP"},
        },
    )
    experiment_id: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Experiment ID (CMIP6)",
        description=(
            "Short string identifying the `experiment`, from a controlled vocabulary (e.g., `historical`, `piControl`). <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small>"
        ),
        openapi_examples={
            "dcppA-hindcast": {"summary": "dcppA-hindcast", "description": "dcppA-hindcast experiment ID.", "value": "dcppA-hindcast"},
            "ssp585": {"summary": "ssp585", "description": "ssp585 experiment ID.", "value": "ssp585"},
            "piControl": {"summary": "piControl", "description": "piControl experiment ID.", "value": "piControl"},
        },
    )
    experiment_title: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Experiment Title",
        description="The full `title` of the experiment, providing a human-readable description.",
        openapi_examples={
            "Historical": {"summary": "Historical", "description": "Historical experiment.", "value": "historical"},
            "piControl": {"summary": "Pre-Industrial Control", "description": "Pre-industrial control experiment.", "value": "piControl"},
        },
    )
    forcing: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Forcing (CMIP5)",
        description=(
            "List of `forcing` agents. For a control run with no variation in radiative forcing, this is `N/A`. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP5 Model Output Requirements]"
            "(https://pcmdi.llnl.gov/mips/cmip5/CMIP5_output_metadata_requirements.pdf), Section 'Required global attributes'</small>"
        ),
        openapi_examples={
            "Natural": {"summary": "Natural Forcing", "description": "Forcing agents: Volcanic, Solar.", "value": "N/A"},
            "GHG": {"summary": "Greenhouse Gas Forcing", "description": "Forcing agents: GHG.", "value": "GHG"},
        },
    )
    frequency: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Sampling Frequency",
        description=(
            "The `frequency` of data samples, e.g., `mon` (monthly), `day` (daily), `6hr` (6-hourly). <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small>"
        ),
        openapi_examples={
            "Monthly": {"summary": "Monthly", "description": "Monthly sampling frequency.", "value": "mon"},
            "Daily": {"summary": "Daily", "description": "Daily sampling frequency.", "value": "day"},
            "6-Hourly": {"summary": "6-Hourly", "description": "6-hourly sampling frequency.", "value": "6hr"},
        },
    )
    grid: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Grid Description",
        description=(
            "A textual `description` of the grid used for the data. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small>"
        ),
        openapi_examples={
            "Native": {
                "summary": "Native Grid",
                "description": "Data on the model's native grid.",
                "value": "data regridded to a 360x180 latxlon grid from the native T127l grid",
            },
        },
    )
    grid_label: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Grid Label",
        description=(
            "A short string identifying the `grid`, e.g., `gn` (generic), `gr` (regridded). <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small>"
        ),
        openapi_examples={
            "gn": {"summary": "Generic Grid", "description": "Generic grid label.", "value": "gn"},
            "gr": {"summary": "Regridded", "description": "Regridded grid label.", "value": "gr"},
            "gr1": {"summary": "Regridded 1", "description": "Regridded grid label 1.", "value": "gr1"},
        },
    )
    grid_resolution: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Grid Resolution",
        description=(
            "The `resolution` of the grid, e.g., `2.5x2.5`. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP5 Model Output Requirements]"
            "(https://pcmdi.llnl.gov/mips/cmip5/CMIP5_output_metadata_requirements.pdf), "
            "Section 'Requirements for output variables' examples</small>"
        ),
        openapi_examples={"2.5x2.5": {"summary": "2.5x2.5 Resolution", "description": "Grid resolution 2.5x2.5.", "value": "2.5x2.5"}},
    )
    height_units: OptionalParam[MultiValued[str]] = Query(
        None,
        alias="height-units",
        title="Height Units",
        description="The `units` for the vertical coordinate, e.g., `m`.",
        openapi_examples={"meters": {"summary": "Meters", "description": "Height units in meters.", "value": "m"}},
    )
    index_node: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Index Node",
        description="The ESGF `index node` where the dataset is cataloged. <sup>1</sup><br><br><small><sup>1</sup>: [ESGF Search "
        "Documentation](https://esgf-node.llnl.gov/esgf_docs/search_api.html)</small>",
        openapi_examples={"US": {"summary": "US Index Node", "description": "ESGF index node in the US.", "value": "esgf-node.llnl.gov"}},
    )
    institute: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Institute (CMIP5)",
        description=(
            "A short identifier for the `institute` in CMIP5. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP5 Data Reference Syntax (DRS)]"
            "(https://pcmdi.llnl.gov/mips/cmip5/docs/cmip5_data_reference_syntax.pdf), Section 2.3</small>"
        ),
        openapi_examples={
            "CCCMA": {"summary": "CCCMA", "description": "Canadian Centre for Climate Modelling and Analysis", "value": "CCCMA"},
            "MIROC": {"summary": "MIROC", "description": "MIROC", "value": "MIROC"},
            "MOHC": {"summary": "MOHC", "description": "Met Office Hadley Centre", "value": "MOHC"},
        },
    )
    institution: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Institution",
        description=(
            "The `institution` that produced the data. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small>"
        ),
        openapi_examples={
            "UoM": {
                "summary": "University of Melbourne",
                "description": "The University of Melbourne, Parkville, Victoria 3010, Australia",
                "value": "The University of Melbourne, Parkville, Victoria 3010, Australia",
            },
            "IAMC": {
                "summary": "IAMC",
                "description": "Integrated Assessment Modeling Consortium",
                "value": "Integrated Assessment Modeling Consortium",
            },
        },
    )
    institution_id: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Institution ID (CMIP6)",
        description=(
            "A short identifier for the `institution`. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small>"
        ),
        openapi_examples={
            "IPSL": {"summary": "IPSL", "description": "Institut Pierre Simon Laplace", "value": "IPSL"},
            "CCCma": {"summary": "CCCma", "description": "Canadian Centre for Climate Modelling and Analysis", "value": "CCCma"},
            "CAS": {"summary": "CAS", "description": "Chinese Academy of Sciences", "value": "CAS"},
        },
    )
    instrument: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Instrument",
        description="The `instrument` used to collect the data, e.g., `MODIS`.",
        openapi_examples={"MODIS": {"summary": "MODIS", "description": "MODIS instrument.", "value": "MODIS"}},
    )
    land_grid_resolution: OptionalParam[MultiValued[str]] = Query(None, title="Land Grid Resolution")
    master_gateway: OptionalParam[MultiValued[str]] = Query(None, title="Master Gateway")
    member_id: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Member ID (CMIP6)",
        description=(
            "In CMIP6, this is the `variant_label` (e.g., `r1i1p1f1`). <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Section 'The CMIP6 Data Reference Syntax (DRS)'</small>"
        ),
        openapi_examples={
            "r1i1p1f1": {"summary": "r1i1p1f1", "description": "Member ID r1i1p1f1.", "value": "r1i1p1f1"},
            "r1i1p1f2": {"summary": "r1i1p1f2", "description": "Member ID r1i1p1f2.", "value": "r1i1p1f2"},
        },
    )
    metadata_format: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Metadata Format",
        description="The `format` of the metadata, e.g., `THREDDS`.",
        openapi_examples={"THREDDS": {"summary": "THREDDS", "description": "THREDDS metadata format.", "value": "THREDDS"}},
    )
    mip_era: OptionalParam[MultiValued[str]] = Query(
        None,
        title="MIP Era",
        description=(
            "The `era` of the Model Intercomparison Project, e.g., `CMIP5`, `CMIP6`. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small>"
        ),
        openapi_examples={
            "CMIP5": {"summary": "CMIP5 Era", "description": "MIP era CMIP5.", "value": "CMIP5"},
            "CMIP6": {"summary": "CMIP6 Era", "description": "MIP era CMIP6.", "value": "CMIP6"},
        },
    )
    model: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Model (CMIP5)",
        description=(
            "The `model` identifier used in CMIP5. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP5 Data Reference Syntax (DRS)]"
            "(https://pcmdi.llnl.gov/mips/cmip5/docs/cmip5_data_reference_syntax.pdf), Section 2.3</small>"
        ),
        openapi_examples={
            "bcc-csm1-1": {"summary": "bcc-csm1-1", "description": "Model bcc-csm1-1.", "value": "bcc-csm1-1"},
            "ACCESS1-0": {"summary": "ACCESS1-0", "description": "Model ACCESS1-0.", "value": "ACCESS1-0"},
        },
    )
    model_cohort: OptionalParam[MultiValued[str]] = Query(
        None,
        alias="model_cohort",
        title="Model Cohort",
        description="The `cohort` to which the model belongs, e.g., `CMIP5`.",
        openapi_examples={"CMIP5": {"summary": "CMIP5 Cohort", "description": "Model cohort CMIP5.", "value": "CMIP5"}},
    )
    model_version: OptionalParam[MultiValued[str]] = Query(
        None,
        alias="model_version",
        title="Model Version",
        description=(
            "The `version` of the model. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP5 Model Output Requirements]"
            "(https://pcmdi.llnl.gov/mips/cmip5/CMIP5_output_metadata_requirements.pdf), Section 'Required global attributes'</small>"
        ),
        openapi_examples={"1": {"summary": "Version 1", "description": "Model version 1.", "value": "1"}},
    )
    nominal_resolution: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Nominal Resolution (CMIP6)",
        description=(
            "The approximate horizontal `resolution` of the grid. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small>"
        ),
        openapi_examples={
            "100 km": {"summary": "100 km", "description": "Nominal resolution of 100 km.", "value": "100 km"},
            "250 km": {"summary": "250 km", "description": "Nominal resolution of 250 km.", "value": "250 km"},
            "10000 km": {"summary": "10000 km", "description": "Nominal resolution of 10000 km.", "value": "10000 km"},
        },
    )
    ocean_grid_resolution: OptionalParam[MultiValued[str]] = Query(None, title="Ocean Grid Resolution")
    Period: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Period",
        description="The `period` of time covered by the data, e.g., `1980-2005`.",
        openapi_examples={"1980-2005": {"summary": "1980-2005", "description": "Period 1980-2005.", "value": "1980-2005"}},
    )
    period: OptionalParam[MultiValued[str]] = Query(
        None,
        title="period",
        description="The `period` of time covered by the data, e.g., `1980-2005`.",
        openapi_examples={"1980-2005": {"summary": "1980-2005", "description": "period 1980-2005.", "value": "1980-2005"}},
    )
    processing_level: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Processing Level",
        description="The `processing level` of the data, e.g., `L3`.",
        openapi_examples={"L3": {"summary": "Level 3", "description": "Processing level 3.", "value": "L3"}},
    )
    product: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Product",
        description=(
            "The `product` type, e.g., `model-output`, `obs`. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small>"
        ),
        openapi_examples={
            "model-output": {"summary": "Model Output", "description": "Product type model-output.", "value": "model-output"},
            "obs": {"summary": "Observations", "description": "Product type obs.", "value": "obs"},
            "reanalysis": {"summary": "Reanalysis", "description": "Product type reanalysis.", "value": "reanalysis"},
        },
    )
    project: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Project",
        description="The `project` identifier, e.g., `CMIP5`, `CMIP6`. <sup>1</sup><br><br><small><sup>1</sup>: [ESGF Search "
        "Documentation](https://esgf-node.llnl.gov/esgf_docs/search_api.html)</small>",
        openapi_examples={
            "CMIP5": {"summary": "CMIP5 Project", "description": "Project CMIP5.", "value": "CMIP5"},
            "CMIP6": {"summary": "CMIP6 Project", "description": "Project CMIP6.", "value": "CMIP6"},
            "obs4MIPs": {"summary": "obs4MIPs Project", "description": "Project obs4MIPs.", "value": "obs4MIPs"},
        },
    )
    quality_control_flags: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Quality Control Flags",
        description="Flags indicating the `quality control` status of the data, e.g., `passed`.",
        openapi_examples={"passed": {"summary": "Passed", "description": "Quality control passed.", "value": "passed"}},
    )
    range: OptionalParam[MultiValued[str]] = Query(None, title="Range")
    realm: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Realm",
        description=(
            "The modeling `realm` (e.g., `atmos`, `ocean`). <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small>"
        ),
        openapi_examples={
            "atmos": {"summary": "Atmosphere", "description": "Atmosphere realm.", "value": "atmos"},
            "ocean": {"summary": "Ocean", "description": "Ocean realm.", "value": "ocean"},
            "land": {"summary": "Land", "description": "Land realm.", "value": "land"},
        },
    )
    realm_drs: OptionalParam[MultiValued[str]] = Query(None, title="Realm DRS")
    region: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Region",
        description="The geographical `region` covered by the data, e.g., `global`.",
        openapi_examples={"global": {"summary": "Global", "description": "Global region.", "value": "global"}},
    )
    regridding: OptionalParam[MultiValued[str]] = Query(None, title="Regridding")
    run_category: OptionalParam[MultiValued[str]] = Query(None, title="Run Category")
    Science_Driver: OptionalParam[MultiValued[str]] = Query(
        None,
        alias="Science Driver",
        title="Science Driver",
        description="The `science driver` for the experiment, e.g., `aerosol`.",
        openapi_examples={"aerosol": {"summary": "Aerosol", "description": "Aerosol science driver.", "value": "aerosol"}},
    )
    science_driver_: OptionalParam[MultiValued[str]] = Query(None, alias="science driver", title="Science Driver (Alternative)")
    science_driver: OptionalParam[MultiValued[str]] = Query(
        None,
        title="science_driver",
        description="The `science driver` for the experiment, e.g., `aerosol`.",
        openapi_examples={"aerosol": {"summary": "Aerosol", "description": "aerosol science driver.", "value": "aerosol"}},
    )
    seaice_grid_resolution: OptionalParam[MultiValued[str]] = Query(None, title="Sea Ice Grid Resolution")
    set_name: OptionalParam[MultiValued[str]] = Query(None, title="Set Name")
    short_description: OptionalParam[MultiValued[str]] = Query(None, title="Short Description")
    source: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Source (CMIP5)",
        description=(
            "The `source` of the data, which is the model name in CMIP5. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP5 Data Reference Syntax (DRS)]"
            "(https://pcmdi.llnl.gov/mips/cmip5/docs/cmip5_data_reference_syntax.pdf), Section 2.3</small>"
        ),
        openapi_examples={
            "bcc-csm1-1": {"summary": "bcc-csm1-1", "description": "Source bcc-csm1-1.", "value": "bcc-csm1-1"},
            "ACCESS1-0": {"summary": "ACCESS1-0", "description": "Source ACCESS1-0.", "value": "ACCESS1-0"},
        },
    )
    source_id: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Source ID (CMIP6, Obs4MIPs)",
        description=(
            "The `source` identifier, which is the model name in CMIP6 or the dataset name in Obs4MIPs. <sup>1, 2</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small><br>"
            "<small><sup>2</sup>: [Obs4MIPs Data Specifications 2.5 (ODS2.5)](https://doi.org/10.5281/zenodo.11500474), Table 1</small>"
        ),
        openapi_examples={
            "IPSL-CM6A-LR": {"summary": "IPSL-CM6A-LR", "description": "Source ID IPSL-CM6A-LR.", "value": "IPSL-CM6A-LR"},
            "BCC-CSM2-MR": {"summary": "BCC-CSM2-MR", "description": "Source ID BCC-CSM2-MR.", "value": "BCC-CSM2-MR"},
            "HadISST-1-1": {"summary": "HadISST-1-1", "description": "Source ID HadISST-1-1.", "value": "HadISST-1-1"},
        },
    )
    source_type: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Source Type (CMIP6, Obs4MIPs)",
        description=(
            "The `type` of the data source, e.g., `AOGCM` (Atmosphere-Ocean General Circulation Model), `SATELLITE`. <sup>1, 2</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small><br>"
            "<small><sup>2</sup>: [Obs4MIPs Data Specifications 2.5 (ODS2.5)](https://doi.org/10.5281/zenodo.11500474), Table 1</small>"
        ),
        openapi_examples={
            "AOGCM": {"summary": "AOGCM", "description": "Source type AOGCM.", "value": "AOGCM"},
            "SATELLITE": {"summary": "SATELLITE", "description": "Source type SATELLITE.", "value": "SATELLITE"},
        },
    )
    source_version: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Source Version",
        description="The `version` of the source data.",
        openapi_examples={"v20210812": {"summary": "v20210812", "description": "Source version v20210812.", "value": "v20210812"}},
    )
    source_version_number: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Source Version Number",
        description="The `version number` of the source data.",
        openapi_examples={"v20210812": {"summary": "v20210812", "description": "Source version number v20210812.", "value": "v20210812"}},
    )
    status: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Status",
        description="The `status` of the dataset, e.g., `latest`.",
        openapi_examples={"latest": {"summary": "Latest", "description": "Status latest.", "value": "latest"}},
    )
    sub_experiment_id: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Sub-Experiment ID",
        description="The identifier for a `sub-experiment`, e.g., `s1960-r1i1p1f1`.",
        openapi_examples={
            "s1960-r1i1p1f1": {"summary": "s1960-r1i1p1f1", "description": "Sub-experiment ID s1960-r1i1p1f1.", "value": "s1960-r1i1p1f1"}
        },
    )
    table: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Table (CMIP5)",
        description=(
            "The CMOR `table` used in CMIP5. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP5 Data Reference Syntax (DRS)]"
            "(https://pcmdi.llnl.gov/mips/cmip5/docs/cmip5_data_reference_syntax.pdf), Section 2.3</small>"
        ),
        openapi_examples={
            "Amon": {"summary": "Amon Table", "description": "CMOR table Amon.", "value": "Amon"},
            "Omon": {"summary": "Omon Table", "description": "CMOR table Omon.", "value": "Omon"},
            "Lmon": {"summary": "Lmon Table", "description": "CMOR table Lmon.", "value": "Lmon"},
        },
    )
    table_id: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Table ID (CMIP6)",
        description=(
            "The CMOR `table` identifier used in CMIP6. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small>"
        ),
        openapi_examples={
            "Amon": {"summary": "Amon Table", "description": "Table ID Amon.", "value": "Amon"},
            "Omon": {"summary": "Omon Table", "description": "Table ID Omon.", "value": "Omon"},
            "Emon": {"summary": "Emon Table", "description": "Table ID Emon.", "value": "Emon"},
        },
    )
    target_mip: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Target MIP",
        description="The `target MIP` for the data, e.g., `CMIP`.",
        openapi_examples={"CMIP": {"summary": "CMIP", "description": "Target MIP CMIP.", "value": "CMIP"}},
    )
    target_mip_list: OptionalParam[MultiValued[str]] = Query(None, title="Target MIP List")
    target_mip_listsource: OptionalParam[MultiValued[str]] = Query(None, title="Target MIP List Source")
    target_mip_single: OptionalParam[MultiValued[str]] = Query(None, title="Target MIP Single")
    time_frequency: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Time Frequency",
        description="The `time frequency` of the data, e.g., `mon`.",
        openapi_examples={"mon": {"summary": "Monthly", "description": "Monthly time frequency.", "value": "mon"}},
    )
    tuning: OptionalParam[MultiValued[str]] = Query(None, title="Tuning")
    variable: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Variable (CMIP5)",
        description=(
            "The `variable` name as defined in the CMIP5 standard output. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP5 Data Reference Syntax (DRS)]"
            "(https://pcmdi.llnl.gov/mips/cmip5/docs/cmip5_data_reference_syntax.pdf), Section 2.3</small>"
        ),
        openapi_examples={
            "tas": {"summary": "tas", "description": "Variable tas.", "value": "tas"},
            "pr": {"summary": "pr", "description": "Variable pr.", "value": "pr"},
            "ua": {"summary": "ua", "description": "Variable ua.", "value": "ua"},
        },
    )
    variable_id: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Variable ID (CMIP6, Obs4MIPs)",
        description=(
            "The `variable` identifier as defined in the CMIP6 and Obs4MIPs standard output. <sup>1, 2</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small><br>"
            "<small><sup>2</sup>: [Obs4MIPs Data Specifications 2.5 (ODS2.5)](https://doi.org/10.5281/zenodo.11500474), Table 1</small>"
        ),
        openapi_examples={
            "ua": {"summary": "ua", "description": "Variable ID ua.", "value": "ua"},
            "ta": {"summary": "ta", "description": "Variable ID ta.", "value": "ta"},
            "psl": {"summary": "psl", "description": "Variable ID psl.", "value": "psl"},
        },
    )
    variable_label: OptionalParam[MultiValued[str]] = Query(None, title="Variable Label")
    variable_long_name: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Variable Long Name",
        description="The `long name` of the variable, e.g., `Precipitation`.",
        openapi_examples={
            "Precipitation": {"summary": "Precipitation", "description": "Precipitation long name.", "value": "Precipitation"}
        },
    )
    variant_label: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Variant Label (CMIP6)",
        description=(
            "A label constructed from the realization, initialization, physics, and forcing indices (`r<N>i<M>p<L>f<K>`). <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Table 1</small>"
        ),
        openapi_examples={
            "r1i1p1f1": {"summary": "r1i1p1f1", "description": "Variant label r1i1p1f1.", "value": "r1i1p1f1"},
            "r1i1p1f2": {"summary": "r1i1p1f2", "description": "Variant label r1i1p1f2.", "value": "r1i1p1f2"},
            "r1i1p1f3": {"summary": "r1i1p1f3", "description": "Variant label r1i1p1f3.", "value": "r1i1p1f3"},
        },
    )
    version: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Version",
        description=(
            "The `version` of the dataset, typically in the format `vYYYYMMDD`. <sup>1</sup><br><br>"
            "<small><sup>1</sup>: [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV's]"
            "(https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf), "
            "Section 'Directory structure template'</small>"
        ),
        openapi_examples={
            "v20190429": {"summary": "20190429", "description": "Version 20190429.", "value": "20190429"},
            "v20201222": {"summary": "20201222", "description": "Version 20201222.", "value": "20201222"},
            "v20200108": {"summary": "20200108", "description": "Version 20200108.", "value": "20200108"},
        },
    )
    versionnum: OptionalParam[MultiValued[str]] = Query(
        None,
        title="Version Number",
        description="The `version number` of the dataset.",
        openapi_examples={"1": {"summary": "1", "description": "Version number 1.", "value": "1"}},
    )
    year_of_aggregation: OptionalParam[MultiValued[str]] = Query(None, title="Year of Aggregation")

    # Time-based search parameters
    start: OptionalParam[str] = Query(
        None,
        title="Temporal Coverage Start",
        description="The `start` of the temporal coverage in the dataset. <sup>1</sup><br><br><small><sup>1</sup>: [ESGF Search "
        "Documentation](https://esgf-node.llnl.gov/esgf_docs/search_api.html)</small>",
        openapi_examples={
            "Start 1980": {
                "summary": "Start 1980",
                "description": "Temporal coverage starts on 1980-01-01.",
                "value": "1980-01-01T00:00:00Z",
            },
            "Start 2000": {
                "summary": "Start 2000",
                "description": "Temporal coverage starts on 2000-01-01.",
                "value": "2000-01-01T00:00:00Z",
            },
        },
    )
    end: OptionalParam[str] = Query(
        None,
        title="Temporal Coverage End",
        description="The `ending` of the temporal coverage in the dataset. <sup>1</sup><br><br><small><sup>1</sup>: [ESGF Search "
        "Documentation](https://esgf-node.llnl.gov/esgf_docs/search_api.html)</small>",
        openapi_examples={
            "End 2000": {"summary": "End 2000", "description": "Temporal coverage ends on 2000-12-31.", "value": "2000-12-31T23:59:59Z"},
            "End 2014": {"summary": "End 2014", "description": "Temporal coverage ends on 2014-12-31.", "value": "2014-12-31T23:59:59Z"},
        },
    )
    latest: OptionalParam[bool] = Query(
        None,
        title="Latest Version Only",
        description="If enabled, only returns the `latest versions` of datasets. <sup>1</sup><br><br><small><sup>1</sup>: [ESGF Search "
        "Documentation](https://esgf-node.llnl.gov/esgf_docs/search_api.html)</small>",
        openapi_examples={
            "True": {"summary": "Latest Only", "description": "Only retrieve the latest versions.", "value": True},
            "False": {"summary": "All Versions", "description": "Retrieve all versions, including deprecated ones.", "value": False},
        },
    )

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

        if isinstance(value, str):
            return [
                GlobusFacet(name=facet.strip(), field_name=facet.strip(), type="terms") for facet in value.split(",")
            ]

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
                    values=[GlobusRange(from_=lower_bound, to=upper_bound)],  # type: ignore[reportArgumentType]
                ),
            )

        if {"from_", "to"} & query.model_fields_set:
            built_filters.append(
                GlobusRangeFilter(field_name="_timestamp", values=[GlobusRange(from_=query.from_ or "*", to=query.to or "*")])
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
    q: OptionalParam[str] = None
    """The search query."""
    advanced: bool = True
    """Whether or not to use advanced search."""
    limit: int = 10
    """The maximum number of results to return."""
    offset: int = Field(0, ge=0, le=9999)
    """The number of results to skip."""

    filters: OptionalParam[SerializeAsAny[SupportedAsFilters]] = None
    """A list of filters to apply to the query.
        Note: Globus Filters is a parent model for the specific types of filters that Globus supports.
            The `SerializeAsAny` type annotation is necessary for Pydantic to include attributes defined
            in the child model, but not in the parent model, while still allowing any subtype to be used.
    """

    facets: OptionalParam[SupportedAsFacets] = None
    """A list of facets to apply to the query."""

    # filter_principal_sets: OptionalParam[str] = None
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

    value: OptionalParam[float] = None
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

    facet_results: OptionalParam[list[GlobusFacetResult]] = None
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
    echoParams: str = "all"  # noqa: N815
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

    numFound: int  # noqa: N815
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

    responseHeader: ESGSearchHeader  # noqa: N815
    """Represents the response header for the ESG Search Response."""
    response: ESGSearchResult
    """Represents a search result from ESG Search."""
    facet_counts: ESGFSearchFacetResult = ESGFSearchFacetResult()
    """Represents a facet result from ESG Search."""
