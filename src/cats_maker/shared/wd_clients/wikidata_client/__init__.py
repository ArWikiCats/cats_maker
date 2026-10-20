from __future__ import annotations

from .bot_wd import WDFunctions
from .bot_wp import WPFunctions
from .entity_types import (
    WdClaims,
    WdDescriptions,
    WdItems,
    WdLabels,
    WdSiteLinks,
)
from .wd_requests_handler import (
    WikidataRequestHandler,
)
from .wikidata_client_main import WikidataClient

__all__ = [
    "WikidataClient",
    "WikidataRequestHandler",
    "WDFunctions",
    "WPFunctions",
    "WdClaims",
    "WdDescriptions",
    "WdItems",
    "WdLabels",
    "WdSiteLinks",
]
