#!/usr/bin/python3
""" """

from __future__ import annotations

import logging
import sys

from ....config import Settings

from ...newapi import ApiResult, AskBot, WikiLoginClient
from ...newapi.core.result_error import ApiResultError
from .bot_wd import WDFunctions
from .bot_wp import WPFunctions
from .entity_types import (
    WdAliases,
    WdClaims,
    WdDescriptions,
    WdItems,
    WdLabels,
    WdSiteLinks,
)
from .wd_requests_handler import (
    WikidataRequestHandler,
)

logger = logging.getLogger(__name__)


class WikidataClient(WPFunctions, WDFunctions):
    def __init__(
        self,
        login_bot: WikiLoginClient,
        dont_do_lag_wait: bool = False,
    ) -> None:

        self.login_bot = login_bot

        self.wd_request_handler = WikidataRequestHandler(
            self.login_bot,
            dont_do_lag_wait=dont_do_lag_wait,
        )

        self.ask_bot = AskBot(
            ask="ask" in sys.argv,
            nodiff="nodiff" in sys.argv,
        )

        # WikidataRequestHandler.__init__(self, self.login_bot)
        WPFunctions.__init__(self, self.login_bot)
        WDFunctions.__init__(self, self.login_bot)
        # =======================

        _claims = WdClaims(self.wd_request_handler)

        self.add_quall = _claims.add_quall
        self.claim_api = _claims.claim_api
        self.claim_api_time = _claims.claim_api_time

        # =======================
        _descriptions = WdDescriptions(self.wd_request_handler, self.ask_bot)

        self.new_mult_des = _descriptions.new_mult_des
        self.new_mult_des_2 = _descriptions.new_mult_des_2
        self.des_api = _descriptions.des_api

        # =======================
        _labels = WdLabels(self.wd_request_handler)

        self.add_label_qid = _labels.add_label_qid
        self.add_label_by_site = _labels.add_label_by_site

        # =======================
        aliases = WdAliases(self.wd_request_handler)
        self.alias_api = aliases.alias_api

        # =======================
        _sitelinks = WdSiteLinks(self.wd_request_handler)

        self.add_sitelink_by_qid = _sitelinks.add_sitelink_by_qid
        self.sitelink_api_by_title = _sitelinks.sitelink_api_by_title
        self.remove_sitelink = _sitelinks.remove_sitelink
        self.merge_items = _sitelinks.merge_items

        # =======================
        _items = WdItems(self.wd_request_handler)

        self.new_api = _items.new_api
        self.clearitem = _items.clearitem
        self.mergehistory = _items.mergehistory

    def labels_api_or_aliases(
        self,
        qid: str,
        label: str,
        lang: str,
        tage: str = "",
    ) -> ApiResult:

        result = self.add_label_qid(
            qid=qid,
            label=label,
            lang=lang,
            tage=tage,
        )

        if not result.is_ok and self._is_label_conflict_retriable(result.error):
            return self.alias_api(qid, [label], lang)

        return result

    def _is_label_conflict_retriable(self, error: ApiResultError | None) -> bool:
        return (
            error is not None
            and error.code == "modification-failed"
            and getattr(error, "reason", "") == "label-description-conflict"
        )

    @classmethod
    def load(
        cls,
        www="www",
        dont_do_lag_wait: bool = False,
    ) -> WikidataClient:
        main_settings = Settings.get_instance()
        username, password = main_settings.wikipedia.load_credentials("bot")

        login_bot = WikiLoginClient.load(
            lang=www,
            family="wikidata",
            username=str(username),
            password=str(password),
        )

        return cls(
            login_bot=login_bot,
            dont_do_lag_wait=dont_do_lag_wait,
        )


__all__ = [
    "WikidataClient",
]
