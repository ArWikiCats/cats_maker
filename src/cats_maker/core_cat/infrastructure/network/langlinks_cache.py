""" """

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from .mapping import PageParseResult

logger = logging.getLogger(__name__)

deleted_pages = []


class LangLinksCacheManager:
    """Manages internal caching structures for MediaWiki page data, cross-language links,
    and category mapping tracking."""

    def __init__(self, enabled: bool = True) -> None:
        self._cache: dict[tuple[str, str, str], dict[str, Any]] = {}
        self.lang_links_cache: dict[str, dict[str, dict[str, str]]] = defaultdict(lambda: defaultdict(dict))
        # Track pages inside English categories that miss Arabic langlinks
        self.cached_arpage_inside_encat: dict[str, list[str]] = defaultdict(list)

        self.enabled = enabled

    def update_page_cache(
        self,
        title: str,
        site_code: str,
        data: dict[str, Any],
        props: str = "",
    ) -> None:
        """Store full payload and individual sub-properties into cache safely."""
        # Explicitly tag full payload keys to prevent property collision
        if not self.enabled:
            return
        prop_label = props if props else "default"
        full_payload_key = (title, site_code, f"full_{prop_label}")
        self._cache[full_payload_key] = {title: data}

        # Update cross-language map
        langlinks = data.get("langlinks")
        if isinstance(langlinks, dict):
            for target_lang, target_title in langlinks.items():
                # enwiki -> Yemen -> ar -> اليمن
                self.lang_links_cache[site_code][title][target_lang] = target_title

                # arwiki -> اليمن -> en -> Yemen
                self.lang_links_cache[target_lang][target_title][site_code] = title

    def track_encat_missing_arpage(self, page_title: str, parent_category: str) -> None:
        """Record pages inside an English category that lack Arabic equivalents."""
        if not self.enabled:
            return
        if parent_category not in self.cached_arpage_inside_encat[page_title]:
            self.cached_arpage_inside_encat[page_title].append(parent_category)

    def get_cached_arpage_inside_encat(self, page_title: str) -> list[str] | None:
        """Retrieve cached parent category mapping for a given page."""
        if not self.enabled:
            return None
        return self.cached_arpage_inside_encat.get(page_title)

    def get_cached_item(self, title: str, site_code: str, key: str) -> Any:
        """Retrieve an item from the main cache dictionary."""
        if not self.enabled:
            return None
        return self._cache.get((title, site_code, key))

    def clear(self) -> None:
        """Reset all cached data structures."""
        if not self.enabled:
            return
        self._cache.clear()
        self.lang_links_cache.clear()
        self.cached_arpage_inside_encat.clear()

    def get_cached_page_parse_result(
        self,
        title: str,
        site_code: str,
        props: str,
    ) -> dict[str, Any] | None:
        cached_result = self.get_cached_item(title, site_code, f"full_{props}")
        if cached_result:
            logger.debug("Returning cached data ")
            result = PageParseResult.from_json_or_none(cached_result)
            if result:
                return {title: result}
        return None

    def cache_results(self, site_code: str, props: str, results: dict[str, PageParseResult]):
        for title, data in results.items():
            self.update_page_cache(title, site_code, data.to_json(), props)

    def track_encat_missing_arpages(self, cats_without_langlinks: list[str], page_title: str):
        # Update cache tracking for categories missing Arabic language links
        formatted_in_line = ", ".join(cats_without_langlinks)
        logger.debug("Categories without langlinks: %s", formatted_in_line)
        for cat in cats_without_langlinks:
            self.track_encat_missing_arpage(
                page_title=cat,
                parent_category=page_title,
            )


__all__ = [
    "LangLinksCacheManager",
]
