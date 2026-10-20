""" """

from __future__ import annotations

import logging
import sys
from typing import Any

from ...newapi import WikiLoginClient, parse_api_error
from ..utils import LagHandler, LagHandlerMaxAttemptError

logger = logging.getLogger(__name__)


class WikidataRequestHandler:
    def __init__(
        self,
        login_bot: WikiLoginClient,
        dont_do_lag_wait: bool = False,
    ) -> None:
        self.login_bot = login_bot
        self.dont_do_lag_wait = dont_do_lag_wait

        self.lang = "test" if "testwikidata" in sys.argv else "www"
        self.family = "wikidata"
        self.lag_handler = LagHandler(self.lang)

        self.username = self.login_bot.username

        # Correctly initialize parent classes
        # WPFunctions.__init__(self, self.login_bot)
        # WDFunctions.__init__(self, self.login_bot)

    def _filter_data(self, data: dict[str, Any], editgroups, tage) -> dict[str, Any]:

        if "maxlag" not in data:
            data["maxlag"] = 5

        data["format"] = "json"
        data["utf8"] = 1

        if "summary" in data:
            if self.username.find("bot") == -1:
                del data["summary"]

        # TODO: formatversion should upgrade to 2
        data.setdefault("formatversion", 1)

        return data

    def _execute_newapi_call(
        self,
        params: dict[str, Any] | None = None,
        data=None,
        tage: str = "",
        editgroups: str = "",
        max_retry: int = 0,
        **kwargs,
    ) -> dict[str, Any]:

        if data is None:
            data = {}

        if params is None:
            params = {}

        if not params and data:
            params = data

        params = self._filter_data(params, tage=tage, editgroups=editgroups)

        try:
            results = self.login_bot.client_request(
                params,
                method="get",
                max_retry=max_retry,
            )
        except Exception as e:
            logger.error(f"{e}")
            return {}

        if results.get("servedby"):
            results["servedby"] = ""

        success = results.get("success", 0)

        if success is True or success == 1:
            logger.info("<<lightgreen>> ** true.")

            return results

        error_dict = results.get("error", {})
        error_code = error_dict.get("code", "")

        if error_code == "maxlag" and max_retry < 4:
            logger.info(f"lag_work: {max_retry=}")

            self.lag_handler.update_lag_value(error_dict.get("lag", "0"))

            return self._execute_newapi_call(
                params=params,
                tage=tage,
                editgroups=editgroups,
                max_retry=max_retry + 1,
            )

        if error_dict:
            er = parse_api_error(error_dict=error_dict)
            logger.info(f"<<red>> {er}")

        return results

    # ------------------------------
    # Public API
    # ------------------------------

    def execute_wd_api_call(
        self,
        params: dict[str, Any],
        tage: str = "",
    ) -> dict[str, Any]:

        if self.lag_handler.is_bad_lag(self.dont_do_lag_wait):
            return {"success": False, "error_code": "bad_lag"}

        try:
            self.lag_handler.check_lag_status()
        except LagHandlerMaxAttemptError as exc:
            logger.error(exc.msg)
            return {"success": False, "error_code": exc.code}

        return self._execute_newapi_call(params, tage=tage)


__all__ = [
    "WikidataRequestHandler",
]
