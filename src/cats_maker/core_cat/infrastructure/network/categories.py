from __future__ import annotations

import logging
from typing import Any

from ....shared import AllAPIS
from .api_formatter import ApiFormatData

logger = logging.getLogger(__name__)


class CategoryMembersClient(ApiFormatData):
    """
    Client for retrieving category members and subcategories.
    """

    def __init__(
        self,
        valid_namespace_ids: list[int] | None = None,
    ) -> None:
        self._call_count = 0
        self.valid_namespace_ids = valid_namespace_ids or [0, 14, 10, 100]

    def client_request_safe_main_api(
        self,
        params: dict[str, Any],
        code: str,
        family: str = "wikipedia",
    ) -> dict[str, Any]:
        api = AllAPIS.load(code, family)
        data = api.client_request_safe(params) or {}
        return data

    def retrieve_category_members_list(
        self,
        title: str,
        site_code: str,
        ctype: str = "",
        language_link_target: str = "",
    ) -> list[str]:
        """
        Retrieve category members and/or subcategories.
        """
        if not title:
            return []

        # find categorymembers and subcategories of category

        self._call_count += 1
        logger.info(f"<<lightblue>> CategoryMembersClient call #{self._call_count} → {site_code}:{title}")

        params: dict[str, Any] = {
            "action": "query",
            "format": "json",
            "prop": "langlinks",
            "titles": title,
            "generator": "categorymembers",
            "utf8": 1,
            # "lllang": lllang,
            "lllimit": "max",
            "gcmtitle": title,
            "gcmprop": "title",
            "gcmtype": "page|subcat",
            "gcmlimit": "max",
            "formatversion": 2,
        }
        if language_link_target:
            params["lllang"] = language_link_target

        if ctype in {"subcat", "page"}:
            params["gcmtype"] = ctype

        data = self.client_request_safe_main_api(params, site_code, "wikipedia")

        pages = data.get("query", {}).get("pages", [])

        result = [page_data["title"] for page_data in pages]

        return result

    def retrieve_category_members_with_langlinks(
        self,
        title: str,
        site_code: str,
        ctype: str = "",
        language_link_target: str = "",
    ) -> dict[str, dict[str, Any]]:
        """
        Retrieve category members and/or subcategories.

        Parameters
        ----------
        title : str
            Category title (e.g. "Category:Physics" or "تصنيف:فيزياء")
        site_code : str
            Source site code ("en", "ar", ...)
        ctype : str
            "subcat" → only subcategories
            "page"   → only pages
            ""       → both (default)
        """
        if not title:
            return {}

        # find categorymembers and subcategories of category
        # depth 0

        self._call_count += 1
        logger.info(f"<<lightblue>> CategoryMembersClient call #{self._call_count} → {site_code}:{title}")

        params: dict[str, Any] = {
            "action": "query",
            "format": "json",
            "prop": "langlinks",
            "titles": title,
            "generator": "categorymembers",
            "utf8": 1,
            "lllimit": "max",
            "gcmtitle": title,
            "gcmprop": "title",
            "gcmtype": "page|subcat",
            "gcmlimit": "max",
            "formatversion": 2,
        }
        if language_link_target:
            params["lllang"] = language_link_target

        if ctype in {"subcat", "page"}:
            params["gcmtype"] = ctype

        data = self.client_request_safe_main_api(params, site_code, "wikipedia")

        tablemember: dict[str, dict[str, Any]] = {}

        pages = data.get("query", {}).get("pages", [])

        for page_data in pages:
            cat_title = page_data["title"]
            entry: dict[str, Any] = {"langlinks": {}}

            logger.debug(f"cate_title: {cat_title}")

            if "ns" in page_data:
                entry["ns"] = page_data["ns"]

            entry["langlinks"] = self.map_langlinks_to_titles(page_data.get("langlinks", []))

            tablemember[cat_title] = entry

        return tablemember


__all__ = [
    "CategoryMembersClient",
]
