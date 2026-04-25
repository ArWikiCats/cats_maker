""" """

import copy
import logging
import time
import urllib.parse

from ...config import settings
from .bot import LOGIN_HELPS
from .handel_errors import HANDEL_ERRORS

logger = logging.getLogger(__name__)

ar_lag = {1: 3}
urls_prints = {"all": 0}


class Login(LOGIN_HELPS, HANDEL_ERRORS):
    """
    Represents a login session for a wiki.
    """

    def __init__(self, lang, family="wikipedia"):
        self.user_login = ""
        self.lang = lang
        self.family = family
        self.r3_token = ""
        self.url_o_print = ""
        self.user_agent = settings.wikipedia.user_agent
        self.endpoint = f"https://{self.lang}.{self.family}.org/w/api.php"
        super().__init__()

    def filter_params(self, params):
        """
        Filter out unnecessary parameters.
        """
        params["format"] = "json"
        params["utf8"] = 1

        if params["action"] in ["query"]:
            if "bot" in params:
                del params["bot"]
            if "summary" in params:
                del params["summary"]

        params.setdefault("formatversion", "1")

        return params

    def add_users(self, Users_tables, lang=""):
        if Users_tables:
            for family, user_tab in Users_tables.items():
                self.user_login = user_tab.get("username")
                self.add_User_tables(family, user_tab, lang=lang)

    def p_url(self, params):
        """
        Print the URL for debugging purposes.
        """
        if settings.debug_config.print_url:
            no_url = ["lgpassword", "format"]
            no_remove = ["titles", "title"]
            pams2 = {
                k: v[:100] if isinstance(v, str) and len(v) > 100 and k not in no_remove else v
                for k, v in params.items()
                if k not in no_url
            }
            self.url_o_print = f"{self.endpoint}?{urllib.parse.urlencode(pams2)}".replace("&format=json", "")
            if self.url_o_print not in urls_prints:
                urls_prints[self.url_o_print] = 0
            urls_prints[self.url_o_print] += 1
            urls_prints["all"] += 1
            logger.debug(f"c: {urls_prints[self.url_o_print]}/{urls_prints['all']}\t {self.url_o_print}")

    def make_response(
        self,
        params,
        files=None,
        timeout=30,
        do_error=True,
    ):
        """
        Make a POST request to the API endpoint.
        """
        self.p_url(params)

        data = {}

        if params.get("list") == "querypage":
            timeout = 60
        req = self.post_it(params, files, timeout)

        if req:
            data = self.parse_data(req)

        error = data.get("error", {})

        if error != {}:
            er = self.handel_err(error, "", params=params, do_error=do_error)
            if do_error:
                return er

        return data

    def post_params(
        self,
        params,
        Type="get",
        addtoken=False,
        GET_CSRF=True,
        files=None,
        do_error=False,
        max_retry=0,
    ):
        """
        Make a POST request to the API endpoint with authentication token.
        """
        if not self.r3_token:
            self.r3_token = self.make_new_r3_token()

        if not self.r3_token:
            logger.warning('<<red>> self.r3_token == "" ')

        params["token"] = self.r3_token

        params = self.filter_params(params)

        data = self.make_response(params, files=files, do_error=do_error)

        if not data:
            logger.debug("<<red>> super_login(post): not data. return {}.")
            return {}

        error = data.get("error", {})

        if error != {}:
            return self.error_do(data, GET_CSRF, params, Type, addtoken, max_retry)

        return data

    def error_do(self, data, GET_CSRF, params, Type, addtoken, max_retry):
        error = data.get("error", {})

        Invalid = error.get("info", "")
        error_code = error.get("code", "")

        logger.debug(f"<<red>> super_login(post): error: {error}")

        if Invalid == "Invalid CSRF token.":
            logger.debug(f'<<red>> ** error "Invalid CSRF token.".\n{self.r3_token} ')
            if GET_CSRF:
                self.r3_token = None
                return self.post_params(params, Type=Type, addtoken=addtoken, GET_CSRF=False)

        error_code = error.get("code", "")

        if error_code == "maxlag" and max_retry < 4:
            lage = int(error.get("lag", "0"))
            logger.debug(params)
            logger.debug(f"<<purple>>: <<red>> {lage=} {max_retry=}, sleep: {lage + 1}")
            time.sleep(lage + 1)
            ar_lag[1] = lage + 1
            params["maxlag"] = ar_lag[1]
            return self.post_params(
                params,
                Type=Type,
                addtoken=addtoken,
                max_retry=max_retry + 1,
            )

        return data

    def post_continue(
        self,
        params,
        action,
        _p_="pages",
        p_empty=None,
        Max=500000,
        first=False,
        _p_2="",
        _p_2_empty=None,
    ):
        logger.debug("_______________________")
        logger.debug(f", start. {action=}, {_p_=}")
        if not isinstance(Max, int) and Max.isdigit():
            Max = int(Max)
        if Max == 0:
            Max = 500000
        p_empty = p_empty or []
        _p_2_empty = _p_2_empty or []
        results = p_empty
        continue_params = {}
        d = 0
        while continue_params != {} or d == 0:
            params2 = copy.deepcopy(params)
            d += 1
            if continue_params:
                logger.debug("continue_params:")
                for k, v in continue_params.items():
                    params2[k] = v
                logger.debug(params2)
            json1 = self.post_params(params2)
            if not json1:
                logger.debug(", json1 is empty. break")
                break
            continue_params = {}
            if action == "wbsearchentities":
                data = json1.get("search", [])
            else:
                continue_params = json1.get("continue", {})
                data = json1.get(action, {}).get(_p_, p_empty)
                if _p_ == "querypage":
                    data = data.get("results", [])
                elif first:
                    if isinstance(data, list) and len(data) > 0:
                        data = data[0]
                        if _p_2:
                            data = data.get(_p_2, _p_2_empty)
            if not data:
                logger.debug("post continue, data is empty. break")
                break
            logger.debug(f"post continue, len:{len(data)}, all: {len(results)}")
            if Max <= len(results) and len(results) > 1:
                logger.debug(f"post continue, {Max=} <= {len(results)=}. break")
                break
            if isinstance(results, list):
                results.extend(data)
            else:
                print(f"{type(results)=}")
                print(f"{type(data)=}")
                results = {**results, **data}
        logger.debug(f"post continue, {len(results)=}")
        return results
