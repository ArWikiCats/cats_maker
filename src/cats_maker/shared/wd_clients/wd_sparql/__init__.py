from __future__ import annotations

from .get_property_for_list import (
    get_properties_for_qids,
    get_properties_label,
)
from .wikidata_sparql import WikidataSPARQLClient

__all__ = [
    "WikidataSPARQLClient",
    "get_properties_label",
    "get_properties_for_qids",
]
