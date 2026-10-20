#!/usr/bin/python3
"""Pure SQL query functions for the module."""

from __future__ import annotations

import logging

from .....config.constants import EN_FALSE_TEMPLATES
from ...new_config import C18Config
from ..wrapper import SharedWrapper
from .base import ReplicaClient

logger = logging.getLogger(__name__)


class EnCategorySQL:
    """
    SQL operations related to English categories.
    """

    def __init__(
        self,
        client: ReplicaClient | None = None,
        wrapper: SharedWrapper | None = None,
        *,
        config: C18Config | None = None,
    ) -> None:
        self.wrapper = wrapper or SharedWrapper()
        self.config = config or self.wrapper.config
        self.client = client or ReplicaClient("enwiki", wrapper=self.wrapper)
        self.use_sql = self.config.use_sql and self.wrapper.can_use_sql()

        self.sql_ns_filter = self.config.sql_ns_filter

    def fetch_arabic_titles_from_en_category(
        self,
        encat_title: str,
        site_code: str = "en",
    ) -> list[str]:
        """
        Return Arabic titles of pages that are in the given English category
        and have an Arabic language link.
        """
        if not self.use_sql:
            return []

        encat2 = self.remove_category_prefix(encat_title.replace(" ", "_"))

        if not encat2:
            logger.info(f"sql → ({encat_title}) is not a valid category")
            return []

        # nss is validated against known safe values above
        query = f"""
            SELECT DISTINCT
                ll_title
            FROM
                page p1
                JOIN categorylinks cla ON cla.cl_from = p1.page_id
                JOIN linktarget lt ON cla.cl_target_id = lt.lt_id
                JOIN langlinks ON p1.page_id = ll_from
            WHERE
                lt.lt_title = %s
                AND lt.lt_namespace = 14
                AND ll_lang = 'ar'
                AND p1.page_namespace IN ({self.sql_ns_filter})
            GROUP BY
                ll_title
        """
        client = self.client
        if site_code != self.client.dbname:
            client = ReplicaClient(f"{site_code}wiki", wrapper=self.wrapper)

        rows = client.select(query, [encat2])
        result = [row["ll_title"].replace("_", " ") for row in rows if row.get("ll_title")]

        logger.info(f"sql → ({encat_title}) returned {len(result)} titles")
        return list(dict.fromkeys(result))  # unique preserve order

    def get_categories_like(
        self,
        pattern: str,
        limit: int | str = 600,
        offset: int | str = 0,
    ) -> list[str]:
        """
        Find English categories that match a pattern and meet several
        business rules (no Arabic link, not false templates, etc.).

        Equivalent to the old `get_en_categories_like`.
        """
        logger.info(f"<<lightred>> sql . get_en_categories_like {pattern}")
        if not self.use_sql or not pattern.strip():
            return []

        pattern = pattern.replace(" ", "_")
        params: list = [f"%{pattern}%", f"%{pattern}", "CS1_%"]

        limit = int(limit)
        offset = int(offset)

        false_params, false_placeholders = self.get_false_template_params()

        params.extend(false_params)
        params.append(limit)

        offset_sql = ""
        if offset > 0:
            offset_sql = "OFFSET %s"
            params.append(offset)

        query = f"""
            SELECT CONCAT('Category:', p.page_title) AS category_title
            FROM page p
            WHERE p.page_namespace = 14
              AND (p.page_title LIKE %s OR p.page_title LIKE %s)
              AND p.page_title NOT LIKE %s
              AND p.page_id NOT IN (
                  SELECT ll_from
                  FROM langlinks
                  WHERE ll_lang = 'ar'
              )
              AND p.page_id NOT IN (
                  SELECT tl_from
                  FROM templatelinks
                  JOIN linktarget ON lt_id = tl_target_id
                  WHERE lt_namespace = 10
                    AND lt_title IN ({false_placeholders})
              )
              AND p.page_title IN (
                  SELECT DISTINCT linktarget.lt_title
                  FROM page p1
                  JOIN categorylinks cla ON cla.cl_from = p1.page_id
                  JOIN linktarget ON cla.cl_target_id = linktarget.lt_id
                  JOIN langlinks ON p1.page_id = ll_from
                  WHERE p1.page_namespace IN ({self.sql_ns_filter})
                    AND ll_lang = 'ar'
                    AND linktarget.lt_title = p.page_title
                    AND linktarget.lt_namespace = 14
              )
            GROUP BY p.page_title
            LIMIT %s
            {offset_sql}
        """

        logger.debug(f"Executing get_categories_like with pattern: {pattern}")
        rows = self.client.select(query, params)

        result = [row["category_title"].replace("_", " ") for row in rows]

        logger.info(f"<<lightgreen>> get_categories_like('{pattern}') → {len(result)} categories")
        return result

    def get_false_template_params(self) -> tuple[list[str], str]:
        false_params = [x.replace(" ", "_") for x in EN_FALSE_TEMPLATES]
        false_placeholders = ", ".join(["%s"] * len(false_params)) if false_params else "''"
        return false_params, false_placeholders

    def make_24_cat(self, sql_limit: int = 500) -> list[str]:
        if not self.use_sql:
            return []

        false_params, false_placeholders = self.get_false_template_params()

        query = f"""
            select /* SLOW_OK */
            concat('Category:', rc_title) AS title
            from recentchanges
            join page
            on rc_cur_id=page_id
            where rc_namespace=14
            and rc_source = "mw.new"
            and page_id not in (
                select tl_from from templatelinks, linktarget
                where lt_namespace = 10 and tl_target_id = lt_id and lt_title in ({false_placeholders})
            )
            and rc_deleted=0
            and rc_title not like %s
            and DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 2 DAY)<rc_timestamp

            limit %s
        """
        params: list = false_params
        params.append("%Wikipedia%")
        params.append(sql_limit)

        rows = self.client.select(query, params)

        result = [row["title"].replace("_", " ") for row in rows]

        logger.info(f" result: {len(result):,}")

        return result

    def remove_category_prefix(self, title: str) -> str:
        title = (
            title.replace("[[", "")
            .replace("]]", "")
            .removeprefix("Category:")
            .removeprefix("category:")
            .removeprefix("Category talk:")
            .removeprefix("category talk:")
            .strip()
        )
        return title


__all__ = [
    "EnCategorySQL",
]
