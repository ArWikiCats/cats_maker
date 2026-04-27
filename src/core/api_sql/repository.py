"""Data Access Layer (Repository Pattern)."""

import logging
from typing import List

from .db_pool import db_manager
from .utils import add_namespace_prefix

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


class CategoryRepository:
    """Handles all database interactions related to Wikipedia categories."""

    @staticmethod
    def fetch_arabic_titles_with_english_links(category_title: str) -> List[str]:
        """
        Fetch Arabic page titles that belong to a specific category
        and have an English language link.
        """
        try:
            rows = db_manager.execute_query(wiki="ar", query=_ARCAT_QUERY, params=(category_title,))

            titles = [
                add_namespace_prefix(row["page_title"].replace(" ", "_"), row["page_namespace"], lang="ar")
                for row in rows
            ]
            return titles
        except Exception as e:
            logger.error("Failed to fetch Arabic titles for category '%s': %s", category_title, e)
            return []

    @staticmethod
    def fetch_english_titles_with_arabic_links(category_title: str) -> List[str]:
        """
        Fetch English language links (ll_title) for pages in a specific
        English category.
        """
        try:
            rows = db_manager.execute_query(wiki="enwiki", query=_ENCAT_QUERY, params=(category_title,))

            titles = sorted(row["ll_title"] for row in rows)
            logger.debug("Fetched %d English titles for category '%s'", len(titles), category_title)
            return titles
        except Exception as e:
            logger.error("Failed to fetch English titles for category '%s': %s", category_title, e)
            return []
