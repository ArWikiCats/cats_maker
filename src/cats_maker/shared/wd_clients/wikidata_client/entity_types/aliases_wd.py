#!/usr/bin/python3
"""
POST bot - Aliases functionality

This module provides functions for working with Aliases in Wikidata.
"""

from __future__ import annotations

import logging
from typing import Any

from ....newapi import ApiResult
from ..wd_requests_handler import WikidataRequestHandler
from .handle_response import ResponseHandler

logger = logging.getLogger(__name__)


class WdAliases(ResponseHandler):
    def __init__(self, wd_handler: WikidataRequestHandler) -> None:
        self.execute_wd_api_call = wd_handler.execute_wd_api_call

    def alias_api(
        self,
        qid: str,
        alias_list: list[str],
        lang: str,
        remove_it: list | None = None,
    ) -> ApiResult:

        # TODO: write a function for remove aliases

        if remove_it is None:
            remove_it = []

        # save the edit
        NN = "|".join(alias_list)
        out = f'{qid} alia:"{lang}"@{NN}.'
        params: dict[str, Any] = {
            "action": "wbsetaliases",
            "id": qid,
            "language": lang,
        }

        if remove_it:
            lala = "|".join(remove_it)
            params["remove"] = lala
            out = f'{qid} alia remove:"{lang}"@{lala}.'
        else:
            params["add"] = NN

        r4 = self.execute_wd_api_call(params)

        return self.handle_response(r4, out)


__all__ = [
    "WdAliases",
]
