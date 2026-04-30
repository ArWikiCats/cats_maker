#!/usr/bin/python3
"""Category generator — merged from cat_tools2 + ar_from_en2."""

from __future__ import annotations

import logging

from ....config import settings
from ...client_wiki import load_main_api
from ...wiki_api import find_LCN
from ..constants import DEFAULT_MEMBER_NAMESPACES, STUB_MEMBER_NAMESPACES

logger = logging.getLogger(__name__)


def _get_namespace_ids() -> list[int]:
    if settings.category.stubs:
        return list(STUB_MEMBER_NAMESPACES)
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

    api = load_main_api(wiki)
    cat_member = api.CatDepth(title, depth=0, ns=ns_str, with_lang="ar")

    return [title.replace("_", " ") for title, info in cat_member.items() if int(info["ns"]) in namespaces]


def translate_titles_to_ar(titles: list[str], source_wiki: str = "en", batch_size: int = 50) -> list[str]:
    """Batch-translate page titles from source_wiki to Arabic via langlinks.

    Args:
        titles: List of page titles to translate.
        source_wiki: Source wiki code ("en" or "fr").
        batch_size: Number of titles per API call.
    """
    new_ar_list: list[str] = []

    sito_code = settings.EEn_site.code
    if source_wiki == "fr":
        sito_code = settings.FR_site.code

    for i in range(0, len(titles), batch_size):
        batch = titles[i : i + batch_size]
        part_list = "|".join(batch)
        if part_list.startswith("|"):
            part_list = part_list[1:]

        result = find_LCN(part_list, prop="langlinks", lllang="ar", first_site_code=sito_code)
        if not result:
            continue

        for p_w, data in result.items():
            if "langlinks" in data and "ar" in data["langlinks"]:
                ar_title = data["langlinks"]["ar"]
                logger.debug(f"<<lightblue>>Adding {ar_title} to ar lists {p_w}")
                new_ar_list.append(ar_title)

    logger.info(f"<<lightyellow>> length of new_ar_list:{len(new_ar_list)}")
    return new_ar_list
