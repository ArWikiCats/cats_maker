""" """

import logging
import time
from typing import Any
import urllib.parse

from ....config import settings
from .handel_errors import HandleErrors
from .bot import LOGIN_HELPS

logger = logging.getLogger(__name__)

ar_lag = {1: 3}


class Login(LOGIN_HELPS, HandleErrors):
    """
    Represents a login session for a wiki.
    """
    _logins_count: int = 0

    def __init__(self, lang: str, family: str = "wikipedia") -> None:
        self.user_login: str = ""
        self.lang: str = lang
        self.family: str = family
        self.r3_token: str = ""
        self.url_o_print: str = ""
        self.user_agent: str = settings.wikipedia.user_agent
        self.endpoint: str = f"https://{self.lang}.{self.family}.org/w/api.php"
        self._url_counts: dict[str, int] = {}
        self.headers = {"User-Agent": self.user_agent}
        super().__init__()

    def filter_params(self, params: dict) -> dict:
        """
        Filter out unnecessary parameters.
        """
        params["format"] = "json"
        params["utf8"] = 1

        if params.get("action") == "query":
            if "bot" in params:
                del params["bot"]
            if "summary" in params:
                del params["summary"]

        params.setdefault("formatversion", "1")
        return params

    def p_url(self, params: dict) -> None:
        if settings.debug_config.print_url:
            no_url = ["lgpassword", "format"]
            no_remove = ["titles", "title"]
            pams2 = {
                k: v[:100] if isinstance(v, str) and len(v) > 100 and k not in no_remove else v
                for k, v in params.items()
                if k not in no_url
            }
            self.url_o_print = f"{self.endpoint}?{urllib.parse.urlencode(pams2)}".replace("&format=json", "")

            if self.url_o_print not in self._url_counts:
                self._url_counts[self.url_o_print] = 0

            self._url_counts[self.url_o_print] += 1
            self._url_counts["all"] = self._url_counts.get("all", 0) + 1

            logger.debug(f"c: {self._url_counts[self.url_o_print]}/{self._url_counts['all']}\t {self.url_o_print}")

    def add_users(self, Users_tables, lang=""):
        if Users_tables:
            for family, user_tab in Users_tables.items():
                self.user_login = user_tab.get("username")
                self.add_User_tables(family, user_tab, lang=lang)

    def make_response(
        self,
        params: dict,
        files: Any = None,
        timeout: int = 30,
        do_error: bool = True,
    ) -> dict:
        self.p_url(params)
        data = {}

        if params.get("list") == "querypage":
            timeout = 60
        req = self.post_it(params, files, timeout)

        if req:
            data = self.parse_data(req)

        error = data.get("error", {})
        if error and do_error:
            return self.handle_err(error, "", params=params, do_error=do_error)

        return data

    def post_params(
        self,
        params,
        Type: str = "get",
        addtoken: bool = False,
        GET_CSRF: bool = True,
        files: Any = None,
        do_error: bool = False,
        max_retry: int = 0,
    ) -> dict:
        """
        Make a POST request to the API endpoint with authentication token.
        """
        if not self.r3_token:
            self.r3_token = self.make_new_r3_token()

        if not self.r3_token:
            logger.warning('<<red>> self.r3_token == "" ')

        params["token"] = self.r3_token
        params = self.filter_params(params)

        for attempt in range(5):
            data = self._make_response_impl(params, files=files, do_error=do_error)

            if not data:
                logger.debug("<<red>> super_login(post): not data. return {}.")
                return {}

            error = data.get("error", {})
            if not error:
                return data

            Invalid = error.get("info", "")
            error_code = error.get("code", "")

            logger.debug(f"<<red>> super_login(post): error: {error}")

            if Invalid == "Invalid CSRF token.":
                logger.debug(f'<<red>> ** error "Invalid CSRF token.".\n{self.r3_token} ')
                if GET_CSRF:
                    self.r3_token = ""
                    self.r3_token = self._make_new_r3_token()
                    continue

            if error_code == "maxlag" and max_retry < 4:
                lage = int(error.get("lag", "0"))
                logger.debug(params)
                logger.debug(f"<<purple>>: <<red>> {lage=} {max_retry=}, sleep: {lage + 1}")

                sleep_time = min(2**attempt + lage, 30)
                time.sleep(sleep_time)

                self._ar_lag = lage + 1
                params["maxlag"] = self._ar_lag
                max_retry += 1
                continue

            return data

        return {}

    def _make_new_r3_token(self) -> str:
        r3_params = {
            "format": "json",
            "action": "query",
            "meta": "tokens",
        }
        req = self.post_it_parse_data(r3_params) or {}
        if not req:
            return ""
        return req.get("query", {}).get("tokens", {}).get("csrftoken", "") or ""

    def _make_response_impl(
        self,
        params,
        files: Any = None,
        do_error: bool = True,
    ) -> dict:
        self.p_url(params)
        data = {}

        if params.get("list") == "querypage":
            timeout = 60
        else:
            timeout = 30

        if not self._client.session:
            self._make_session()

        req = self._client.session.request("POST", self.endpoint, data=self.params_w(params), files=files, timeout=timeout)

        if req:
            data = self.parse_data(req)

        error = data.get("error", {})
        if error != {}:
            return self.handle_err(error, "", params=params, do_error=do_error)

        return data


__all__ = [
    "Login",
]
