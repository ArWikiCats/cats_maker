""" """

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ApiFormatData:
    def extract_template_titles(self, templates: list[dict[str, Any]]) -> list[str]:
        # templates has same format in both formatversion 1 and 2
        # "templates": [{ "ns": 10, "title": "قالب:-" }]
        return [x["title"] for x in templates]

    def extract_category_map(
        self,
        categories_data: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        # Categories data has differ format in both formatversion 1 and 2
        # V1: { "ns": 14, "title": "تصنيف:hidden", "hidden": "" }, { "ns": 14, "title": "تصنيف:not_hidden", "sortkey": "d8b7", "sortkeyprefix": ""}
        # V2: { "ns": 14, "title": "تصنيف:hidden", "hidden": true }, { "ns": 14, "title": "تصنيف:not_hidden", "hidden": false }

        def set_is_hidden(cat_data: dict[str, Any]) -> dict[str, Any]:
            if cat_data.get("hidden") in ("", True):
                cat_data["hidden"] = True
            else:
                cat_data["hidden"] = False
            return cat_data

        return {cat["title"]: set_is_hidden(cat) for cat in categories_data}

    def map_langlinks_to_titles(self, page_langlinks: list[dict[str, Any]]):
        # langlinks has differ format in both formatversion 1 and 2
        # V1: "langlinks": [{ "lang": "en", "*": "Category:Yemen" }],
        # V2: "langlinks": [{ "lang": "en", "title": "Category:Yemen" }],
        return {langlink["lang"]: langlink.get("*") or langlink["title"] for langlink in page_langlinks}


__all__ = [
    "ApiFormatData",
]
