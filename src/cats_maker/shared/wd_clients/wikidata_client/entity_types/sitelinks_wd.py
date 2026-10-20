#!/usr/bin/python3
""" """

from __future__ import annotations

import logging
import re
from typing import Any

from ....newapi import ApiResult
from ..wd_requests_handler import WikidataRequestHandler
from .handle_response import ResponseHandler

logger = logging.getLogger(__name__)


class WdSiteLinks(ResponseHandler):
    def __init__(self, wd_handler: WikidataRequestHandler) -> None:
        self.execute_wd_api_call = wd_handler.execute_wd_api_call

    def merge_items(self, q1: str, q2: str) -> ApiResult:
        """Merge two items in a knowledge base.

        This function merges two items identified by their IDs (q1 and q2). It
        first checks for any lag issues and then determines which item should be
        the source and which should be the target based on their numeric values.
        The merge operation is performed via a session post request, and the
        function handles potential redirection and errors that may arise during
        the process.

        Args:
            q1 (str): The ID of the first item to merge.
            q2 (str): The ID of the second item to merge.

        Returns:
            bool: True if the merge was successful, False otherwise.
        """
        q11 = re.sub(r"Q", "", q1)
        q22 = re.sub(r"Q", "", q2)

        if int(q11) > int(q22):
            item_from = q1
            item_to = q2
        else:
            item_from = q2
            item_to = q1

        out = f"Merge from {item_from} to {item_to} "

        logger.info(out)

        params: dict[str, Any] = {
            "action": "wbmergeitems",
            "fromid": item_from,
            "toid": item_to,
            "ignoreconflicts": "description",
            "summary": "",
            # "summary": "duplicated",
        }
        r4 = self.execute_wd_api_call(params)

        result = self.handle_response(r4, out)

        if result.is_ok:
            _e = {
                "success": 1,
                "redirected": 0,
                "from": {"id": "Q65687062", "type": "item", "lastrevid": 1849114386},
                "to": {"id": "Q8278540", "type": "item", "lastrevid": 1849114387},
            }

            redirected = r4.get("redirected", 0)

            if redirected == 1:
                logger.info("<<lightgreen>> ** true .. redirected.")
            else:
                logger.info("<<lightgreen>> ** true, no redirected.")
                self.wbcreateredirect(item_from, item_to)
            return result

        return result

    def wbcreateredirect(
        self,
        item_from: str,
        item_to: str,
    ) -> ApiResult:

        if item_from.strip() == item_to.strip():
            logger.info("<<lightgreen>> **False: From == To.")
            return ApiResult.fail(code="from_to_equals")

        out = f"wbcreateredirect from {item_from} to {item_to} "

        params: dict[str, Any] = {
            "action": "wbcreateredirect",
            "from": item_from,
            "to": item_to,
            "ignoreconflicts": "description",
        }
        r4 = self.execute_wd_api_call(params)
        return self.handle_response(r4, out)

    def find_page_qids(
        self,
        site_code: str,
        titles_str: str,
    ) -> dict[str, Any]:
        site_code = site_code.removesuffix("wiki")

        params: dict[str, Any] = {
            "action": "query",
            "titles": titles_str,
            "redirects": 1,
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            # "normalize": 1,
            "formatversion": 2,
        }

        _sitewiki = f"{site_code}wiki"

        json1 = self.execute_wd_api_call(params)

        if not json1:
            return {}

        Main_table = {}
        js = json1.get("query", {})

        for red in js.get("redirects", []):
            Main_table[red["from"]] = {
                "is_redirect_page": True,
                "missing": True,
                "from": red["from"],
                "to": red["to"],
                "title": red["from"],
                "ns": "",
                "q": "",
            }

        pages = js.get("pages") or []

        for kk in pages:
            if "title" in kk:
                title = kk["title"]
                Main_table[title] = {}

                if "missing" in kk:
                    Main_table[title]["missing"] = True

                Main_table[title]["ns"] = kk.get("ns", "")
                Main_table[title]["pageid"] = kk.get("pageid", "")
                Main_table[title]["q"] = kk.get("pageprops", {}).get("wikibase_item", "")

        return Main_table

    def remove_sitelink(
        self,
        qid_str: str,
        wiki: str,
    ) -> ApiResult:

        wiki = wiki.removesuffix("wiki")

        wiki = f"{wiki}wiki"

        # save the edit
        out = f'remove "{wiki}" link from "{qid_str}"'

        params: dict[str, Any] = {
            "action": "wbsetsitelink",
            "id": qid_str,
            "linksite": wiki,
        }
        r4 = self.execute_wd_api_call(params)

        return self.handle_response(r4, out)

    def add_sitelink_by_qid(
        self,
        *,
        qid: str,
        title: str,
        wiki: str,
    ) -> ApiResult:

        wiki = self.ensure_wiki_suffix(wiki)

        logger.info(f' ** qid_str:"{qid}" {wiki}:{title}')

        # save the edit

        if qid.strip() == "":
            logger.info(f'<<lightred>> ** False: qid_str == "" {wiki}:{title}.')
            return ApiResult.fail(code="no_qid")

        paramse = {
            "action": "wbsetsitelink",
            "linktitle": title,
            "linksite": wiki,
            "id": qid,
        }

        out = f'Added link to "{qid}" [{wiki}]:"{title}"'

        r4 = self.execute_wd_api_call(paramse, tage="setsitelink")

        result = self.handle_response(r4, out)

        if result.is_ok:
            return ApiResult.ok(data={"id": qid})

        return result

    def sitelink_api_by_title(
        self,
        title: str,
        wiki: str,
        enlink: str = "",
        ensite: str = "",
    ) -> ApiResult:

        wiki = self.ensure_wiki_suffix(wiki)

        logger.info(f' ** enlink:"{ensite}:{enlink}" {wiki}:{title}')

        # save the edit

        if not enlink or not ensite:
            logger.info(f"<<lightred>> ** False: {enlink=}, {ensite=}.")
            return ApiResult.fail(code="no_qid")

        paramse = {
            "action": "wbsetsitelink",
            "linktitle": title,
            "linksite": wiki,
            "title": enlink,
            "site": ensite,
        }

        out = f'Added link to "{ensite}:{enlink}" [{wiki}]:"{title}"'

        r4 = self.execute_wd_api_call(paramse, tage="setsitelink")

        result = self.handle_response(r4, out)

        if result.is_ok:
            ido = re.match(r".*\"id\"\:\"(Q\d+)\".*", str(r4))
            new_qid = ido.group(1) if ido else None
            return ApiResult.ok(data={"id": new_qid})

        return result

    @staticmethod
    def ensure_wiki_suffix(wiki: str) -> str:
        if not wiki.endswith("wiki") and wiki.find("wiki") == -1 and wiki.find("wiktionary") == -1:
            wiki = f"{wiki}wiki"
        return wiki


__all__ = [
    "WdSiteLinks",
]
