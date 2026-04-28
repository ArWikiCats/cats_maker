""" """

import json
import logging
import os
import time
import urllib.parse
from http.cookiejar import MozillaCookieJar
from typing import Any

import requests

from ....config import settings
from .cookies_bot import del_cookies_file, get_file_name
from .transport import load_session

logger = logging.getLogger(__name__)


class WikiApiClient:
    def __init__(
        self,
        lang: str,
        family: str,
        username: str,
        password: str = "",
        user_agent: str = "",
    ) -> None:
        self.lang = lang
        self.family = family
        self.username = username
        self.password = password
        self.user_agent = user_agent or settings.wikipedia.user_agent
        self.endpoint = f"https://{lang}.{family}.org/w/api.php"
        self.session: requests.Session | None = None
        self.cookies_file = ""
        self.username_in = ""
        self.user_table_done = False
        self.r3_token = ""

        self.session = load_session(lang=lang, family=family, username=username)
        self.cookies_file = str(get_file_name(lang, family, username))

        if self.session and hasattr(self.session, "cookies"):

            self.session.cookies = MozillaCookieJar(self.cookies_file)
            if os.path.exists(self.cookies_file):
                try:
                    self.session.cookies.load(ignore_discard=True, ignore_expires=True)
                except Exception:
                    pass

    def params_w(self, params: dict) -> dict:
        params = dict(params)
        if (
            self.family == "wikipedia"
            and self.lang == "ar"
            and params.get("summary")
            and self.username.find("bot") == -1
        ):
            params["summary"] = ""

        params["bot"] = 1

        if "minor" in params and params["minor"] == "":
            params["minor"] = 1

        if self.family != "toolforge":
            if (
                params["action"] in ["edit", "create", "upload", "delete", "move"]
                or params["action"].startswith("wb")
                or self.family == "wikidata"
            ):
                if not settings.bot.no_login and self.username:
                    params["assertuser"] = self.username

        return params

    def parse_data(self, req0: requests.Response | dict) -> dict:
        """
        Parse JSON response data.
        """
        text = ""
        try:
            data = req0 if isinstance(req0, dict) else req0.json()

            if data.get("error", {}).get("*", "").find("mailing list") > -1:
                data["error"]["*"] = ""
            if data.get("servedby"):
                data["servedby"] = ""

            return data
        except Exception as e:
            logger.warning(f"<<red>> Error parsing response data: {e}")
            text = str(getattr(req0, "text", "").strip())

        valid_text = text.startswith("{") and text.endswith("}")

        if not text or not valid_text:
            return {}

        try:
            return json.loads(text)
        except Exception as e:
            logger.warning(e)
            logger.warning(self.url_o_print)

        return {}

    def filter_params(self, params: dict) -> dict:
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
            url_o_print = f"{self.endpoint}?{urllib.parse.urlencode(pams2)}".replace("&format=json", "")
            logger.debug(url_o_print)

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

        if not self.session:

            self.session = load_session(lang=self.lang, family=self.family, username=self.username)

        req = self.session.request("POST", self.endpoint, data=self.params_w(params), files=files, timeout=timeout)

        if req:
            data = self.parse_data(req)

        error = data.get("error", {})
        if error and do_error:
            return self._handle_error(error, "", params=params, do_error=do_error)

        return data

    def _handle_error(
        self,
        error: dict,
        function: str = "",
        params: dict | None = None,
        do_error: bool = True,
    ) -> dict | str:
        err_code = error.get("code", "")
        err_info = error.get("info", "")

        if err_code == "abusefilter-disallowed":
            abusefilter = error.get("abusefilter", "")
            description = abusefilter.get("description", "") if abusefilter else ""
            logger.debug(f"<<lightred>> ** abusefilter-disallowed: {description} ")
            if description in [
                "تأخير البوتات 3 ساعات",
                "تأخير البوتات 3 ساعات- 3 من 3",
                "تأخير البوتات 3 ساعات- 1 من 3",
                "تأخير البوتات 3 ساعات- 2 من 3",
            ]:
                return False
            return description

        if err_code in ("no-such-entity", "protectedpage", "maxlag"):
            return False

        if err_code == "articleexists":
            return "articleexists"

        if do_error:
            if params:
                params["data"] = {}
                params["text"] = {}
            logger.error(f"<<lightred>>{function} ERROR: <<defaut>>info: {err_info}, {params=}")
            if settings.bot.raise_err:
                raise Exception(f"{function} ERROR: {err_info}")

        return error

    def post_it_parse_data(
        self,
        params: dict,
        files: Any = None,
        timeout: int = 30,
    ) -> dict:
        params = self.params_w(params)
        if not self.session:

            self.session = load_session(lang=self.lang, family=self.family, username=self.username)

        # req = self.session.request("POST", self.endpoint, data=params, files=files, timeout=timeout)
        req = self._raw_request(params, files=files, timeout=timeout)

        if not req:
            logger.debug("<<red>> no req0.. ")
            return {}

        if req.headers and req.headers.get("x-database-lag"):
            logger.debug("<<red>> x-database-lag.. ")
            logger.debug(req.headers)

        data = self.parse_data(req) or {}

        error = data.get("error", {})

        # {'code': 'assertnameduserfailed', 'info': 'You are no longer logged in as "Mr. Ibrahem", ....', '*': ''}

        if error:
            code = error.get("code", "")
            if code == "assertnameduserfailed":
                logger.warning("assertnameduserfailed" * 10)

                del_cookies_file(self.cookies_file)
                self.username_in = ""
                self.session = None
                return self.post_it_parse_data(params, files, timeout)

        return data

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

    def post_params(
        self,
        params: dict,
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
            self.r3_token = self._make_new_r3_token()

        if not self.r3_token:
            logger.warning('<<red>> self.r3_token == "" ')
            return {}

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
                    self.r3_token = self._make_new_r3_token()
                    continue

            if error_code == "maxlag" and max_retry < 4:
                lage = int(error.get("lag", "0"))
                logger.debug(params)
                logger.debug(f"<<purple>>: <<red>> {lage=} {max_retry=}, sleep: {lage + 1}")

                sleep_time = min(2**attempt + lage, 30)
                time.sleep(sleep_time)

                params["maxlag"] = lage + 1
                max_retry += 1
                continue

            return data

        return {}

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

        req = self._client.session.request(
            "POST", self.endpoint, data=self.params_w(params), files=files, timeout=timeout
        )

        if req:
            data = self._client.parse_data(req)

        error = data.get("error", {})
        if error != {}:
            return self.handle_err(error, "", params=params, do_error=do_error)

        return data


__all__ = [
    "WikiApiClient",
]
