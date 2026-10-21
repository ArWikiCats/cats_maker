import logging
from collections.abc import Callable

from ...core_cat.lists.category_resolver import CategoryResolver
from .mknew_creator import CategoryCreator
from .mknew_members import CategoryMembersAdder
from .mknew_processor import CategoryBatchProcessor
from .mknew_sources import ArabicCategoryChecker, EnglishCategorySource
from .mknew_state import CategoryManagerStats
from .mknew_wikidata import CategoryWikidataService

# TODO: move it to the settings file!
WIKI_SITE_AR = {"family": "wikipedia", "code": "ar"}
WIKI_SITE_EN = {"family": "wikipedia", "code": "en"}

logger = logging.getLogger(__name__)


class CategoryManager:
    """Facade over the category creation components (also the composition root).

    Responsibilities live in:
    - CategoryWikidataService: Wikidata lookup, labels, logging
    - EnglishCategorySource / ArabicCategoryChecker: reading the two wikis
    - CategoryMembersAdder: adding the new category to member pages
    - CategoryCreator: creating one category (make_ar)
    - CategoryBatchProcessor: iterating over titles (one_cat, process_categories, ...)
    - CategoryManagerStats: shared processing state
    """

    def __init__(
        self,
        category_resolver: CategoryResolver | None = None,
        wiki_site_ar: dict | None = None,
        wiki_site_en: dict | None = None,
        stats: CategoryManagerStats | None = None,
        creator: CategoryCreator | None = None,
        processor: CategoryBatchProcessor | None = None,
    ) -> None:
        self.category_resolver = category_resolver or CategoryResolver()
        self.wiki_site_ar = wiki_site_ar or WIKI_SITE_AR
        self.wiki_site_en = wiki_site_en or WIKI_SITE_EN

        self.stats = stats or CategoryManagerStats()

        # One shared stats instance and one resolver are passed down the whole graph
        self.creator = creator or CategoryCreator(
            wiki_site_ar=self.wiki_site_ar,
            stats=self.stats,
            wikidata=CategoryWikidataService(self.wiki_site_ar, self.wiki_site_en),
            english_source=EnglishCategorySource(self.wiki_site_en),
            arabic_checker=ArabicCategoryChecker(self.wiki_site_ar),
            members_adder=CategoryMembersAdder(),
            category_resolver=self.category_resolver,
        )
        self.processor = processor or CategoryBatchProcessor(
            stats=self.stats,
            creator=self.creator,
            category_resolver=self.category_resolver,
        )

    def make_ar(self, en_page_title: str, ar_title: str, callback: Callable | None = None) -> list:
        """Create an Arabic category based on the English category."""
        return self.creator.make_ar(en_page_title, ar_title, callback=callback)

    def one_cat(self, en_title: str, num: int, lenth: int, sugust: str = "", callback: Callable | None = None) -> bool:
        return self.processor.one_cat(en_title, num, lenth, sugust=sugust, callback=callback)

    def process_categories(self, cat: str, arlab: str, num: int, lenth: int, callback: Callable | None = None) -> None:
        return self.processor.process_categories(cat, arlab, num, lenth, callback=callback)

    def create_categories_from_list(self, titles: list[str], callback: Callable | None = None) -> None:
        return self.processor.create_categories_from_list(titles, callback=callback)


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
