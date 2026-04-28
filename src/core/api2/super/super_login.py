""" """

import logging
import os
import time
import urllib.parse
from http.cookiejar import MozillaCookieJar
from typing import Any

import requests

from ....config import settings
from .client import WikiApiClient
from .cookies_bot import del_cookies_file, get_file_name
from .handel_errors import HandleErrors

logger = logging.getLogger(__name__)


class Login(HandleErrors):
    _users_by_lang: dict[str, str] = {}
    _logins_count: int = 0

    def __init__(self, lang: str, family: str = "wikipedia") -> None:
        self.user_login: str = ""
        self.lang: str = lang
        self.family: str = family
        self.r3_token: str = ""
        self.url_o_print: str = ""
        self.user_agent: str = settings.wikipedia.user_agent
        self.endpoint: str = f"https://{self.lang}.{self.family}.org/w/api.php"

        self._client = WikiApiClient(
            lang=lang,
            family=family,
            username="",
            password="",
            user_agent=self.user_agent,
        )
        self._client.lang = lang
        self._client.family = family
        self._url_counts: dict[str, int] = {}
        self._ar_lag: int = 3
        self.headers = {"User-Agent": self.user_agent}

    @property
    def session(self):
        return self._client.session

    @session.setter
    def session(self, value):
        self._client.session = value

    def add_users(self, Users_tables: dict, lang: str = "") -> None:
        if Users_tables:
            for family, user_tab in Users_tables.items():
                self.user_login = user_tab.get("username", "")
                self._client.add_User_tables(family, user_tab, lang=lang)

    def add_User_tables(self, family: str, table: dict, lang: str = "") -> None:
        self._client.add_User_tables(family, table, lang=lang)

    def params_w(self, params: dict) -> dict:
        return self._client.params_w(params)

    def parse_data(self, req0) -> dict:
        return self._client.parse_data(req0)

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
            self.url_o_print = f"{self.endpoint}?{urllib.parse.urlencode(pams2)}".replace("&format=json", "")

            if self.url_o_print not in self._url_counts:
                self._url_counts[self.url_o_print] = 0

            self._url_counts[self.url_o_print] += 1
            self._url_counts["all"] = self._url_counts.get("all", 0) + 1

            logger.debug(f"c: {self._url_counts[self.url_o_print]}/{self._url_counts['all']}\t {self.url_o_print}")

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

    def post_it(self, params, files: Any = None, timeout: int = 30):
        params = self.params_w(params)

        if not self._client.session:
            self._client.session = self._make_session()

        if not self._client.username_in:
            logger.debug("<<red>> no username_in.. action:" + params.get("action"))

        req0 = self._raw_request(params, files=files, timeout=timeout)

        if not req0:
            logger.debug("<<red>> no req0.. ")
            return req0

        if req0.headers and req0.headers.get("x-database-lag"):
            logger.debug("<<red>> x-database-lag.. ")
            logger.debug(req0.headers)

        return req0

    def _make_session(self) -> requests.Session:
        from .transport import load_session

        load_session.cache_clear()
        self._client.session = load_session(lang=self.lang, family=self.family, username=self._client.username)
        self._client.cookies_file = str(get_file_name(self.lang, self.family, self._client.username))
        return self._client.session

    def _raw_request(self, params, files: Any = None, timeout: int = 30):
        # TODO: ('toomanyvalues', 'Too many values supplied for parameter "titles". The limit is 50.', 'See https://en.wikipedia.org/w/api.php for API usage. Subscribe to the mediawiki-api-announce mailing list at &lt;https://lists.wikimedia.org/postorius/lists/mediawiki-api-announce.lists.wikimedia.org/&gt; for notice of API deprecations and breaking changes.')
        if not self._client.session:
            self._make_session()

        if not self._client.user_table_done:
            logger.debug("<<green>> user_table_done == False!")

        if self.family == "mdwiki":
            timeout = 60

        args = {
            "files": files,
            "headers": self.headers,
            "data": params,
            "timeout": timeout,
        }

        u_action = params.get("action", "")

        if settings.debug_config.do_post:
            logger.debug("<<green>> dopost:::")
            logger.debug(params)
            logger.debug("<<green>> :::dopost")
            req0 = self._client.session.request("POST", self.endpoint, **args)
            self._handle_server_error(req0, u_action, params=params)
            return req0

        req0 = None
        try:
            req0 = self._client.session.request("POST", self.endpoint, **args)
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

    def post_it_parse_data(self, params, files: Any = None, timeout: int = 30) -> dict:
        req = self.post_it(params, files, timeout)
        data = {}

        if req:
            data = self.parse_data(req) or {}

        error = data.get("error", {})

        # {'code': 'assertnameduserfailed', 'info': 'You are no longer logged in as "Mr. Ibrahem", ....', '*': ''}

        if error:
            code = error.get("code", "")
            if code == "assertnameduserfailed":
                logger.warning("assertnameduserfailed" * 10)

                del_cookies_file(self._client.cookies_file)
                self._client.username_in = ""
                self._client.session = None
                self._make_session()
                return self.post_it_parse_data(params, files, timeout)

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

    def log_in(self) -> bool:
        """
        Log in to the wiki and get authentication token.
        """
        from .transport import load_session

        Login._logins_count += 1
        logger.debug(f"<<yellow>> {self.endpoint} count:{Login._logins_count}")
        logger.debug(f"page.py: log to {self.lang}.{self.family}.org user:{self._client.username})")

        if not self._client.session:
            self._client.session = load_session(lang=self.lang, family=self.family, username=self._client.username)

        logintoken = self._get_logintoken()
        if not logintoken:
            return False
        return self._get_login_result(logintoken, self._client.username, self._client.password)

    def _get_logintoken(self) -> str:
        r1_params = {
            "format": "json",
            "action": "query",
            "meta": "tokens",
            "type": "login",
        }

        # WARNING: /data/project/himo/core/bots/page.py:101: UserWarning: Exception:502 Server Error: Server Hangup for url: https://ar.wikipedia.org/w/api.php

        try:
            r11 = self._client.session.request("POST", self.endpoint, data=r1_params, headers=self.headers)
            if not str(r11.status_code).startswith("2"):
                logger.debug(f"<<red>>  {r11.status_code} Server Error: Server Hangup for url: {self.endpoint}")
        except Exception as e:
            logger.warning(f"<<red>> Error getting login token: {e}")
            return ""

        jsson1 = {}
        try:
            jsson1 = r11.json()
        except Exception as e:
            logger.debug(r11.text)
            logger.warning(f"<<red>> Error getting login token: {e}")
            return ""

        return jsson1.get("query", {}).get("tokens", {}).get("logintoken") or ""

    def _get_login_result(self, logintoken: str, username: str, password: str) -> bool:
        if not password:
            logger.debug("No password")
            return False

        r2_params = {
            "format": "json",
            "action": "login",
            "lgname": username,
            "lgpassword": password,
            "lgtoken": logintoken,
        }
        req = ""
        try:
            req = self._client.session.request("POST", self.endpoint, data=r2_params, headers=self.headers)
        except Exception as e:
            logger.warning(f" {self.lang}.{self.family} login request exception: {e}")
            return False

        result = {}
        if req:
            try:
                result = req.json()
            except Exception as e:
                logger.warning(
                    f" {self.lang}.{self.family} error parsing login response: {e} - response: {getattr(req, 'text', '')}"
                )
                logger.debug(req.text)
                return False

        login_result = result.get("login", {}).get("result", "")
        success = login_result.lower() == "success"

        if success:
            self._logged_in()
            return True

        reason = result.get("login", {}).get("reason", "")
        if reason == "Incorrect username or password entered. Please try again.":
            logger.debug(f"user:{username}, pass:******")

        return False

    def _logged_in(self) -> bool:
        params = {
            "format": "json",
            "action": "query",
            "meta": "userinfo",
            "uiprop": "groups|rights",
        }
        req = ""
        try:
            req = self._client.session.request("POST", self.endpoint, data=params, headers=self.headers)
        except Exception as e:
            logger.warning(f" {self.lang}.{self.family} userinfo request exception: {e}")
            return False

        json1 = {}
        if req:
            try:
                json1 = req.json()
            except Exception as e:
                logger.warning(
                    f" {self.lang}.{self.family} error parsing userinfo response: {e} - response: {getattr(req, 'text', '')}"
                )
                logger.debug(req.text)
                return False

        userinfo = json1.get("query", {}).get("userinfo", {})
        result_x = "success" if userinfo else "failed"

        if "anon" in userinfo or "temp" in userinfo:
            return False

        self._client.username_in = userinfo.get("name", "")
        return True

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

    def make_new_session(self) -> None:
        from .transport import load_session

        logger.debug(f":({self.lang}, {self.family}, {self._client.username})")
        self._client.session = load_session(lang=self.lang, family=self.family, username=self._client.username)
        self._client.cookies_file = str(get_file_name(self.lang, self.family, self._client.username))

        self._client.session.cookies = MozillaCookieJar(self._client.cookies_file)

        if os.path.exists(self._client.cookies_file) and self.family != "mdwiki":
            logger.debug("Load cookies from file, including session cookies")
            try:
                self._client.session.cookies.load(ignore_discard=True, ignore_expires=True)
                logger.debug("We have %d cookies" % len(self._client.session.cookies))
            except Exception as e:
                logger.warning(e)

        if self._client.session.cookies is not self._client.session.cookies:
            pass
        self.ensure_logged_in()

    def ensure_logged_in(self) -> bool:
        logged_in = False
        if len(self._client.session.cookies) > 0:
            if self._logged_in():
                logged_in = True
                logger.debug(f"<<green>>Cookie Already logged in with user:{self._client.username_in}")
        else:
            logged_in = self.log_in()
        if logged_in and hasattr(self.session, "cookies"):
            try:
                self._client.session.cookies.save(ignore_discard=True, ignore_expires=True)
            except Exception:
                pass


__all__ = [
    "Login",
]
