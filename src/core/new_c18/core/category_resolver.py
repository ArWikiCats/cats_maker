#!/usr/bin/python3
"""Category resolver — merges sql_cat.py + cat_tools_enlist2.py logic."""

from __future__ import annotations

import logging

from ....config import settings
from ...api_sql import add_namespace_prefix
from ...cats_helpers import Categorized_Page_Generator
from ...client_wiki import load_main_api
from ...wiki_api import find_LCN, get_arpage_inside_encat
from ..constants import DEFAULT_MEMBER_NAMESPACES
from ..io.sql_queries import fetch_ar_category_members, fetch_en_category_langlinks
from ..utils.text import normalize_category_title

logger = logging.getLogger(__name__)


class CategoryResolver:
    """Resolve category members across wikis via SQL or API."""

    def __init__(self, backend: str = "auto") -> None:
        self.backend = backend

    def _use_sql(self) -> bool:
        if self.backend == "sql":
            return True
        if self.backend == "api":
            return False
        return settings.database.use_sql

    def list_ar_pages_in_cat(self, ar_title: str) -> list[str]:
        """Return all page titles inside an Arabic category."""
        ar_list: list[str] = []

        if self._use_sql():
            rows = fetch_ar_category_members(ar_title)

            ar_list = [add_namespace_prefix(r["page_title"], r["page_namespace"], lang="ar") for r in rows]

        if not ar_list:
            api = load_main_api("ar")
            cat_members = api.CatDepth("Category:" + ar_title, depth=0, ns="all")
            ar_list = list(cat_members.keys())

        logger.info(f"<<lightgreen>> length ar_list:{len(ar_list)}")
        return ar_list

    def list_en_pages_with_ar_links(self, encat: str, wiki: str = "en") -> list[str]:
        """Return Arabic page titles linked from pages in an EN/FR category."""
        en_list: list[str] = []

        if self._use_sql():
            rows = fetch_en_category_langlinks(encat, wiki=wiki)
            en_list = [x.get("ll_title") for x in rows if x.get("ll_title")]

        if not en_list:
            en_list = self._fetch_ar_titles_based_on_en_category(encat, wiki=wiki)

        return [x.replace("_", " ") for x in en_list]

    def diff_missing_ar_pages(self, en_title: str, ar_title: str, wiki: str = "en") -> list[str]:
        """Return Arabic pages present in EN category but missing from AR category."""
        ar_list = self.list_ar_pages_in_cat(ar_title)
        en_list = self.list_en_pages_with_ar_links(en_title, wiki=wiki)
        missing = [x for x in en_list if x not in ar_list]
        logger.info(f"<<lightgreen>> length missing ar pages:{len(missing)}")
        return missing

    def resolve_members(self, en_title: str, ar_title: str, wiki: str = "en") -> list[str]:
        """High-level resolver: normalise inputs and return missing pages."""
        en_title = normalize_category_title(en_title, lang=wiki)
        ar_title = normalize_category_title(ar_title, lang="ar")
        return self.diff_missing_ar_pages(en_title, ar_title, wiki=wiki)

    # --- API-based helpers (formerly MakeLitApiWay / cat_tools_enlist2) ---

    def _fetch_ar_titles_based_on_en_category(self, enpage_title: str, wiki: str = "en") -> list[str]:
        """Fallback: use API to find Arabic titles for EN category members."""
        en_titles = self._en_category_members(enpage_title, wiki=wiki)
        return self._translate_titles_to_ar(en_titles, wiki=wiki)

    def _en_category_members(self, enpage_title: str, wiki: str = "en") -> list[str]:
        logger.info(f"<<lightyellow>> from category: {enpage_title}")
        namespace_ids = list(DEFAULT_MEMBER_NAMESPACES)
        api = load_main_api(wiki)
        cat_members = api.CatDepth(enpage_title, depth=0, ns="all", without_lang="", with_lang="ar", tempyes=[])
        return [title for title, info in cat_members.items() if int(info["ns"]) in namespace_ids]

    def _translate_titles_to_ar(self, titles: list[str], wiki: str = "en", batch_size: int = 50) -> list[str]:
        """Batch-translate page titles from source wiki to Arabic via langlinks."""
        new_ar_list: list[str] = []

        sito_code = settings.EEn_site.code
        if wiki == "fr":
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

    def make_lit_api_way(self, encat: str, item_type: str = "cat") -> list[str]:
        """Generate a list of Arabic page titles based on the provided EN category.

        This is the refactored ``MakeLitApiWay``.
        """
        if not encat:
            logger.info("<<lightblue>> No encat")
            return []

        logger.info("<<lightgreen>>* MakeLit ApiWay: ")
        encat_clean = normalize_category_title(encat, lang="en")

        member_type = "cat" if item_type == "cat" else item_type
        gent_faso_list = Categorized_Page_Generator(encat_clean, member_type)

        uux = get_arpage_inside_encat("Category:" + encat_clean)
        if uux:
            logger.info("arpage inside_encat: " + (", ".join(uux)))
            for x in uux:
                gent_faso_list.append(x.replace("_", " "))

        listen_page_title: list[str] = []
        logger.info(f" MakeLitApi: Way length : {len(gent_faso_list)}")

        for i in range(0, len(gent_faso_list), 50):
            batch = gent_faso_list[i : i + 50]
            joined = "|".join(batch)

            gent_sasa = find_LCN(joined, prop="langlinks", first_site_code=settings.EEn_site.code)
            if not gent_sasa:
                continue

            for p_w, data in gent_sasa.items():
                if "langlinks" in data and "ar" in data["langlinks"]:
                    arpagetitle = data["langlinks"]["ar"]
                    logger.debug(f'find "{p_w}" page_work in gent_sasa arpagetitle: {arpagetitle}')
                    listen_page_title.append(arpagetitle)

        return listen_page_title
