#!/usr/bin/python3
"""Template query — refactored from temp_bot.py."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from ....shared import find_LCN
from ..constants import SKIP_CATEGORIES

logger = logging.getLogger(__name__)


class TemplateCache:
    """Encapsulates the module-level template cache."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = defaultdict(dict)

    def get(self, enlink: str, sitecode: str) -> Any | None:
        site_cache = self._store[sitecode]

        if enlink in site_cache:
            return site_cache[enlink]

        return None

    def set(self, enlink: str, sitecode: str, value: Any) -> None:
        self._store[sitecode][enlink] = value


_cache = TemplateCache()


def get_templates(titles: str | list[str], sitecode: str = "ar") -> dict[str, list[str]] | list[str] | None:
    """Single entry point for template queries.

    Pass a string for one title, a list for batch.
    """
    if isinstance(titles, str):
        result = _query_multi(titles, sitecode)
        if not result:
            return None
        return result.get(titles, {}).get("templates")

    joined = "|".join(titles)
    return _query_multi(joined, sitecode)


def _query_multi(enlink: str, sitecode: str):
    if enlink in SKIP_CATEGORIES:
        return None

    cached = _cache.get(enlink, sitecode)
    if cached is not None:
        return cached

    logger.info(f"templatequery {sitecode}:{enlink} . ")

    sasa = find_LCN(enlink, prop="templates", first_site_code=sitecode)
    result = sasa if sasa else None

    _cache.set(enlink, sitecode, result)
    return result
