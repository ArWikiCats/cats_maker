#!/usr/bin/python3
"""Category generator — merged from cat_tools2 + ar_from_en2."""

from __future__ import annotations

import logging

from .....shared import AllAPIS
from ...config.constants import DEFAULT_MEMBER_NAMESPACES

logger = logging.getLogger(__name__)


def _get_namespace_ids() -> list[int]:
    return list(DEFAULT_MEMBER_NAMESPACES)


def fetch_category_members(title: str, wiki: str = "en", namespaces: list[int] | None = None) -> list[str]:
    """Fetch category members from any source wiki.

    Args:
        title: Category title (with or without prefix).
        wiki: Source wiki code.
        namespaces: Optional namespace filter.
    """
    if namespaces is None:
        namespaces = _get_namespace_ids()

    ns_str = "all"
    if namespaces == [14]:
        ns_str = "14"

    api = AllAPIS.load(wiki)
    cat_member = api.catdepth(title, depth=0, ns=ns_str, with_lang="ar")

    return [title.replace("_", " ") for title, info in cat_member.items() if int(info["ns"]) in namespaces]


__all__ = [
    "fetch_category_members",
]
