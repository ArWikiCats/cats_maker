""" """

import logging
from ..utils import filter_category

logger = logging.getLogger(__name__)


try:
    from ArWikiCats import resolve_arabic_category_label  # type: ignore
except ImportError:
    resolve_arabic_category_label = None
    logging.warning("ArWikiCats not available.")


def set_project_log_level(name: str, level: int) -> None:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    for handler in logger.handlers:
        handler.setLevel(level)


set_project_log_level("ArWikiCats", logging.ERROR)


def ar_make_lab(title: str, *args, **kwargs) -> str:
    title = str(title)

    bad_words = [
        "ذكور",
    ]

    if not filter_category(title):
        logger.debug(f"{title} is not okay.")
        return ""

    if not resolve_arabic_category_label:
        logger.debug("ArWikiCats.resolve_arabic_category_label not available.")
        return ""

    label = resolve_arabic_category_label(title)

    if not label:
        logger.debug(f'No label found for "{title}".')
        return ""

    for word in bad_words:
        if word in label:
            logger.error(f'label "{label}" has "{word}".')
            return ""

    return label


__all__ = [
    "ar_make_lab",
]
