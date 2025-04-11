import json
import re
from datetime import datetime
from keyword import iskeyword
from types import EllipsisType
from typing import Annotated

import pydantic
import requests
from datamodel_code_generator import DataModelType, PythonVersion
from datamodel_code_generator.model import get_data_model_types
from datamodel_code_generator.parser.jsonschema import JsonSchemaParser
from fastapi import Query
from fastapi.params import Param
from pydantic_core import PydanticUndefined, PydanticUndefinedType

from esg_fastapi.api.versions.v1.models import ESGSearchQuery, MultiValued

RETRIEVE_EXAMPLES = 3

# TODO: can we get this from ESGSearch instead of Solr directly?
SOLR_API_URL = "http://localhost:8983/solr/files/admin/luke"
MappableTypes = type | Annotated
TYPE_MAPPING: dict[str, MappableTypes] = {
    "string": str,
    "date": datetime,
    "long": int,
    "text_general": str,
    "float": float,
    # probably need a converter for this. ref: https://github.com/ESGF/esgf-docker/blob/master/images/solr/core-template/conf/schema.xml#L584-L585
    # maybe convert to geojson using this? https://solr.apache.org/guide/6_6/transforming-result-documents.html#TransformingResultDocuments-_geo_-Geospatialformatter
    # what does elastic support? geojson is a good bet
    "location_rpt": str,
    "boolean": bool,
    "int": int,
    "text_general_rev": str,
}


def lookup_default(field: dict) -> bool | None | EllipsisType | PydanticUndefinedType:
    """Convert the `default` field to a `type` and value appropriate for the field."""
    match field.get("default"):
        case "true" | "false" as value:
            return bool(value)
        case "NOW":
            # timestamp defaults to "NOW," makes sense when ingesting, but querying should be optional (None)
            return None
        case None:
            return PydanticUndefined
        case value:
            return value


def lookup_type(field: dict) -> MappableTypes:
    """Look up the type mapping for the given field's type string.

    Args:
    field (dict): A dictionary containing the schema and type of the field.

    Returns:
    MappableTypes: The mapped type for the field's type string.

    Raises:
    ValueError: If the type string cannot be mapped to a type.

    Notes:
    - If the field's schema string contains "M", it returns a MultiValued version of the mapped type.
    - Otherwise, it returns the type directly.
    """
    schema = field["schema"]
    match TYPE_MAPPING.get(field["type"]):
        case None:
            raise ValueError(f"Could not map `type` string {field['type']} to type")
        case value if "M" in schema:
            return MultiValued[value]
        case value:
            return value


def validate_name(name: str) -> tuple[str, int]:
    """Validates a field name and returns a validated name and a flag indicating if the name was modified.

    Args:
    name (str): The original field name.

    Returns:
    tuple[str, int]: A tuple containing the validated field name and a flag indicating if the name was modified.

    The validated field name is either the original name with leading underscores, or a modified name with a suffix added if it is a reserved keyword or starts with an underscore.

    The flag indicates if the name was modified. If the name was not modified, the flag is 0. If the name was modified, the flag is 1.

    Examples:
    >>> validate_name("_id")
    ('id_', 1)
    >>> validate_name("author")
    ('author', 0)
    """
    if iskeyword(name) or name.startswith("_"):
        return (f"{name.lstrip('_')}_", 1)
    else:
        return re.subn(r"\W|^(?=\d)", "_", name)


def generate_field_defintions(key: str, value: dict) -> dict[str, tuple[type, Param]]:
    """Generates field definitions for a given key and its corresponding value.

    Args:
    key (str): The name of the field to generate definitions for.
    value (dict): A dictionary containing the type and FieldInfo object of the field.

    Returns:
    dict[str, tuple[type, Param]]: A dictionary containing the validated field name and a tuple containing the mapped type for the field's type string and a Query parameter.

    The validated field name is either the original name with leading underscores, or a modified name with a suffix added if it is a reserved keyword or starts with an underscore.

    The tuple contains the mapped type for the field's type string and a Query parameter. The Query parameter has a default value, an optional alias, and a list of examples.

    Notes:
    - If the field's schema string contains "M", it returns a MultiValued version of the mapped type.
    - Otherwise, it returns the type directly.

    Examples:
    >>> generate_field_definitions("_id", {"type": "string", "schema": "SOLR_TYPE_STRING"})
    {'id_': (<class 'str'>, Query(default=None, alias='id_', examples=[u'1234567890']))}
    """
    lookup = requests.get(SOLR_API_URL, params={"wt": "json", "numTerms": RETRIEVE_EXAMPLES, "fl": key}).json()
    details = lookup["fields"][key]
    name, aliased = validate_name(key)
    return {
        name: (
            lookup_type(value),
            Query(
                default=lookup_default(value),
                alias=name if aliased else None,
                # `xlink` doesn't return topTerms. why?
                examples=details.get("topTerms", [])[::2],
            ),
        )
    }


# NOTE: Using `fl:*` makes the query take a while, but seems like its necessary in order to get top terms back
#       Not including `fl:*` still returns all fields (and quickly) but not top terms, which we want to use for examples.
#       otherwise we could get everything in one request instead of looking up each field individually in the loop.
# TODO: If `dynamicBase` is *NOT* set, the field was defined in the schema.xml file and is thus a core field and
#       Should(tm) exist in all records. We should use this to split the models into a core ESGF model and child models
#       for the various projects with their own additional fields.
field_lookup = requests.get(SOLR_API_URL, params={"wt": "json", "show": "all"}).json()

known_fields = ESGSearchQuery.model_fields.keys()
discovered_fields = field_lookup["fields"]

# For some reason, "Science Driver" is returned in the field list, but returns an empty
# `fields` dict when looked up with `fl=Science Driver` or `fl=Science+Driver`
del discovered_fields["Science Driver"]

missing_fields = {key: discovered_fields[key] for key in (discovered_fields.keys() - known_fields)}

# TODO: Set a private property on ESGSearchQuery model to indicate the last modified date of the index. Skip this lookup
#       if the index hasn't changed since the last time this was run.
if missing_fields:
    NewESGSearchQuery = pydantic.create_model(
        __model_name="ESGSearchQuery",
        __base__=ESGSearchQuery,
        # Type checking doesn't recognize the **dict syntax as valid for the field defs, so ignore it on this line only
        # since the generation function is fully typed anyway.
        **{name: field for k, v in missing_fields.items() for name, field in generate_field_defintions(k, v).items()},  # type: ignore
    )

    # ref: https://koxudaxi.github.io/datamodel-code-generator/using_as_module/#__codelineno-3-1
    data_model_types = get_data_model_types(
        DataModelType.PydanticV2BaseModel, target_python_version=PythonVersion.PY_312
    )
    ESGSearchQuery.model_json_schema()

    # TODO:
    # - This inherits from `ESGSearchQuery` but doesn't preserve the existing definition.
    # - Custom types and aliases aren't kept, but converted to standard types.
    # - Attribute level docstrings aren't kept.
    parser = JsonSchemaParser(
        json.dumps(NewESGSearchQuery.model_json_schema()),
        data_model_type=data_model_types.data_model,
        data_model_root_type=data_model_types.root_model,
        data_model_field_type=data_model_types.field_model,
        data_type_manager_type=data_model_types.data_type_manager,
        dump_resolve_reference_action=data_model_types.dump_resolve_reference_action,
    )

    print(parser.parse())  # noqa: T201
