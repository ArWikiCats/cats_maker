"""Category comparison logic between English and Arabic Wikipedias."""

import logging
import re

from ..helps import function_timer
from .service import GET_SQL, add_nstext_to_title, sql_new

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

_ARCAT_QUERY = """
    SELECT page_title, page_namespace
    FROM page
    JOIN categorylinks
    JOIN linktarget ON cl_target_id = lt_id
    JOIN langlinks
    WHERE lt_title = %s
      AND lt_namespace = 14
      AND cl_from = page_id
      AND page_id = ll_from
      AND ll_lang = 'en'
    GROUP BY page_title
"""

_ENCAT_QUERY = """
    SELECT ll_title, page_namespace
    FROM page
    JOIN categorylinks
    JOIN linktarget ON cl_target_id = lt_id
    JOIN langlinks
    WHERE lt_title = %s
      AND lt_namespace = 14
      AND cl_from = page_id
      AND page_id = ll_from
      AND ll_lang = 'ar'
    GROUP BY ll_title
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalise_category_title(title: str, prefix_pattern: str) -> str:
    """Strip a category prefix and normalise spaces to underscores."""
    if not title:
        return title
    title = re.sub(prefix_pattern, "", title, flags=re.IGNORECASE)
    return title.replace(" ", "_")


# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------


@function_timer
def _fetch_ar_titles(ar_category: str) -> list[str]:
    """Return Arabic-wiki page titles that are in *ar_category* and have an en langlink."""
    title = _normalise_category_title(ar_category, r"تصنيف:")
    if not title:
        return []

    rows = sql_new(_ARCAT_QUERY, wiki="ar", values=(title,))
    return [add_nstext_to_title(row["page_title"].replace(" ", "_"), row["page_namespace"], lang="ar") for row in rows]


@function_timer
def _fetch_en_titles(en_category: str) -> list[str]:
    """Return Arabic ll_titles for pages in *en_category* on English Wikipedia."""
    title = _normalise_category_title(
        en_category,
        r"(\[\[en:)|(category:)|(]])",  # strips [[en: … ]] or Category: prefixes
    )
    if not title:
        return []

    rows = sql_new(_ENCAT_QUERY, wiki="enwiki", values=(title,))
    titles = sorted(row["ll_title"] for row in rows)
    logger.debug("_fetch_en_titles: %d titles for '%s'", len(titles), title)
    return titles


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@function_timer
def get_exclusive_category_titles(en_category: str, ar_category: str) -> list[str]:
    """Return en-wiki titles that are in *en_category* but absent from *ar_category*.

    Both arguments are category names (with or without their namespace prefix).
    Returns [] when SQL is not available (non-production environment).
    """
    if not GET_SQL():
        return []

    en_titles = _fetch_en_titles(en_category)
    ar_titles = _fetch_ar_titles(ar_category)

    logger.debug(
        "get_exclusive_category_titles: en=%d ar=%d for en_cat='%s'",
        len(en_titles),
        len(ar_titles),
        en_category,
    )

    exclusive = [t for t in en_titles if t not in ar_titles]
    logger.info("get_exclusive_category_titles: %d exclusive titles", len(exclusive))
    return exclusive


__all__ = ["get_exclusive_category_titles"]
