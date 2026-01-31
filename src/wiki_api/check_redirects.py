import logging

from ..new_api.pagenew import load_main_api

logger = logging.getLogger(__name__)


def load_non_redirects(lang: str, page_titles: list) -> list:
    """Remove redirect pages from a list of page titles."""
    api = load_main_api(lang)
    result = api.NEW_API.Find_pages_exists_or_not(page_titles, get_redirect=True)

    non_redirects = [x for x, v in result.items() if v is True]  # and v != "redirect"
    return non_redirects


def remove_redirect_pages(lang: str, page_titles: list) -> list:
    """Remove redirect pages from a list of page titles."""
    non_redirects = load_non_redirects(lang, page_titles)
    logger.info(f"<<lightgreen>> Removed {len(page_titles) - len(non_redirects)} redirect pages.<<default>>")
    return non_redirects
