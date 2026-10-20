#!/usr/bin/python3
"""Template query service — refactored to class-based architecture."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from ....config.constants import AR_CATEGORIES_SHOULD_SKIPPED_WITH_NS
from .langlinks import LangLinksClient

logger = logging.getLogger(__name__)


class TemplateCache:
    """Encapsulates template caching across site codes."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = defaultdict(dict)

    def get(self, enlink: str, site_code: str) -> Any | None:
        site_cache = self._store[site_code]
        return site_cache.get(enlink)

    def set(self, enlink: str, site_code: str, value: Any) -> None:
        self._store[site_code][enlink] = value


class TemplateClient:
    """
    Client for fetching templates used on pages/categories.
    """

    def __init__(
        self,
        langlinks_client: LangLinksClient | None = None,
        cache: TemplateCache | None = None,
        skip_categories: set[str] | list[str] | None = None,
    ) -> None:
        self.langlinks = langlinks_client or LangLinksClient()
        self._cache = cache or TemplateCache()
        self.skip_categories = skip_categories if skip_categories is not None else AR_CATEGORIES_SHOULD_SKIPPED_WITH_NS

    def query(self, title: str, site_code: str) -> Any | None:
        """Query templates for a given link and site code."""
        if title in self.skip_categories:
            return None

        cached = self._cache.get(title, site_code)
        if cached is not None:
            return cached

        logger.info(f"templatequery {site_code}:{title} . ")

        data = self.langlinks.find_page_data(title, prop="templates", site_code=site_code)
        result = data if data else None

        self._cache.set(title, site_code, result)
        return result

    def get_templates(self, titles: str | list[str], site_code: str = "ar") -> dict[str, list[str]] | list[str] | None:
        """
        Single entry point for template queries.

        Pass a string for one title, a list for batch queries.
        """
        if isinstance(titles, str):
            result = self.query(titles, site_code)
            if not result:
                return None
            return result.get(titles, {}).get("templates")

        joined = "|".join(titles)
        return self.query(joined, site_code)


__all__ = [
    "TemplateCache",
    "TemplateClient",
]
