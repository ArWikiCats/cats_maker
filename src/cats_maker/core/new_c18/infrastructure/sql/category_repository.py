"""Data Access Layer (Repository Pattern)."""

import logging

from .....config.constants import NS_TEXT_AR, NS_TEXT_EN
from .....database import WikiReplicaDB

logger = logging.getLogger(__name__)

# Queries are defined here to keep them close to the data access logic
_ARCAT_QUERY = """
SELECT page_title, page_namespace
FROM page
JOIN categorylinks ON cl_from = page_id
JOIN linktarget ON cl_target_id = lt_id
JOIN langlinks ON page_id = ll_from
WHERE lt_title = %s
AND lt_namespace = 14
AND ll_lang = 'en'
GROUP BY page_title
"""

_ENCAT_QUERY = """
SELECT ll_title, page_namespace
FROM page
JOIN categorylinks ON cl_from = page_id
JOIN linktarget ON cl_target_id = lt_id
JOIN langlinks ON page_id = ll_from
WHERE lt_title = %s
AND lt_namespace = 14
AND ll_lang = 'ar'
GROUP BY ll_title
"""


def add_namespace_prefix(title: str, ns: int | str, lang: str = "ar") -> str:
    """Helper to prepend namespace labels."""
    ns_key = str(ns)
    if not title or ns_key == "0":
        return title

    table = NS_TEXT_AR if lang == "ar" else NS_TEXT_EN
    prefix = table.get(ns_key)

    if not prefix:
        logger.debug("No namespace label found for ns=%s lang=%s", ns_key, lang)
        return title

    return f"{prefix}:{title}"


class CategoryRepository:
    """Handles all database interactions related to Wikipedia categories."""

    @staticmethod
    def fetch_arabic_titles_with_english_links(category_title: str) -> list[str]:
        """
        Fetch Arabic page titles that belong to a specific category
        and have an English language link.
        """

        if not WikiReplicaDB.can_use_sql():
            logger.warning("WikiReplicaDB not available, returning empty list")
            return []

        try:
            ar_db = WikiReplicaDB("arwiki")
            rows = ar_db.select_safe(query=_ARCAT_QUERY, params=(category_title,)) or []

            titles = [
                add_namespace_prefix(row["page_title"].replace(" ", "_"), row["page_namespace"], lang="ar")
                for row in rows
            ]
            return titles
        except Exception as e:
            logger.error("Failed to fetch Arabic titles for category '%s': %s", category_title, e)
            return []

    @staticmethod
    def fetch_english_titles_with_arabic_links(category_title: str) -> list[str]:
        """
        Fetch English language links (ll_title) for pages in a specific
        English category.
        """

        if not WikiReplicaDB.can_use_sql():
            logger.warning("WikiReplicaDB not available, returning empty list")
            return []

        try:
            en_db = WikiReplicaDB("enwiki")
            rows = en_db.select_safe(query=_ENCAT_QUERY, params=(category_title,)) or []

            titles = sorted(row["ll_title"] for row in rows)
            logger.debug("Fetched %d English titles for category '%s'", len(titles), category_title)
            return titles
        except Exception as e:
            logger.error("Failed to fetch English titles for category '%s': %s", category_title, e)
            return []


__all__ = [
    "CategoryRepository",
]
