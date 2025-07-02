from collections.abc import Sequence
from typing import TYPE_CHECKING, Annotated, Any, ForwardRef, Literal, TypedDict

from annotated_types import T
from fastapi import Query
from pydantic import AfterValidator, BeforeValidator, PlainSerializer

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


class GlobusToken(TypedDict):
    access_token: str
    expires_in: int
    resource_server: str
    scope: str
    token_type: Literal["bearer"]


class GlobusTokenResponse(GlobusToken):
    id_token: str
    state: str
    other_tokens: list[GlobusToken]
