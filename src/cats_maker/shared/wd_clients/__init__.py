from __future__ import annotations

from .wd_sparql import (
    get_properties_for_qids,
    get_properties_label,
)
from .wikidata_client import WikidataClient

__all__ = [
    "get_properties_label",
    "get_properties_for_qids",
    "WikidataClient",
]
