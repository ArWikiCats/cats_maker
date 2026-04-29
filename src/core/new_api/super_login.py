""" """

import functools
import json
import logging
import os
import time
import urllib.parse
from http.cookiejar import MozillaCookieJar
from typing import Any

import requests

from ...config import settings
from .auth import AuthProvider
from .cookies_bot import del_cookies_file, get_file_name
from .handel_errors import HandleErrors

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1024)
def _load_session(lang: str = "", family: str = "", username: str = "") -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": settings.wikipedia.user_agent})
    return s


class Login(HandleErrors):
    """
    Represents a login session for a wiki.
    """

    def __init__(self, lang: str, family: str = "wikipedia") -> None:
        self.lang: str = lang
        self.family: str = family
        self.r3_token: str = ""
        self.user_agent: str = settings.wikipedia.user_agent
        self.endpoint: str = f"https://{self.lang}.{self.family}.org/w/api.php"
        self.cookies_file = get_file_name(self.lang, self.family, self.username)
        self.session = None
        self.auth = None
        self.auth = AuthProvider()

        self.username = getattr(self, "username", "")

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
            url_o_print = f"{self.endpoint}?{urllib.parse.urlencode(pams2)}".replace("&format=json", "")

            logger.debug(f"{url_o_print}")

    def add_users(self, Users_tables, lang=""):
        if Users_tables:
            for family, user_tab in Users_tables.items():
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
        params = self.params_w(params)

        if not self.session:
            self._make_session()

        req = self._raw_request(params, files=files, timeout=timeout)

        if not req:
            logger.debug("<<red>> no req.. ")
            return {}

        if req.headers and req.headers.get("x-database-lag"):
            logger.debug("<<red>> x-database-lag.. ")
            logger.debug(req.headers)

        data = self.parse_data(req)

        error = data.get("error", {})
        if error and do_error:
            return self.handle_err(error, "", params=params, do_error=do_error)

        return data

    def _make_session(self):
        self.make_new_session()
        self.auth = AuthProvider(self.lang, self.family, self.session)
        self.ensure_logged_in()

    def _raw_request(
        self,
        params: dict,
        files: Any = None,
        timeout: int = 30,
    ) -> requests.Response | None:
        # TODO: ('toomanyvalues', 'Too many values supplied for parameter "titles". The limit is 50.', 'See https://en.wikipedia.org/w/api.php for API usage. Subscribe to the mediawiki-api-announce mailing list at &lt;https://lists.wikimedia.org/postorius/lists/mediawiki-api-announce.lists.wikimedia.org/&gt; for notice of API deprecations and breaking changes.')

        if self.family == "mdwiki":
            timeout = 60

        args = {
            "files": files,
            "data": params,
            "timeout": timeout,
        }

        u_action = params.get("action", "")

        if settings.debug_config.do_post:
            logger.debug("<<green>> dopost:::")
            logger.debug(params)
            logger.debug("<<green>> :::dopost")
            req0 = self.session.request("POST", self.endpoint, **args)

            self._handle_server_error(req0, u_action, params=params)

            return req0

        req0 = None

        try:
            req0 = self.session.request("POST", self.endpoint, **args)

        except requests.exceptions.ReadTimeout:
            logger.debug(f"<<red>> ReadTimeout: {self.endpoint=}, {timeout=}")

        except Exception as e:
            logger.warning(f" {self.lang}.{self.family} exception for action '{u_action}': {e}")

        self._handle_server_error(req0, u_action, params=params)

        return req0

    def _handle_server_error(self, req0, action: str, params=None) -> None:
        if req0 and req0.status_code:

            if not str(req0.status_code).startswith("2"):
                logger.debug(f"<<red>>  {req0.status_code} Server Error: Server Hangup for url: {self.endpoint}")

    def post_it_parse_data(
        self,
        params: dict,
        files: Any = None,
        timeout: int = 30,
    ) -> dict:
        params = self.params_w(params)

        if not self.session:
            self._make_session()

        req = self._raw_request(params, files=files, timeout=timeout)

        if not req:
            logger.debug("<<red>> no req.. ")
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

                _load_session.cache_clear()
                self._make_session()

                return self.post_it_parse_data(params, files, timeout)

        return data

    def client_request(
        self,
        params: dict,
        method: str = "get",
        GET_CSRF: bool = True,
        files: Any = None,
        do_error: bool = False,
        max_retry: int = 0,
    ) -> dict:
        """
        Make a POST request to the API endpoint with authentication token.
        """
        if not self.r3_token:
            self.r3_token = self.auth._make_new_r3_token()

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
                    self.r3_token = self.auth._make_new_r3_token()
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
            data = self.parse_data(req)

        error = data.get("error", {})
        if error != {}:
            return self.handle_err(error, "", params=params, do_error=do_error)

        return data

    def add_User_tables(self, family, table, lang="") -> None:
        self.auth.add_User_tables(family, table, lang)

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

        return {}

    def make_new_session(self) -> None:
        logger.debug(f":({self.lang}, {self.family}, {self.username})")
        self.username_in = ""
        self.session = _load_session(lang=self.lang, family=self.family, username=self.username)

        self.cookie_jar = MozillaCookieJar(self.cookies_file)

        if os.path.exists(self.cookies_file) and self.family != "mdwiki":
            logger.debug("Load cookies from file, including session cookies")
            try:
                self.cookie_jar.load(ignore_discard=True, ignore_expires=True)
                logger.debug("We have %d cookies" % len(self.cookie_jar))

            except Exception as e:
                logger.warning(e)

        # Bind cookies once; subsequent calls for the same user reuse the same jar.
        if self.session.cookies is not self.cookie_jar:
            self.session.cookies = self.cookie_jar

    def ensure_logged_in(self) -> bool:
        logged_in = False

        if self.cookie_jar:
            if self.loged_in():
                logged_in = True
                logger.debug(f"<<green>>Cookie Already logged in with user:{self.username_in}")
        else:
            logged_in = self.log_in()

        if logged_in:
            self.cookie_jar.save(ignore_discard=True, ignore_expires=True)


__all__ = [
    "Login",
]
