""" """

import logging
from collections.abc import KeysView
from ..api_utils import change_codes

logger = logging.getLogger(__name__)


class NEW_API:
    def __init__(self, login_bot, lang):
        self.login_bot = login_bot
        self.user_login = login_bot.user_login
        self.username = getattr(self, "username", "")
        self.lang = change_codes.get(lang) or lang
        # ---
        super().__init__()

    def post_params(self, params, Type="get", addtoken=False, GET_CSRF=True, files=None, do_error=False, max_retry=0):
        # ---
        return self.login_bot.post_params(
            params, Type=Type, addtoken=addtoken, GET_CSRF=GET_CSRF, files=files, do_error=do_error, max_retry=max_retry
        )

    def post_continue(
        self, params, action, _p_="pages", p_empty=None, Max=500000, first=False, _p_2="", _p_2_empty=None
    ):
        return self.login_bot.post_continue(
            params, action, _p_=_p_, p_empty=p_empty, Max=Max, first=first, _p_2=_p_2, _p_2_empty=_p_2_empty
        )

    def Find_pages_exists_or_not(self, liste, get_redirect=False):
        # ---
        done = 0
        # ---
        all_jsons = {}
        # ---
        for titles in self.chunk_titles(liste, chunk_size=50):
            # ---
            done += len(titles)
            # ---
            params = {
                "action": "query",
                "titles": "|".join(titles),
                "prop": "info|pageprops",
                "ppprop": "wikibase_item",
                "formatversion": 2,
            }
            json1 = self.post_params(params)
            # ---
            if not json1:
                logger.debug("<<lightred>> error when ")
                continue
            # ---
            all_jsons = self.merge_all_jsons_deep(all_jsons, json1)
        # ---
        redirects = 0
        missing = 0
        exists = 0
        # ---
        query_table = all_jsons.get("query", {})
        # ---
        normalz = query_table.get("normalized", [])
        normalized = {red["to"]: red["from"] for red in normalz}
        # ---
        query_pages = query_table.get("pages", [])
        # ---
        table = {}
        # ---
        for kk in query_pages:
            # ---
            if isinstance(query_pages, dict):
                kk = query_pages[kk]
            # ---
            tit = kk.get("title", "")
            # ---
            if not tit:
                continue
            # ---
            tit = normalized.get(tit, tit)
            # ---
            table[tit] = True
            # ---
            if "missing" in kk:
                table[tit] = False
                missing += 1
            elif "redirect" in kk and get_redirect:
                table[tit] = "redirect"
                redirects += 1
            else:
                exists += 1
        # ---
        logger.debug(f" : missing:{missing}, exists: {exists}, redirects: {redirects}")
        # ---
        return table

    def chunk_titles(self, titles, chunk_size=50):
        # ---
        if isinstance(titles, dict):
            titles = list(titles.keys())

        elif isinstance(titles, KeysView):
            # TypeError: 'dict_keys' object is not subscriptable
            titles = list(titles)
        # ---
        result = [titles[i : i + chunk_size] for i in range(0, len(titles), chunk_size)]
        # ---
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
