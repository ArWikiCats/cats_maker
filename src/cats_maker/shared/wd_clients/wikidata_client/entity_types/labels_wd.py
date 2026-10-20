#!/usr/bin/python3
"""
POST bot - Labels functionality

This module provides functions for working with labels in Wikidata.
"""

from __future__ import annotations

import logging
from typing import Any

from ....newapi import ApiResult
from ..wd_requests_handler import WikidataRequestHandler
from .handle_response import ResponseHandler

logger = logging.getLogger(__name__)


class WdLabels(ResponseHandler):
    def __init__(self, wd_handler: WikidataRequestHandler) -> None:
        self.execute_wd_api_call = wd_handler.execute_wd_api_call

    def add_label_qid(
        self,
        qid: str,
        label: str,
        lang: str,
        number: int = 0,
        tage: str = "",
    ) -> ApiResult:

        if not qid:
            logger.info("qid == '' ")
            return ApiResult.fail(code="qid == ''")

        if label == "":
            logger.info("label == ''")
            return ApiResult.fail(code="empty_label")

        # save the edit
        out = f'{qid} label:"{lang}"@{label}.'

        if number:
            out = f'{number} {qid} label:"{lang}"@{label}.'

        params: dict[str, Any] = {
            "action": "wbsetlabel",
            "id": qid,
            "language": lang,
            "value": label,
        }
        r4 = self.execute_wd_api_call(params, tage=tage)

        result = self.handle_response(r4, out)

        return result

    def add_label_by_site(
        self,
        label: str,
        lang: str,
        enlink: str,
        ensite: str,
    ) -> ApiResult:

        if enlink == "" or ensite == "":
            logger.info('<<lightred>> **add_label: False: enlink == "" or ensite == "".')
            return ApiResult.fail(code="enlink == '' or ensite == ''")

        out = f'{ensite}:{enlink} label:"{lang}"@{label}.'

        params: dict[str, Any] = {
            "action": "wbsetlabel",
            "site": ensite,
            "title": enlink,
            "language": lang,
            "value": label,
        }

        r4 = self.execute_wd_api_call(params)
        result = self.handle_response(r4, out)

        return result

    def remove_label(
        self,
        qid: str,
        lang: str,
        tage: str = "",
    ) -> ApiResult:

        if not qid:
            logger.info("qid == '' ")
            return ApiResult.fail(code="qid == ''")

        # save the edit
        out = f"remove {qid} label for {lang=}"

        params: dict[str, Any] = {
            "action": "wbsetlabel",
            "id": qid,
            "language": lang,
            "value": "",
        }
        r4 = self.execute_wd_api_call(params, tage=tage)

        result = self.handle_response(r4, out)
        return result


__all__ = [
    "WdLabels",
]
