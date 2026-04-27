#!/usr/bin/python3
"""Member lister — refactored from cat_tools_enlist.py."""

from __future__ import annotations

import logging

from ....config import settings
from ...api_sql import CategoryComparator
from ..utils.text import normalize_category_title
from .category_resolver import CategoryResolver
from .category_validator import validate_categories_for_new_cat

logger = logging.getLogger(__name__)


class MemberLister:
    """Orchestrates listing pages that should be added to a new category."""

    def __init__(self, cache: dict[str, list[str]] | None = None, resolver: CategoryResolver | None = None) -> None:
        self.cache = cache if cache is not None else {}
        self.resolver = resolver if resolver is not None else CategoryResolver()

    def extract_fan_page_titles(self, enpage_title: str) -> list[str]:
        """Fetch exclusive category titles from EN wiki via SQL comparator."""
        fapages: list[str] = []

        if settings.database.use_sql:
            comparator = CategoryComparator()
            cat2 = normalize_category_title(enpage_title, lang="en")
            fapages = comparator.get_exclusive_category_titles(cat2, "") or []

        logger.info(f"<<lightgreen>>Adding {len(fapages)} pages to fapage lists")
        return fapages

    def get_listen_page_title(self, ar_title: str, enpage_title: str) -> list[str]:
        """Resolve the list of Arabic pages to add to a new category."""
        enpage_title = enpage_title.strip()
        listen_page_title: list[str] = []

        validation = validate_categories_for_new_cat(ar_title, enpage_title, wiki="en")
        if validation.valid:
            listen_page_title = self.resolver.resolve_members(enpage_title, ar_title, wiki="en")

        if not listen_page_title:
            fapages = self.extract_fan_page_titles(enpage_title)
            listen_page_title.extend(fapages)

        if enpage_title in self.cache:
            logger.info(f'<<lightgreen>> cache hit for "{enpage_title}"')
            listen_page_title.extend(self.cache[enpage_title])

        listen_page_title = list({x for x in listen_page_title if isinstance(x, str) and x != ""})

        return listen_page_title
