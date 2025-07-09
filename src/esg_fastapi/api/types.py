from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, ForwardRef, Literal, TypedDict

from annotated_types import T
from fastapi import Query
from pydantic import BeforeValidator, PlainSerializer

from esg_fastapi.utils import ensure_list

if TYPE_CHECKING:  # pragma: no cover
    from .models import GlobusFacet, GlobusFilter
else:
    GlobusFacet = ForwardRef("GlobusFacet")
    GlobusFilter = ForwardRef("GlobusFilter")


Stringified = Annotated[T, PlainSerializer(str)]
"""String representation of the parameterized type."""

MultiValued = Annotated[list[T], BeforeValidator(ensure_list), Query()]
"""Solr MultiValued Field of the parameterized type."""

LowerCased = Annotated[T, PlainSerializer(lambda x: str(x).lower())]
"""Lower-case string representation of the parameterized type."""

SupportedAsFacets = str | Sequence[GlobusFacet]
"""Represents types convertable to a list of GlobusFacet objects."""

SupportedAsFilters = dict | Sequence[GlobusFilter]
"""Represents types convertable to a list of GlobusFilter objects."""

SolrFQ = str | Sequence[str]
"""Presentation type for the Solr `fq` field."""

# TODO: we should be able to better specify the typing of docs
SolrDoc = dict[str, Any]

SolrDatetime = Annotated[datetime, PlainSerializer(lambda x: x.strftime("%Y-%m-%dT%H:%M:%SZ")), Query()]

FacetName = str
FacetValue = str
FacetValueCount = int
ESGSearchFacetField = dict[FacetName, tuple[FacetValue | FacetValueCount, ...]]


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
