#!/usr/bin/python3
"""Category resolver — merges sql_cat.py + cat_tools_enlist2.py logic."""

from __future__ import annotations

import logging

from .....config import main_settings
from .....config.constants import DEFAULT_MEMBER_NAMESPACES
from .....shared import AllAPIS
from ...utils.text import normalize_category_title
from ..sql.ar_lists import ArCategorySQL
from ..sql.en_lists import EnCategorySQL
from .category_generator import fetch_category_members
from .langlinks import LangLinksClient, get_arpage_inside_encat

logger = logging.getLogger(__name__)


class CategoryResolver:
    """Resolve category members across wikis via SQL or API."""

    def __init__(
        self,
        backend: str = "auto",
        wiki_query_service: ArCategorySQL | None = None,
        wiki_api_handler: LangLinksClient | None = None,
        en_wiki_query_service: EnCategorySQL | None = None,
    ) -> None:
        self.wiki_api_handler = wiki_api_handler or LangLinksClient()
        self.en_wiki_query_service = en_wiki_query_service or EnCategorySQL()
        self.wiki_query_service = wiki_query_service or ArCategorySQL()
        self.backend = backend

    def _use_sql(self) -> bool:
        if self.backend == "sql":
            return True

        if self.backend == "api":
            return False
        return main_settings.database.use_sql

    def list_ar_pages_in_cat(self, ar_title: str) -> list[str]:
        """
        Return all page titles inside an Arabic category."""
        ar_list: list[str] = []

        if self._use_sql():
            ar_list = self.wiki_query_service.sql_retrieve_category_members_list(ar_title)

        if not ar_list:
            api = AllAPIS.load("ar")
            cat_members = api.catdepth("Category:" + ar_title, depth=0, ns="all")
            ar_list = list(cat_members.keys())

        logger.info(f"length ar_list:{len(ar_list)}")
        return ar_list

    def list_en_pages_with_ar_links(self, encat: str, wiki: str = "en") -> list[str]:
        """
        Return Arabic page titles linked from pages in an EN/FR category."""
        en_list: list[str] = []

        if self._use_sql():
            en_list = self.en_wiki_query_service.fetch_arabic_titles_from_en_category(encat, site_code=wiki)

        if not en_list:
            en_list = self._fetch_ar_titles_based_on_en_category(encat, wiki=wiki)

        return [x.replace("_", " ") for x in en_list]

    def diff_missing_ar_pages(self, en_title: str, ar_title: str, wiki: str = "en") -> list[str]:
        """
        Return Arabic pages present in EN category but missing from AR category."""
        ar_list = self.list_ar_pages_in_cat(ar_title)
        en_list = self.list_en_pages_with_ar_links(en_title, wiki=wiki)
        missing = [x for x in en_list if x not in ar_list]
        logger.info(f"length missing ar pages:{len(missing)}")
        return missing

    def resolve_members(self, en_title: str, ar_title: str, wiki: str = "en") -> list[str]:
        """
        High-level resolver: normalise inputs and return missing pages."""
        en_title = normalize_category_title(en_title, lang=wiki)
        ar_title = normalize_category_title(ar_title, lang="ar")
        return self.diff_missing_ar_pages(en_title, ar_title, wiki=wiki)

    # --- API-based helpers (formerly MakeLitApiWay / cat_tools_enlist2) ---

    def _fetch_ar_titles_based_on_en_category(self, enpage_title: str, wiki: str = "en") -> list[str]:
        """
        Fallback: use API to find Arabic titles for EN category members."""
        en_titles = self._en_category_members(enpage_title, wiki=wiki)
        return self._translate_titles_to_ar(en_titles, wiki=wiki)

    def _en_category_members(self, enpage_title: str, wiki: str = "en") -> list[str]:
        logger.info(f"from category: {enpage_title}")
        namespace_ids = list(DEFAULT_MEMBER_NAMESPACES)
        api = AllAPIS.load(wiki)
        cat_members = api.catdepth(enpage_title, depth=0, ns="all", without_lang="", with_lang="ar", tempyes=[])
        return [title for title, info in cat_members.items() if int(info["ns"]) in namespace_ids]

    def _translate_titles_to_ar(self, titles: list[str], wiki: str = "en", batch_size: int = 50) -> list[str]:
        """
        Batch-translate page titles from source wiki to Arabic via langlinks."""
        new_ar_list: list[str] = []

        sito_code = main_settings.en_site.code
        if wiki == "fr":
            sito_code = main_settings.fr_site.code

        for i in range(0, len(titles), batch_size):
            batch = titles[i : i + batch_size]
            part_list = "|".join(batch)
            part_list = part_list.removeprefix("|")

            result = self.wiki_api_handler.find_page_data(
                part_list,
                prop="langlinks",
                language_link_target="ar",
                site_code=sito_code,
            )
            if not result:
                continue

            for p_w, data in result.items():
                if "langlinks" in data and "ar" in data["langlinks"]:
                    ar_title = data["langlinks"]["ar"]
                    logger.debug(f"Adding {ar_title} to ar lists {p_w}")
                    new_ar_list.append(ar_title)

        logger.info(f"length of new_ar_list:{len(new_ar_list)}")
        return new_ar_list

    def make_lit_api_way(self, encat: str, item_type: str = "cat") -> list[str]:
        """
        Generate a list of Arabic page titles based on the provided EN category.

        This is the refactored ``MakeLitApiWay``.
        """
        if not encat:
            logger.info("No encat")
            return []

        logger.info("* MakeLit ApiWay: ")
        encat_clean = normalize_category_title(encat, lang="en")

        titles = fetch_category_members(title=encat_clean, wiki="en", namespaces=[0, 14, 10, 100])

        cached_titles = get_arpage_inside_encat("Category:" + encat_clean)
        if cached_titles:
            titles.extend([x.replace("_", " ") for x in cached_titles])
            logger.info("arpage inside_encat: " + (", ".join(cached_titles)))

        listen_page_title: list[str] = []
        logger.info(f" MakeLitApi: Way length : {len(titles)}")

        for i in range(0, len(titles), 50):
            batch = titles[i : i + 50]
            joined = "|".join(batch)

            gent_sasa = self.wiki_api_handler.find_page_data(
                joined,
                prop="langlinks",
                site_code=main_settings.en_site.code,
            )
            if not gent_sasa:
                continue

            for p_w, data in gent_sasa.items():
                if "langlinks" in data and "ar" in data["langlinks"]:
                    arpagetitle = data["langlinks"]["ar"]
                    logger.debug(f'find "{p_w}" page_work in gent_sasa arpagetitle: {arpagetitle}')
                    listen_page_title.append(arpagetitle)

        return listen_page_title


__all__ = [
    "CategoryResolver",
]
