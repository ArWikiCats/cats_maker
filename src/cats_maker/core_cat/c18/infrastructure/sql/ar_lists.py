from __future__ import annotations

import logging

from .....shared.namespace_handler import NamespaceHandler
from ..wrapper import SharedWrapper
from .base import ReplicaClient

logger = logging.getLogger(__name__)


class ArCategorySQL:
    """
    SQL operations related to Arabic categories and
    cross-language (English → Arabic) category membership.
    """

    def __init__(
        self,
        client: ReplicaClient | None = None,
        wrapper: SharedWrapper | None = None,
        *,
        ar_ns_handler: NamespaceHandler | None = None,
    ) -> None:
        self.wrapper = wrapper or SharedWrapper()
        self.client = client or ReplicaClient(dbname="arwiki", wrapper=self.wrapper)
        self.can_use_sql = self.wrapper.can_use_sql() and self.config.use_sql
        self.ar_ns_handler = ar_ns_handler or NamespaceHandler.load("ar")

    def fetch_dont_add_pages(self) -> list[str]:
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

        if not self.can_use_sql:
            return []

        rows = self.client.select(query)
        result = []

        for row in rows:
            title = row["page_title"]
            ns = str(row["page_namespace"])
            title = self.ar_ns_handler.get_full_title(title.replace("_", " "), ns)
            result.append(title)

        logger.info(f"<<lightgreen>> length ar_list: {len(result)}")
        return result

    def sql_retrieve_category_members_list(self, ar_cat: str) -> list[str]:
        """
        Return all pages that belong to the given Arabic category.
        """
        if not self.can_use_sql:
            return []

        ar_cat2 = self.remove_category_prefix(ar_cat)

        query = """
            SELECT
                page_title,
                page_namespace
            FROM
                page
                JOIN categorylinks ON cl_from = page_id
                JOIN linktarget ON cl_target_id = lt_id
            WHERE
                lt_title = %s
                AND lt_namespace = 14
        """

        rows = self.client.select(query, [ar_cat2.replace(" ", "_")])
        result = []

        for row in rows:
            title = row["page_title"]
            ns = str(row["page_namespace"])
            title = self.ar_ns_handler.get_full_title(title, ns)
            result.append(title.replace("_", " "))

        logger.info(f"<<lightgreen>> length ar_list: {len(result)}")
        return result

    def remove_category_prefix(self, title: str) -> str:
        title = (
            title.strip()
            .replace("[[", "")
            .replace("]]", "")
            .removeprefix("تصنيف:")
            .removeprefix("نقاش التصنيف:")
            .strip()
        )
        return title


__all__ = [
    "ArCategorySQL",
]
