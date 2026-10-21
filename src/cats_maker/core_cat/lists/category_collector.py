"""
Helper module for category member processing.

This module encapsulates all logic related to collecting, merging, filtering,
and normalizing category members from various sources (API, SQL).
Responsibilities:
- Gathering members from API, SQL
- Deduplicating results
- Removing invalid entries and redirects
- Returning a clean, final list of category members
"""

import logging
from itertools import chain
from typing import Any

from .category_resolver import CategoryResolver
from .member_lister import MemberLister
from ..c18.infrastructure.network.categories import CategoryMembersClient
from ...config import Settings
from ...shared.newapi import AllAPIS

logger = logging.getLogger(__name__)


class CategoryMemberCollector:
    """Service class to gather, merge, filter, and normalize category members."""

    def __init__(
        self,
        category_resolver: CategoryResolver | None = None,
        member_lister: MemberLister | None = None,
        category_members_client: CategoryMembersClient | None = None,
        settings_provider: Any | None = None,
    ) -> None:
        self.category_resolver = category_resolver or CategoryResolver()
        self.member_lister = member_lister or MemberLister()
        self.category_members_client = category_members_client or CategoryMembersClient()
        self.settings_provider = settings_provider or Settings

    def load_non_redirects(self, lang: str, page_titles: list[str]) -> dict[str, Any]:
        """Return a mapping of page title -> True (exists) / False (missing) / "redirect"."""
        if not page_titles:
            return {}

        bot = AllAPIS.load(lang, "wikipedia")
        return bot.newapi().find_pages_exists_or_not(page_titles, get_redirect=True)

    def remove_redirect_pages(self, lang: str, page_titles: list[str]) -> list[str]:
        """Remove redirect pages from a list of page titles."""
        result = self.load_non_redirects(lang, page_titles)
        non_redirects = [x for x, v in result.items() if v is True]
        logger.info(f"Removed {len(page_titles) - len(non_redirects)} redirect pages.")
        return non_redirects

    def gather_members_from_sql(self, ar_title: str, en_page_title: str) -> list[str]:
        """Gather category members using SQL-based queries."""
        return self.member_lister.get_listen_page_title(ar_title, en_page_title)

    def gather_members_from_api(self, en_page_title: str) -> list[str]:
        """Gather category members using the Wikipedia API."""
        result = self.category_resolver.make_lit_api_way(en_page_title, item_type="all")

        if result:
            return result

        clean_title = en_page_title.removeprefix("Category:")

        # {'Yemen': {'ns': 0, 'ar': 'اليمن'}, 'Outline of Yemen': {'ns': 0, 'ar': 'مخطط اليمن'}, ... }
        subcategories_result = self.category_members_client.retrieve_category_members_with_langlinks(
            "Category:" + clean_title,
            site_code="en",
            ctype="all",
            language_link_target="ar",
        )
        if subcategories_result:
            result = [x["ar"] for x in subcategories_result.values() if x.get("ar")]

        return result or []

    def merge_member_lists(self, *member_lists: list[str]) -> list[str]:
        """Merge multiple member lists, removing duplicates while preserving order."""
        # Chain all lists and use dict.fromkeys() for efficient O(n) deduplication
        return list(dict.fromkeys(chain.from_iterable(member_lists)))

    def filter_invalid_members(self, members: list[str]) -> list[str]:
        """Filter out invalid members (empty strings, non-strings, None values)."""
        return [m for m in members if m and isinstance(m, str)]

    def deduplicate_members(self, members: list[str]) -> list[str]:
        """Remove duplicate entries from a member list while preserving order."""
        return list(set(members))

    def collect(self, ar_title: str, en_page_title: str) -> list[str]:
        """
            Collect, merge, filter, and normalize category members from all sources.

            This is the main entry point for gathering category members. It:
            1. Gathers members from SQL sources
            2. Gathers members from API if SQL returns empty or is disabled
        X    4. Merges all results
            5. Deduplicates the list
            6. Filters out invalid entries
            7. Removes redirect pages

            Args:
                ar_title: The Arabic category title
                en_page_title: The English page title

            Returns:
                A clean, deduplicated list of valid category members
        """
        # Step 1: Gather members from SQL
        members = self.gather_members_from_sql(ar_title, en_page_title)
        main_settings = self.settings_provider.get_instance()

        # Step 2: Gather from API if SQL is disabled or returned empty
        if main_settings.analytics_database.use_sql is False or members == []:
            api_members = self.gather_members_from_api(en_page_title)
            members = self.merge_member_lists(members, api_members)

        # Step 4: Deduplicate
        members = self.deduplicate_members(members)

        # Step 5: Filter invalid entries
        members = self.filter_invalid_members(members)

        # Step 6: Remove redirects
        members = self.remove_redirect_pages("ar", members)

        return members


__all__ = [
    "CategoryMemberCollector",
]
