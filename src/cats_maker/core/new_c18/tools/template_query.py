#!/usr/bin/python3
"""Template query — refactored from temp_bot.py."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from ....shared import find_page_data
from ..constants import SKIP_CATEGORIES

logger = logging.getLogger(__name__)


class TemplateCache:
    """Encapsulates the module-level template cache."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = defaultdict(dict)

    def get(self, enlink: str, site_code: str) -> Any | None:
        site_cache = self._store[site_code]

        if enlink in site_cache:
            return site_cache[enlink]

        return None

    def set(self, enlink: str, site_code: str, value: Any) -> None:
        self._store[site_code][enlink] = value


_cache = TemplateCache()


def get_templates(titles: str | list[str], site_code: str = "ar") -> dict[str, list[str]] | list[str] | None:
    """Single entry point for template queries.

    Pass a string for one title, a list for batch.
    """
    if isinstance(titles, str):
        result = _query_multi(titles, site_code)
        if not result:
            return None
        return result.get(titles, {}).get("templates")

    joined = "|".join(titles)
    return _query_multi(joined, site_code)


def _query_multi(enlink: str, site_code: str):
    if enlink in SKIP_CATEGORIES:
        return None

    cached = _cache.get(enlink, site_code)
    if cached is not None:
        return cached

    logger.info(f"templatequery {site_code}:{enlink} . ")

    sasa = find_page_data(enlink, prop="templates", first_site_code=site_code)
    result = sasa if sasa else None

    _cache.set(enlink, site_code, result)
    return result


__all__ = [
    "TemplateCache",
    "get_templates",
]
