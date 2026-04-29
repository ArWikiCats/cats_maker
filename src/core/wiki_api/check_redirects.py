import logging
from collections.abc import KeysView

from ..new_api import load_main_api

logger = logging.getLogger(__name__)


class NEW_API:
    def __init__(self, login_bot):
        self.login_bot = login_bot

    def Find_pages_exists_or_not(self, liste, get_redirect=False) -> dict:
        all_jsons = {}

        for titles in self.chunk_titles(liste, chunk_size=50):
            params = {
                "action": "query",
                "titles": "|".join(titles),
                "prop": "info|pageprops",
                "formatversion": 2,
            }
            json1 = self.login_bot.client_request(params)
            if not json1:
                logger.debug("<<lightred>> error when ")
                continue
            all_jsons = self.merge_all_jsons_deep(all_jsons, json1)

        redirects = 0
        missing = 0
        exists = 0

        query_table = all_jsons.get("query", {})
        normalz = query_table.get("normalized", [])
        normalized = {red["to"]: red["from"] for red in normalz}
        query_pages = query_table.get("pages", [])

        table = {}
        for kk in query_pages:
            if isinstance(query_pages, dict):
                kk = query_pages[kk]

            tit = kk.get("title", "")

            if not tit:
                continue

            tit = normalized.get(tit, tit)
            table[tit] = True

            if "missing" in kk:
                table[tit] = False
                missing += 1

            elif "redirect" in kk and get_redirect:
                table[tit] = "redirect"
                redirects += 1
            else:
                exists += 1

        logger.debug(f" : missing:{missing}, exists: {exists}, redirects: {redirects}")
        return table

    def chunk_titles(self, titles, chunk_size=50):
        if isinstance(titles, dict):
            titles = list(titles.keys())

        elif isinstance(titles, KeysView):
            # TypeError: 'dict_keys' object is not subscriptable
            titles = list(titles)
        result = [titles[i : i + chunk_size] for i in range(0, len(titles), chunk_size)]
        return result

    def merge_all_jsons_deep(self, all_jsons, json1):
        def deep_merge(a, b):
            if isinstance(a, dict) and isinstance(b, dict):
                for k, v in b.items():
                    if k in a:
                        a[k] = deep_merge(a[k], v)
                    else:
                        a[k] = v
                return a
            elif isinstance(a, list) and isinstance(b, list):
                return a + b
            else:
                return b

        if not isinstance(all_jsons, dict):
            all_jsons = {}

        return deep_merge(all_jsons, json1)


def load_non_redirects(lang: str, page_titles: list) -> dict:
    """Return a mapping of page title -> True (exists) / False (missing) / "redirect"."""
    if not page_titles:
        return {}

    _bot = load_main_api(lang, "wikipedia")

    api_n = NEW_API(_bot.login_bot)
    result = api_n.Find_pages_exists_or_not(page_titles, get_redirect=True)
    return result


def remove_redirect_pages(lang: str, page_titles: list) -> list:
    """Remove redirect pages from a list of page titles."""
    result = load_non_redirects(lang, page_titles)
    non_redirects = [x for x, v in result.items() if v is True]
    logger.info(f"<<lightgreen>> Removed {len(page_titles) - len(non_redirects)} redirect pages.")
    return non_redirects
