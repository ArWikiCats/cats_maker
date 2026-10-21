import logging
from collections.abc import Callable

from ...config import Settings
from ...core_cat.lists.category_resolver import CategoryResolver
from ...core_cat.lists.category_validator import validate_categories_for_new_cat
from ...core_cat.lists.members_helper import collect_category_members
from ..create_category_page import new_category
from .mknew_members import CategoryMembersAdder
from .mknew_sources import ArabicCategoryChecker, EnglishCategorySource
from .mknew_state import CategoryManagerStats
from .mknew_wikidata import CategoryWikidataService

logger = logging.getLogger(__name__)


class CategoryCreator:
    """Creates one Arabic category from an English category (the make_ar use case)."""

    def __init__(
        self,
        wiki_site_ar: dict,
        stats: CategoryManagerStats,
        wikidata: CategoryWikidataService,
        english_source: EnglishCategorySource,
        arabic_checker: ArabicCategoryChecker,
        members_adder: CategoryMembersAdder | None = None,
        category_resolver: CategoryResolver | None = None,
    ) -> None:
        self.wiki_site_ar = wiki_site_ar
        self.stats = stats
        self.wikidata = wikidata
        self.english_source = english_source
        self.arabic_checker = arabic_checker
        self.members_adder = members_adder or CategoryMembersAdder()
        self.category_resolver = category_resolver or CategoryResolver()

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
        self.members_adder.add(members, ar_title, callback=callback)

        if validate_categories_for_new_cat(ar_title, en_page_title, wiki="en"):
            listen = self.category_resolver.resolve_members(en_page_title, ar_title, wiki="en") or []
            if listen:
                self.members_adder.add(listen, ar_title, callback=callback)

        self.wikidata.log_creation(ar_title, en_page_title, qid)

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
        en_page_title = self.english_source.normalize_title(en_page_title)

        # Validation: Check if Arabic category already exists
        if not self.arabic_checker.can_create(ar_title):
            logger.debug("artitle already exists.")
            return []

        # Check Wikidata sitelinks - early exit if Arabic link exists
        has_ar_sitelink, ar_info = self.wikidata.check_sitelink(en_page_title)
        if has_ar_sitelink:
            return []

        qid = ar_info.get("q", "")

        # Extract parent categories
        en_cats_of_new_cat, cats_of_new_cat = self.english_source.find_parent_categories(en_page_title)

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

        self.members_adder.log_members_info(members)

        # Create the category
        created_category = new_category(
            en_page_title, ar_title, cats_of_new_cat, qid, family=self.wiki_site_ar["family"]
        )

        if not created_category.success:
            self.wikidata.add_arabic_label(qid, ar_title)
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


__all__ = [
    "CategoryCreator",
]
