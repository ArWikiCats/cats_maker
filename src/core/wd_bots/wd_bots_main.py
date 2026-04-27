#!/usr/bin/python3
"""
!
"""

import logging
import time

from ...config import settings
from ..new_api import Login
from .lag_bot import do_lag, find_lag, get_lag_value, get_new_sleep

logger = logging.getLogger(__name__)


class WD_API:
    def __init__(self, login_bot: Login):
        self.login_bot = login_bot

        self.lang = "test" if settings.wikidata.test_mode else "www"
        self.family = "wikidata"

    def handle_err_wd(
        self,
        error: dict,
        function: str = "",
        params: dict | None = None,
    ):
        """Handle errors related to the specified function.

        This method processes an error dictionary returned from an API call,
        extracting relevant error codes and information. It outputs error
        messages based on the error code and may modify the provided parameters.
        The function handles specific error codes such as 'abusefilter-
        disallowed', 'no-such-entity', 'protectedpage', 'articleexists', and
        'maxlag', providing appropriate responses for each case.

        Args:
            error (dict): A dictionary containing error information from the API.
            function (str?): The name of the function that encountered the error.
                Defaults to an empty string.
            params (dict?): A dictionary of parameters that may be modified
                based on the error. Defaults to None.

        Returns:
            Union[str, bool]: Returns a string indicating the error type for specific
                errors or False for others.

        Raises:
            Exception: If the 'raise' argument is present in the command line arguments,
                an exception is raised with the error information.
        """

        # {'error': {'code': 'articleexists', 'info': 'The article you tried to create has been created already.', '*': 'See https://ar.wikipedia.org/w/api.php for API usage. Subscribe to the mediawiki-api-announce mailing list at &lt;https://lists.wikimedia.org/postorius/lists/mediawiki-api-announce.lists.wikimedia.org/&gt; for notice of API deprecations and breaking changes.'}, 'servedby': 'mw1425'}

        err_code = error.get("code", "")
        err_info = error.get("info", "")

        tt = f"<<lightred>>{function} ERROR: <<defaut>>code:{err_code}."
        logger.debug(tt)
        # ---["protectedpage", 'تأخير البوتات 3 ساعات', False]
        if err_code == "abusefilter-disallowed":
            # oioioi = {'error': {'code': 'abusefilter-disallowed', 'info': 'This', 'abusefilter': {'id': '169', 'description': 'تأخير البوتات 3 ساعات', 'actions': ['disallow']}, '*': 'See https'}, 'servedby': 'mw1374'}

            abusefilter = error.get("abusefilter", "")
            description = abusefilter.get("description", "")
            logger.debug(f"<<lightred>> ** abusefilter-disallowed: {description} ")
            if description in [
                "تأخير البوتات 3 ساعات",
                "تأخير البوتات 3 ساعات- 3 من 3",
                "تأخير البوتات 3 ساعات- 1 من 3",
                "تأخير البوتات 3 ساعات- 2 من 3",
            ]:
                return False
            return description

        if err_code == "no-such-entity":
            logger.debug("<<lightred>> ** no-such-entity. ")
            return False

        if err_code == "protectedpage":
            logger.debug("<<lightred>> ** protectedpage. ")
            # return "protectedpage"
            return False

        if err_code == "articleexists":
            logger.debug("<<lightred>> ** article already created. ")
            return "articleexists"

        if err_code == "maxlag":
            logger.debug("<<lightred>> ** maxlag. ")
            return False

        if params is not None:
            params["data"] = {}

        logger.debug(f"<<lightred>>{function} ERROR: <<defaut>>info: {err_info}, {params=}")

    def post_to_newapi(
        self,
        params=None,
        data=None,
        max_retry=0,
        **kwargs,
    ):
        if params is None:
            params = {}
        if data is None:
            data = {}
        if not params and data:
            params = data

        params = self.filter_data(params)

        results = self.login_bot.post_params(params, do_error=False)

        if results.get("servedby"):
            results["servedby"] = ""

        error = results.get("error", {})
        error_code = error.get("code", "")

        if error_code == "maxlag" and max_retry < 4:
            find_lag(error)

            logger.debug(f"<<purple>>: <<red>> lag work: {max_retry=}")

            return self.post_to_newapi(params=params, max_retry=max_retry + 1)

        if error:
            er = self.handle_err_wd(error, function="", params=params)

            logger.debug(f"<<purple>>: <<red>> handle_err_wd: {er}")
            # return er

        success = results.get("success", 0)

        if success == 1:
            # {"entity":{"sitelinks":{"arwiki":{}},"id":"Q97928551","type":"item","lastrevid":1242627521,"nochange":""},"success":1}

            if get_new_sleep() != 0:
                logger.warning(f"<<lightgreen>> ** true. sleep({get_new_sleep()})")
                time.sleep(get_new_sleep())
            else:
                logger.debug("<<lightgreen>> ** true.")
            # return True

        return results

    def filter_data(self, data):
        do_lag()

        if "maxlag" not in data:
            data["maxlag"] = get_lag_value() + 1

        data["format"] = "json"
        data["utf8"] = 1

        data.setdefault("formatversion", 1)

        return data


__all__ = [
    "WD_API",
]
