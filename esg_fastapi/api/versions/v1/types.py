from collections.abc import Sequence
from typing import TYPE_CHECKING, Annotated, Any, Callable, ForwardRef

from annotated_types import T
from fastapi import Query
from pydantic import AfterValidator, BeforeValidator, GetJsonSchemaHandler, PlainSerializer
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema
from pydantic_core.core_schema import (
    chain_schema,
    is_instance_schema,
    json_or_python_schema,
    no_info_plain_validator_function,
    str_schema,
    to_string_ser_schema,
    union_schema,
)
from semver import Version

from esg_fastapi.utils import ensure_list

if TYPE_CHECKING:  # pragma: no cover
    from .models import ESGSearchQuery, GlobusFacet, GlobusFilter, GlobusMetaResult
else:
    GlobusMetaResult = ForwardRef("GlobusMetaResult")
    ESGSearchQuery = ForwardRef("ESGSearchQuery")
    GlobusFacet = ForwardRef("GlobusFacet")
    GlobusFilter = ForwardRef("GlobusFilter")


Stringified = Annotated[T, AfterValidator(lambda x: str(x))]
"""String representation of the parameterized type."""

MultiValued = Annotated[list[T], BeforeValidator(ensure_list), Query()]
"""Solr MultiValued Field of the parameterized type."""

LowerCased = Annotated[T, PlainSerializer(lambda x: x.lower())]
"""Lower-case string representation of the parameterized type."""

SupportedAsFacets = str | Sequence[GlobusFacet]
"""Represents types convertable to a list of GlobusFacet objects."""

SupportedAsFilters = dict | Sequence[GlobusFilter]
"""Represents types convertable to a list of GlobusFilter objects."""

SolrFQ = str | Sequence[str]
"""Presentation type for the Solr `fq` field."""

SupportedAsFQ = ESGSearchQuery | SolrFQ
"""Represents types convertable to SolrFQ objects."""

# TODO: we should be able to better specify the typing of docs
SolrDoc = dict[str, Any]

SupportedAsSolrDocs = SolrDoc | Sequence[GlobusMetaResult]
"""Represents types convertable to a list of GlobusMetaResult objects."""


class SemVer(str):
    """Represents a semantic version string."""

    @staticmethod
    def validate_from_str(value: str) -> Version:
        return Version.parse(value)

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Callable[[Any], CoreSchema]) -> CoreSchema:
        """Generates the Pydantic core schema for a specific source type using the provided handler."""
        from_str_schema = chain_schema(
            [
                str_schema(),
                no_info_plain_validator_function(cls.validate_from_str),
            ]
        )

        return json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=union_schema(
                [
                    is_instance_schema(Version),
                    from_str_schema,
                ]
            ),
            serialization=to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, _: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        """Generates the Pydantic JSON schema using the provided core schema and handler."""
        return handler(str_schema())
