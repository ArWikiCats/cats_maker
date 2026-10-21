import logging

from ...core_cat.c18.infrastructure.network.langlinks import LangLinksClient
from ...shared.newapi import AllAPIS

logger = logging.getLogger(__name__)


class EnglishCategorySource:
    """Reads information about the English source category."""

    def __init__(self, wiki_site_en: dict, langlinks_client_cls: type[LangLinksClient] | None = None) -> None:
        self.wiki_site_en = wiki_site_en
        # A class (not an instance) because a client is created per call
        self.langlinks_client_cls = langlinks_client_cls or LangLinksClient

    @staticmethod
    def normalize_title(en_page_title: str) -> str:
        """Clean and normalize an English page title."""
        title = en_page_title.replace("[[", "").replace("]]", "").strip()
        return title.replace("_", " ")

    def find_parent_categories(self, en_page_title: str) -> tuple[list, list]:
        """Extract parent categories for the English page.

        Returns:
            tuple: (English parents without Arabic equivalent, Arabic parents)
        """
        cates = self.langlinks_client_cls(
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


class ArabicCategoryChecker:
    """Checks the state of categories on the Arabic wiki."""

    def __init__(self, wiki_site_ar: dict, apis_cls: type[AllAPIS] | None = None) -> None:
        self.wiki_site_ar = wiki_site_ar
        self.apis_cls = apis_cls or AllAPIS

    def can_create(self, test_title: str) -> bool:
        """Return True when the Arabic category does not exist yet."""
        if not test_title.startswith("تصنيف:"):
            test_title = f"تصنيف:{test_title}"

        api = self.apis_cls.load(self.wiki_site_ar["code"])
        page = api.mainpage(test_title)

        if page.exists():
            logger.debug(f"* category:{test_title} already exists in arwiki.")
            return False

        return True


__all__ = [
    "EnglishCategorySource",
    "ArabicCategoryChecker",
]
