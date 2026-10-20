""" """

from __future__ import annotations

import logging
from typing import Any

from ...newapi import WikiLoginClient

logger = logging.getLogger(__name__)


class WPFunctions:
    def __init__(self, login_bot: WikiLoginClient) -> None:
        self.login_bot = login_bot

    def get_all_pages(
        self,
        start: str = "",
        namespace: str = "0",
        limit: int | str = "max",
        apfilterredir: str = "",
        ppprop: str = "",
        limit_all: int = 100000,
    ) -> list[str]:

        logger.debug(
            f"get_all_pages for start:{start}, limit:{limit},namespace:{namespace},apfilterredir:{apfilterredir}"
        )

        params: dict[str, Any] = {
            "action": "query",
            "format": "json",
            "prop": "pageprops",
            "list": "allpages",
            "apnamespace": namespace,
            "aplimit": limit,
            "apfilterredir": "nonredirects",
            "formatversion": 1,
        }

        if str(namespace) in ["*", "", "all"]:
            del params["apnamespace"]

        if ppprop:
            params["ppprop"] = ppprop

        if apfilterredir in ["redirects", "all", "nonredirects"]:
            params["apfilterredir"] = apfilterredir

        if start:
            params["apfrom"] = start

        def _load_data(body):
            return body.get("query", {}).get("allpages") or []

        newp = self.login_bot.post_continue_list(
            params=params,
            action="query",
            max=limit_all,
            _load_data=_load_data,
        )

        logger.debug(f"<<lightpurple>> --- : find {len(newp)} pages.")

        Main_table = [x["title"] for x in newp]

        logger.debug(f"len of Main_table {len(Main_table)}.")

        logger.info(f"bot_api.py : find {len(Main_table)} pages.")

        return Main_table

    def api_search(
        self,
        value: str = "",
        ns: str = "*",
        offset: int | str = "",
        srlimit: str = "max",
        addparams=None,
    ) -> list[dict[str, Any]]:

        logger.debug(f'bot_api. for "{value}",ns:{ns}')

        if not srlimit:
            srlimit = "max"

        params: dict[str, Any] = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": value,
            "srnamespace": 0,
            "srlimit": srlimit,
            "formatversion": 1,
        }

        if ns:
            params["srnamespace"] = ns

        if offset:
            params["sroffset"] = offset

        if addparams:
            addparams = {x: v for x, v in addparams.items() if v and x not in params}
            params: dict[str, Any] = {**params, **addparams}

        def _load_data(body):
            return body.get("query", {}).get("search") or []

        search = self.login_bot.post_continue_list(
            params=params,
            action="query",
            _load_data=_load_data,
        )

        results: list = []

        for pag in search:
            results.append(pag)

        logger.debug(f'bot_api. find "{len(search)}" all result: {len(results)}')

        return results

    def get_newpages(
        self,
        limit: int | str = 5000,
        namespace: str = "0",
        rcstart: str = "",
        user: str = "",
    ):
        params: dict[str, Any] = {
            "action": "query",
            "format": "json",
            "list": "recentchanges",
            # "rcdir": "newer",
            "rcnamespace": namespace,
            "rclimit": "max",
            "utf8": 1,
            "rctype": "new",
            "formatversion": 2,
        }

        if rcstart:
            params["rcstart"] = rcstart
        if user:
            params["rcuser"] = user

        if (isinstance(limit, str) and limit.isdigit()) or isinstance(limit, int):
            limit = int(limit)
            params["rclimit"] = limit
        else:
            limit = 5000

        def _load_data(body):
            return body.get("query", {}).get("recentchanges") or []

        json1 = self.login_bot.post_continue_list(
            params=params,
            action="query",
            _load_data=_load_data,
            max=limit,
        )
        Main_table = [x["title"] for x in json1]

        logger.debug(f'bot_api. find "{len(Main_table)}" result. s')

        return Main_table

    def user_contribs(
        self,
        user,
        limit: int | str = 5000,
        namespace: str = "*",
        ucshow: str = "",
    ):

        params: dict[str, Any] = {
            "action": "query",
            "format": "json",
            "list": "usercontribs",
            "ucdir": "older",
            "ucnamespace": namespace,
            "uclimit": "max",
            "ucuser": user,
            "utf8": 1,
            # "bot": 1,
            "ucprop": "title",
            "formatversion": 1,
        }

        if ucshow:
            params["ucshow"] = ucshow

        def _load_data(body):
            return body.get("query", {}).get("usercontribs") or []

        results = self.login_bot.post_continue_list(
            params=params,
            action="query",
            _load_data=_load_data,
            max=int(limit),
        )

        results = [x["title"] for x in results]

        return results

    def get_revisions(
        self,
        title: str,
        rvprop: str = "comment|timestamp|user|content|ids",
        options=None,
    ):

        params: dict[str, Any] = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": title,
            "utf8": 1,
            "rvprop": "comment|timestamp|user|content|ids",
            "rvdir": "newer",
            "rvlimit": "max",
            "formatversion": 2,
        }

        params["rvprop"] = rvprop or "comment|timestamp|user|content|ids"

        if options:
            params.update(options)

        def _load_data(body):
            return body.get("query", {}).get("pages") or []

        results = self.login_bot.post_continue_list(
            params=params,
            action="query",
            _load_data=_load_data,
        )

        return results

    def querypage_list(self, qppage: str = "Wantedcategories", qplimit=None, max=None):

        params: dict[str, Any] = {
            "action": "query",
            "format": "json",
            "list": "querypage",
            # "qppage": "Wantedcategories",
            "qplimit": "max",
            "formatversion": 2,
        }

        if qplimit and str(qplimit).isdigit():
            params["qplimit"] = qplimit

        params["qppage"] = qppage

        qppage_values = [
            "Ancientpages",
            "BrokenRedirects",
            "Deadendpages",
            "DisambiguationPageLinks",
            "DisambiguationPages",
            "DoubleRedirects",
            "Fewestrevisions",
            "GadgetUsage",
            "GloballyWantedFiles",
            "ListDuplicatedFiles",
            "Listredirects",
            "Lonelypages",
            "Longpages",
            "MediaStatistics",
            "MostGloballyLinkedFiles",
            "Mostcategories",
            "Mostimages",
            "Mostinterwikis",
            "Mostlinked",
            "Mostlinkedcategories",
            "Mostlinkedtemplates",
            "Mostrevisions",
            "OrphanedTimedText",
            "Shortpages",
            "Uncategorizedcategories",
            "Uncategorizedimages",
            "Uncategorizedpages",
            "Uncategorizedtemplates",
            "UnconnectedPages",
            "Unusedcategories",
            "Unusedimages",
            "Unusedtemplates",
            "Unwatchedpages",
            "Wantedcategories",
            "Wantedfiles",
            "Wantedpages",
            "Wantedtemplates",
            "Withoutinterwiki",
        ]

        if qppage not in qppage_values:
            logger.info(f"<<lightred>> qppage {qppage} not in qppage_values.")

        def _load_data(body):
            query = body.get("query", {})
            return query.get("querypage") or query.get("results") or []

        results = self.login_bot.post_continue_list(
            params=params,
            action="query",
            _load_data=_load_data,
            max=max,
        )

        logger.debug(f" len(results) = {len(results)}")

        return results

    def get_template_pages(self, title: str, namespace: str = "*", max: int = 10000):

        logger.debug(f'get_template_pages for template:"{title}", limit:"{max}",namespace:"{namespace}"')

        params: dict[str, Any] = {
            "action": "query",
            # "prop": "info",
            "titles": title,
            "generator": "transcludedin",
            "gtinamespace": namespace,
            "gtilimit": "max",
            "formatversion": 2,
        }

        def _load_data(body):
            return body.get("query", {}).get("pages") or []

        results = self.login_bot.post_continue_list(
            params=params,
            action="query",
            _load_data=_load_data,
        )

        # { "pageid": 2973452, "ns": 100, "title": "بوابة:سباق الدراجات الهوائية" }
        pages = [x["title"] for x in results]

        logger.info(f"mdwiki_api.py find {len(pages)} pages.")

        return pages

    def pageswithprop(
        self,
        pwppropname: str = "unlinkedwikibase_id",
        pwplimit=None,
        max=None,
    ):

        params: dict[str, Any] = {
            "action": "query",
            "format": "json",
            "list": "pageswithprop",
            "utf8": 1,
            "formatversion": 2,
            "pwplimit": "max",
            "pwppropname": "unlinkedwikibase_id",
            "pwpprop": "title|value",
        }

        if pwplimit and str(pwplimit).isdigit():
            params["pwplimit"] = pwplimit

        if pwppropname != "":
            params["pwppropname"] = pwppropname

        def _load_data(body):
            return body.get("query", {}).get("pageswithprop") or []

        results = self.login_bot.post_continue_list(
            params=params,
            action="query",
            _load_data=_load_data,
            max=max,
        )

        logger.debug(f" len(results) = {len(results)}")

        return results


__all__ = [
    "WPFunctions",
]
