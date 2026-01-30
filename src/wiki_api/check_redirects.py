import logging

from ..new_api.page import NEW_API, SuperNEW_API

logger = logging.getLogger(__name__)


def _load_new_api(lang) -> SuperNEW_API:
    return NEW_API(lang, family="wikipedia")


def load_non_redirects(lang: str, page_titles: list) -> list:
    """Remove redirect pages from a list of page titles."""
    api = _load_new_api(lang)

    result = api.Find_pages_exists_or_not(page_titles, get_redirect=True)

    non_redirects = [x for x, v in result.items() if v is True]  # and v != "redirect"
    return non_redirects


def remove_redirect_pages(lang: str, page_titles: list) -> list:
    """Remove redirect pages from a list of page titles."""
    non_redirects = load_non_redirects(lang, page_titles)
    logger.info(f"<<lightgreen>> Removed {len(page_titles) - len(non_redirects)} redirect pages.<<default>>")
    return non_redirects
