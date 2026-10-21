import logging
from collections.abc import Callable

from ..core_cat.lists.category_resolver import CategoryResolver
from ..core_cat.lists.category_validator import validate_categories_for_new_cat
from ..config import Settings
from ..core_cat.c18.infrastructure.network.langlinks import LangLinksClient
from ..core_cat.lists.members_helper import collect_category_members
from ..shared.newapi import AllAPIS
from ..shared.wd_clients.wd_api import add_labels, get_sitelinks_from_wikidata, log_to_wikidata, log_to_wikidata_qid
from .add_bot import add_to_page
from .create_category_page import new_category
from .utils import check_en_temps
from .labels_creator import ar_make_lab
from .mknew_state import CategoryManagerStats

# TODO: move it to the settings file!
WIKI_SITE_AR = {"family": "wikipedia", "code": "ar"}
WIKI_SITE_EN = {"family": "wikipedia", "code": "en"}

logger = logging.getLogger(__name__)


class CategoryManager:
    """Manages the creation and processing of Wikipedia categories."""

    def __init__(
        self,
        category_resolver: CategoryResolver | None = None,
        wiki_site_ar: dict | None = None,
        wiki_site_en: dict | None = None,
    ) -> None:
        self.category_resolver = category_resolver or CategoryResolver()
        self.wiki_site_ar = wiki_site_ar or WIKI_SITE_AR
        self.wiki_site_en = wiki_site_en or WIKI_SITE_EN

        self.stats = CategoryManagerStats()

    def _add_to_final_list(self, final_list: list, title: str, callback: Callable | None = None) -> None:
        title = title.replace("_", " ")

        if not title.startswith("تصنيف:"):
            title = f"تصنيف:{title}"

        if not final_list:
            return

        for n, page in enumerate(final_list, start=1):
            logger.info(f"cat:{title} page:{page} n:{n}/{len(final_list)}")
            save = add_to_page(page, title)
            if save and callback:
                try:
                    callback(title)
                except Exception as e:
                    logger.info(f"Error in callback: {e}")

    def _check_if_artitle_exists(self, test_title: str) -> bool:
        if not test_title.startswith("تصنيف:"):
            test_title = f"تصنيف:{test_title}"

        api = AllAPIS.load(self.wiki_site_ar["code"])
        page = api.mainpage(test_title)

        if page.exists():
            logger.debug(f"* category:{test_title} already exists in arwiki.")
            return False

        return True

    @staticmethod
    def _normalize_en_page_title(en_page_title: str) -> str:
        """Clean and normalize an English page title."""
        title = en_page_title.replace("[[", "").replace("]]", "").strip()
        return title.replace("_", " ")

    def _get_site_identifiers(self) -> tuple[str, str]:
        """Get the Arabic and English site identifiers based on wiki family."""
        ar_site_wiki = "arwiki"
        en_site_lang = self.wiki_site_en["code"]  # "en"

        if self.wiki_site_en["family"] != "wikipedia" and self.wiki_site_en["code"] != "commons":
            ar_site_wiki = f"ar{self.wiki_site_ar['family']}"
            en_site_lang = self.wiki_site_en["code"] + self.wiki_site_en["family"]

        return ar_site_wiki, en_site_lang

    def _check_wikidata_sitelink(self, en_site_lang: str, en_page_title: str, ar_site_wiki: str) -> tuple[bool, dict]:
        """Check if an Arabic sitelink exists in Wikidata."""
        ar_info = get_sitelinks_from_wikidata(en_site_lang, en_page_title) or {}

        if ar_info and ("sitelinks" in ar_info) and (ar_site_wiki in ar_info["sitelinks"]):
            ar_page = ar_info["sitelinks"][ar_site_wiki]
            logger.debug(f'found "{ar_site_wiki}" link "{ar_page}" for en cat.')
            return True, ar_info

        logger.debug(f'No "{ar_site_wiki}" link for en cat "{en_page_title}"')
        return False, ar_info

    def _extract_parent_categories(self, en_page_title: str) -> tuple[list, list]:
        """Extract parent categories for the English page."""
        cates = LangLinksClient(
            family=self.wiki_site_en["family"],
        ).find_page_categories_informations(
            en_page_title,
            prop="langlinks",
            site_code=self.wiki_site_en["code"],
        )

        en_cats_of_new_cat = []
        cats_of_new_cat = []

        if not cates:
            return en_cats_of_new_cat, cats_of_new_cat

        for cato in cates:
            if "ar" in cates[cato]:
                cats_of_new_cat.append(cates[cato]["ar"])
            else:
                en_cats_of_new_cat.append(cato)

        if en_cats_of_new_cat:
            logger.debug(f"en_cats_of_new_cat: {','.join(en_cats_of_new_cat)}")
        if cats_of_new_cat:
            logger.debug(f"cats_of_new_cat: {','.join(cats_of_new_cat)}")

        return en_cats_of_new_cat, cats_of_new_cat

    @staticmethod
    def _log_members_info(members: list) -> None:
        """Log information about collected members."""
        formatted_member_list = ""
        if members and len(members) < 30:
            formatted_member_list = ",".join(members)
        logger.debug(f"Add to {len(members)} pages: {formatted_member_list}")

    def _finalize_category_creation(
        self,
        ar_title: str,
        en_page_title: str,
        qid: str,
        members: list,
        en_cats_of_new_cat: list,
        callback: Callable | None,
    ) -> list:
        """Finalize category creation: add members, and log to Wikidata."""
        self._add_to_final_list(members, ar_title, callback=callback)

        if validate_categories_for_new_cat(ar_title, en_page_title, wiki="en"):
            listen = self.category_resolver.resolve_members(en_page_title, ar_title, wiki="en") or []
            if listen:
                self._add_to_final_list(listen, ar_title, callback=callback)

        if qid:
            log_to_wikidata_qid(ar_title, qid)
        else:
            log_to_wikidata(ar_title, en_page_title)

        return en_cats_of_new_cat

    def make_ar(self, en_page_title: str, ar_title: str, callback: Callable | None = None) -> list:
        """
        Create an Arabic category based on the English category.

        This function:
        1. Validates inputs and performs early exits
        2. Checks Wikidata sitelinks
        3. Collects category members (delegated to members_helper)
        4. Creates the category
        5. Logs and updates Wikidata

        Args:
            en_page_title: The English category page title
            ar_title: The Arabic category title
            callback: Optional callback function for progress updates

        Returns:
            list: English categories that don't have Arabic equivalents
        """
        # Validation: Check empty Arabic title
        if not ar_title.strip():
            logger.debug("ar_title is empty.")
            return []

        # Validation: Check if we've already processed this Arabic title
        if not self.stats._scan_ar_title(ar_title):
            logger.debug("_scan_ar_title failed.")
            return []

        # Normalize the English page title
        en_page_title = self._normalize_en_page_title(en_page_title)

        # Validation: Check if Arabic category already exists
        if not self._check_if_artitle_exists(ar_title):
            logger.debug("artitle already exists.")
            return []

        # Get site identifiers for Wikidata lookup
        ar_site_wiki, en_site_lang = self._get_site_identifiers()

        # Check Wikidata sitelinks - early exit if Arabic link exists
        has_ar_sitelink, ar_info = self._check_wikidata_sitelink(en_site_lang, en_page_title, ar_site_wiki)
        if has_ar_sitelink:
            return []

        qid = ar_info.get("q", "")

        # Extract parent categories
        en_cats_of_new_cat, cats_of_new_cat = self._extract_parent_categories(en_page_title)

        # Mark as already created
        self.stats.insert_already_created(en_page_title)

        # Collect category members using the helper module
        members = collect_category_members(ar_title, en_page_title)

        if not members:
            logger.debug("collect_category_members returned empty list")
            return []

        main_settings = Settings.get_instance()

        # Check minimum members requirement
        if len(members) < main_settings.category.min_members:
            logger.debug(
                f"Category has {len(members)} members, less than minimum required ({main_settings.category.min_members})"
            )
            return []

        self._log_members_info(members)

        # Create the category
        created_category = new_category(
            en_page_title, ar_title, cats_of_new_cat, qid, family=self.wiki_site_ar["family"]
        )

        if not created_category.success:
            add_labels(qid, ar_title, "ar")
            return en_cats_of_new_cat

        # Finalize: add members, log to Wikidata
        return self._finalize_category_creation(
            ar_title,
            en_page_title,
            qid,
            members,
            en_cats_of_new_cat,
            callback,
        )

    def one_cat(self, en_title: str, num: int, lenth: int, sugust: str = "", callback: Callable | None = None) -> bool:
        logger.debug("_________________________________________________________")
        logger.debug(f"{num}/{lenth} {en_title=}, {sugust=}")

        if not en_title.strip():
            logger.warning("en_title is empty. return")
            return False

        if self.stats.check_done_d(en_title):
            logger.warning(f'en_title:"{en_title}" in _done_d')
            return False

        self.stats.insert_done_d(en_title)
        labb = ar_make_lab(en_title)

        logger.debug(f"{num}/{lenth} {en_title=}, {sugust=}, {labb=}")

        labb = labb or sugust

        if not labb:
            logger.warning("%s ar label is empty.", en_title)
            return False

        if not check_en_temps(en_title):
            logger.warning("check_en_temps for %s failed.", en_title)
            return False

        en_list = self.category_resolver.list_en_pages_with_ar_links(en_title, wiki="en")

        if not en_list:
            logger.warning("en_list is empty. return")
            return False

        self.process_categories(en_title, labb, num, lenth, callback=callback)

    def process_categories(self, cat: str, arlab: str, num: int, lenth: int, callback: Callable | None = None) -> None:
        logger.debug(f"*:{num}/{lenth} cat: {cat}, arlab: {arlab}")

        ma_table = self.make_ar(cat, arlab, callback=callback)

        main_settings = Settings.get_instance()

        for i in range(main_settings.range_limit):
            if not ma_table:
                break

            logger.debug("===========================")
            logger.debug(f"**: range: {i} of {main_settings.range_limit}: for {len(ma_table)} cats.")
            logger.debug("===========================")

            enriched_titles = []
            number = 0

            for title in ma_table:
                logger.debug(r"\/\/\/ +++++++++ \/\/\/")
                logger.debug(f'work:{number}"{title}"')
                number += 1

                labe = ar_make_lab(title)

                logger.debug(f"*arlab: {labe}")

                if not labe:
                    continue

                en_list = self.category_resolver.list_en_pages_with_ar_links(title, wiki="en")

                if not en_list:
                    continue

                enriched_article_list = self.make_ar(title, labe, callback=callback)

                enriched_titles.extend(enriched_article_list)

            ma_table = list(set(enriched_titles))

        logger.debug("tago done........... ")

    def create_categories_from_list(self, titles: list[str], callback: Callable | None = None) -> None:
        lenth = len(titles)

        for num, en_title in enumerate(titles, 1):
            self.one_cat(en_title, num, lenth, callback=callback)


# ------------------------------------
# Legacy compatibility layer
# ------------------------------------


def process_categories(cat: str, arlab: str, num: int, lenth: int, callback: Callable | None = None) -> None:
    """Legacy compatibility wrapper for process_categories."""
    return CategoryManager().process_categories(cat, arlab, num, lenth, callback=callback)


def create_categories_from_list(titles: list[str], callback: Callable | None = None) -> None:
    """Legacy compatibility wrapper for create_categories_from_list."""
    return CategoryManager().create_categories_from_list(titles, callback=callback)


__all__ = [
    "CategoryManager",
    "create_categories_from_list",
    "process_categories",
]
