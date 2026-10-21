import logging
from collections.abc import Callable

from ...config import Settings
from ...core_cat.lists.category_resolver import CategoryResolver
from .labels_creator import ar_make_lab
from .mknew_creator import CategoryCreator
from .mknew_state import CategoryManagerStats
from ..utils import check_en_temps

logger = logging.getLogger(__name__)


class CategoryBatchProcessor:
    """Drives category creation over titles: label lookup, filtering and recursive expansion."""

    def __init__(
        self,
        stats: CategoryManagerStats,
        creator: CategoryCreator,
        category_resolver: CategoryResolver | None = None,
    ) -> None:
        self.stats = stats
        self.creator = creator
        self.category_resolver = category_resolver or CategoryResolver()

    def one_cat(
        self,
        en_title: str,
        num: int,
        lenth: int,
        sugust: str = "",
        callback: Callable | None = None,
    ) -> bool:
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

        return True

    def process_categories(
        self,
        cat: str,
        arlab: str,
        num: int,
        lenth: int,
        callback: Callable | None = None,
    ) -> None:
        logger.debug(f"*:{num}/{lenth} cat: {cat}, arlab: {arlab}")

        ma_table = self.creator.make_ar(cat, arlab, callback=callback)

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

                enriched_article_list = self.creator.make_ar(title, labe, callback=callback)

                enriched_titles.extend(enriched_article_list)

            ma_table = list(set(enriched_titles))

        logger.debug("tago done........... ")

    def create_categories_from_list(self, titles: list[str], callback: Callable | None = None) -> None:
        lenth = len(titles)

        for num, en_title in enumerate(titles, 1):
            self.one_cat(en_title, num, lenth, callback=callback)


__all__ = [
    "CategoryBatchProcessor",
]
