""" """

from ..api_sql.constants import NS_TEXT_AR

CATEGORY_PREFIXES: dict[str, str] = {
    "ar": "تصنيف:",
    "en": "Category:",
    "www": "Category:",
}

NS_LIST = NS_TEXT_AR

__all__ = [
    "CATEGORY_PREFIXES",
    "NS_LIST",
    "NS_TEXT_AR",
]
