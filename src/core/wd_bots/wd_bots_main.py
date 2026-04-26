#!/usr/bin/python3
"""
!
"""
import functools
import json
import logging
import re
import time

from src.core.wd_bots.utils import do_lag, find_lag

from ...config import settings
from ..new_api.pagenew import password, username
from ..new_api.super.super_login import Login
from .utils import lag_bot

logger = logging.getLogger(__name__)

User_tables_bot = {
    "username": username,
    "password": password,
}


@functools.lru_cache(maxsize=1)
def log_in_wikidata(www="www") -> Login:
    username = User_tables_bot.get("username")
    login_bot = Login(www, family="wikidata")
    logger.debug(f"### <<purple>> make new bot for ({www}.wikidata.org|{username})")
    login_bot.add_users({"wikidata": User_tables_bot}, lang=www)
    return login_bot


class WD_API:
    def __init__(self, login_bot: Login, Mr_or_bot="bot"):

        self.login_bot = login_bot

        self.lang = "test" if settings.wikidata.test_mode else "www"
        self.family = "wikidata"

        self.usernamex = self.login_bot.user_login

        logger.warning(f"<<lightgreen>> {Mr_or_bot}, {self.usernamex=} \n")

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

            if lag_bot.newsleep[1] != 0:
                logger.warning(f"<<lightgreen>> ** true. sleep({lag_bot.newsleep[1]})")
                time.sleep(lag_bot.newsleep[1])
            else:
                logger.debug("<<lightgreen>> ** true.")
            # return True

        return results

    def filter_data(self, data):

        do_lag()

        if "maxlag" not in data:
            data["maxlag"] = lag_bot.FFa_lag[1] + 1

        data["format"] = "json"
        data["utf8"] = 1

        if "summary" in data:
            if self.usernamex.find("bot") == -1:
                del data["summary"]

        data.setdefault("formatversion", 1)

        return data


__all__ = [
    "WD_API",
]
