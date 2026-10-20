#!/usr/bin/python3
"""
POST bot - Items functionality

This module provides functions for working with items in Wikidata.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from ....newapi import ApiResult
from ..wd_requests_handler import WikidataRequestHandler
from .handle_response import ResponseHandler

logger = logging.getLogger(__name__)


class WdItems(ResponseHandler):
    def __init__(self, wd_handler: WikidataRequestHandler) -> None:
        self.execute_wd_api_call = wd_handler.execute_wd_api_call

    def new_api(
        self,
        data2: dict[str, Any],
        summary: str,
        tage: str = "",
    ) -> ApiResult:
        """
        Create a new item in the API with the provided data and summary.
        """
        try:
            data = json.JSONEncoder().encode(data2)
        except Exception as e:
            logger.exception("Exception:", exc_info=True)
            return ApiResult.fail(code="json_encode_error", error=str(e), data={"text": str(e)})

        params: dict[str, Any] = {
            "action": "wbeditentity",
            "new": "item",
            "summary": summary,
            "data": data,
        }
        r4 = self.execute_wd_api_call(params, tage=tage)

        out = summary
        result = self.handle_response(r4, out)

        if result.is_ok:
            qid_str = ""
            if "entity" in r4 and "id" in r4["entity"]:
                qid_str = r4["entity"]["id"]
                logger.info(f'<<lightgreen>> returnid:"{qid_str}" ')
            return ApiResult.ok(data={"id": qid_str})

        return result

    def clearitem(self, q: str, summary: str) -> ApiResult:
        logger.info("bot.new_mult_des: ")

        params: dict[str, Any] = {
            "action": "wbeditentity",
            "errorformat": "wikitext",
            "id": q,
            "summary": summary,
            "clear": 1,
            "data": "{}",
        }
        r4 = self.execute_wd_api_call(params)
        out = summary
        return self.handle_response(r4, out)

    def mergehistory(self, q1: str, q2: str) -> ApiResult:
        q11 = re.sub(r"Q", "", q1)
        q22 = re.sub(r"Q", "", q2)

        if int(q11) > int(q22):
            item_from = q1
            item_to = q2
        else:
            item_from = q2
            item_to = q1

        out = f"mergehistory from {item_from} to {item_to} "
        logger.info(out)

        params: dict[str, Any] = {
            "action": "mergehistory",
            "from": item_from,
            "to": item_to,
            "reason": "duplicated",
        }
        r4 = self.execute_wd_api_call(params)
        return self.handle_response(r4, out)


__all__ = [
    "WdItems",
]
