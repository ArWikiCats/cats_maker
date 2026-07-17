#!/usr/bin/python3
"""Pure SQL query functions for the module."""

from __future__ import annotations

import logging
from typing import Any

from ....config import main_settings
from ...api_sql import add_namespace_prefix, db_manager

logger = logging.getLogger(__name__)


def fetch_ar_category_members(ar_cat: str) -> list[dict[str, Any]]:
    """Return raw rows for members of an Arabic category."""
    ar_cat2 = ar_cat.replace(" ", "_").replace("تصنيف:", "")

    query = """
    SELECT page_title, page_namespace
        FROM page
        JOIN categorylinks ON cl_from = page_id
        JOIN linktarget ON cl_target_id = lt_id
        WHERE lt_title = %s
        AND lt_namespace = 14
    """

    try:
        return db_manager.execute_query(wiki="arwiki", query=query, params=(ar_cat2,))
    except Exception as e:
        logger.error(f"SQL error in fetch_ar_category_members: {e}")
        return []


def fetch_en_category_langlinks(encat: str, wiki: str = "en") -> list[dict[str, Any]]:
    """Return raw rows for Arabic langlinks of pages in an EN/FR category."""
    encat2 = encat.replace(" ", "_").replace("Category:", "").replace("category:", "")

    nss = "0, 10, 14"
    if main_settings.query.ns_no_10:
        nss = "0, 14"
    if main_settings.query.ns_only_14:
        nss = "14"

    # nss is validated against known safe values above
    query = f"""
        SELECT DISTINCT ll_title
            FROM page p1
            JOIN categorylinks cla ON cla.cl_from = p1.page_id
            JOIN linktarget lt ON cla.cl_target_id = lt.lt_id
            JOIN langlinks ON p1.page_id = ll_from
            WHERE p1.page_namespace IN ({nss})
            AND lt.lt_namespace = 14
            AND lt.lt_title = %s
            AND ll_lang = 'ar'
    """

    try:
        return db_manager.execute_query(wiki=f"{wiki}wiki", query=query, params=(encat2,))
    except Exception as e:
        logger.error(f"SQL error in fetch_en_category_langlinks: {e}")
        return []


def fetch_dont_add_pages() -> list[str]:
    """Return pages tagged with 'لا_للتصنيف_المعادل'."""
    query = """
        SELECT page_title, page_namespace
        FROM page, templatelinks, linktarget
        WHERE page_id = tl_from
        AND page_namespace IN (0, 10)
        AND tl_target_id = lt_id
        AND lt_namespace = 10
        AND lt_title = "لا_للتصنيف_المعادل"
    """

    try:
        rows = db_manager.execute_query(wiki="ar", query=query)
        return [add_namespace_prefix(r["page_title"], r["page_namespace"], lang="ar") for r in rows]
    except Exception as e:
        logger.error(f"SQL error in fetch_dont_add_pages: {e}")
        return []
