#!/usr/bin/python3
""" """

from __future__ import annotations

import json
import logging
import time
from typing import Any

from ....newapi import ApiResult, AskBot
from ....newapi.core.result_error import ApiResultError
from ..wd_requests_handler import WikidataRequestHandler
from .handle_response import ResponseHandler

logger = logging.getLogger(__name__)

# Rate-limit wait (seconds) applied before retrying a retryable Wikibase error.
# Kept out of the parser (``wikibase_errors.parse_wikibase_error`` is pure) and
# in the caller, per the consolidation plan.
RATE_LIMIT_WAIT = 5


class WdDescriptions(ResponseHandler):
    def __init__(
        self,
        wd_handler: WikidataRequestHandler,
        ask_bot: AskBot,
    ) -> None:
        self.ask_bot = ask_bot
        self.execute_wd_api_call = wd_handler.execute_wd_api_call

    def des_api(
        self,
        qid_str,
        desc: str,
        lang: str,
        rea: bool = True,
    ) -> ApiResult:
        """
        Set the description for a given item in a specified language.
        """

        if not desc.strip():
            logger.info("<<red>> des_api desc is empty.")
            return ApiResult.fail(code="empty_desc")

        out = f'des_api: {qid_str} description:"{lang}"@{desc}'

        sa = self.ask_bot.ask_user(
            message=f'Add desc:"{lang}:{desc}"for {qid_str} Yes or No? ',
            job="descriptions",
        )
        if not sa:
            return ApiResult.fail(code="user_abort")

        params: dict[str, Any] = {
            "action": "wbsetdescription",
            "id": qid_str,
            "language": lang,
            "value": desc,
        }
        r4 = self.execute_wd_api_call(params)

        result = self.handle_response(r4, out)

        if not result.is_ok and self._should_retry_operation(result.error) and rea:
            logger.info('<<lightred>> "reagain" (retryable) -> wait and retry ')
            time.sleep(RATE_LIMIT_WAIT)
            return self.des_api(qid_str, desc, lang, rea=False)

        return result

    def new_mult_des(
        self,
        q,
        data2,
        summary,
    ) -> ApiResult:
        data = json.JSONEncoder().encode(data2)
        logger.info("bot.new_mult_des: ")

        params: dict[str, Any] = {
            "action": "wbeditentity",
            "errorformat": "wikitext",
            "id": q,
            "summary": summary,
            "data": data,
        }

        r4 = self.execute_wd_api_call(params)
        out = summary
        return self.handle_response(r4, out)

    def _new_mult_des_2(
        self,
        qid: str,
        data: dict[str, Any],
        summary: str | None = None,
        tage: str = "",
    ) -> ApiResult:

        logger.info(f"<<lightblue>> bot.new_mult_des_2:q:{qid}")

        encoded_data = json.JSONEncoder().encode(data)  # type: ignore

        paramse = {
            "action": "wbeditentity",
            "id": qid,
            "summary": summary or "",
            "data": str(encoded_data),
        }

        r4 = self.execute_wd_api_call(paramse, tage=tage)

        out = f"new_mult_des_2: {summary}"

        return self.handle_response(r4, out)

    def new_mult_des_2(
        self,
        qid: str,
        data: dict[str, Any],
        summary: str | None = None,
        rea: bool = True,
        tage: str = "",
    ) -> ApiResult:

        logger.info(f"<<lightblue>> bot.new_mult_des_2:q:{qid}")

        sa = self.ask_bot.ask_user(
            message=f'<<lightyellow>> new_mult_des_2 "{qid}" <<lightgreen>> (Yes or No?) ',
            job="descriptions",
        )
        if not sa:
            return ApiResult.fail(code="user_abort")

        result = self._new_mult_des_2(
            qid=qid,
            data=data,
            summary=summary,
            tage=tage,
        )

        if not result.is_ok and self._should_retry_operation(result.error) and rea:
            logger.info('<<lightred>> "reagain" (retryable) -> wait and retry ')
            time.sleep(RATE_LIMIT_WAIT)

            return self._new_mult_des_2(
                qid=qid,
                data=data,
                summary=summary,
                tage=tage,
            )

        return result

    def _should_retry_operation(self, error: ApiResultError | None) -> bool:
        """
        TODO: compare should_retry_operation between WdDescriptions and WdLabels
        """
        return error is not None and getattr(error, "is_retryable", False)


__all__ = [
    "WdDescriptions",
]
