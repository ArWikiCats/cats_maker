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

from ....config import settings
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
        self.user_login: str = ""
        self.lang: str = lang
        self.family: str = family
        self.r3_token: str = ""
        self.username_in: str = ""
        self.cookies_file: str = ""
        self.user_agent: str = settings.wikipedia.user_agent
        self.endpoint: str = f"https://{self.lang}.{self.family}.org/w/api.php"
        self.headers = {"User-Agent": self.user_agent}

        self.cookie_jar = False
        self.session = None
        self.username = getattr(self, "username", "")
        self.password = ""
        self.user_table_done = False

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
        params = self.params_w(params)

        if not self.session:
            self.make_new_session()

        if not self.username_in:
            logger.debug("<<red>> no username_in.. action:" + params.get("action"))

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

    def _raw_request(
        self,
        params: dict,
        files: Any = None,
        timeout: int = 30,
    ) -> requests.Response | None:
        # TODO: ('toomanyvalues', 'Too many values supplied for parameter "titles". The limit is 50.', 'See https://en.wikipedia.org/w/api.php for API usage. Subscribe to the mediawiki-api-announce mailing list at &lt;https://lists.wikimedia.org/postorius/lists/mediawiki-api-announce.lists.wikimedia.org/&gt; for notice of API deprecations and breaking changes.')

        if not self.user_table_done:
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
            self.make_new_session()

        if not self.username_in:
            logger.debug("<<red>> no username_in.. action:" + params.get("action"))

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

                self.username_in = ""
                _load_session.cache_clear()
                self.make_new_session()

                return self.post_it_parse_data(params, files, timeout)

        return data

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
            data = self.parse_data(req)

        error = data.get("error", {})
        if error != {}:
            return self.handle_err(error, "", params=params, do_error=do_error)

        return data

    def add_User_tables(self, family, table, lang="") -> None:
        langx = self.lang

        # for example family=toolforge, lang in (medwiki, mdwikicx)
        if lang and not self.family.startswith("wik"):
            langx = lang

        if table["username"].find("bot") == -1 and family == "wikipedia":
            logger.info(f": {family=}, {table['username']=}")

        if family != "" and table["username"] != "" and table["password"] != "":
            if self.family == family or (langx == "ar" and self.family.startswith("wik")):  # wiktionary
                self.user_table_done = True

                self.username = table["username"]
                self.password = table["password"]

    def _make_new_r3_token(self) -> str:
        r3_params = {
            "format": "json",
            "action": "query",
            "meta": "tokens",
        }

        req = self.post_it_parse_data(r3_params) or {}

        if not req:
            return False

        csrftoken = req.get("query", {}).get("tokens", {}).get("csrftoken", "")

        return csrftoken

    def log_in(self) -> bool:
        """
        Log in to the wiki and get authentication token.
        """
        # time.sleep(0.5)
        logger.debug(f"<<yellow>> {self.endpoint}")
        logger.debug(f"page.py: log to {self.lang}.{self.family}.org user:{self.username})")

        logintoken = self.get_logintoken()

        if not logintoken:
            return False

        success = self.get_login_result(logintoken, self.username, self.password)

        if success:
            logger.debug("<<green>> new_api login Success")
            return True
        else:
            return False

    def get_logintoken(self) -> str:
        r1_params = {
            "format": "json",
            "action": "query",
            "meta": "tokens",
            "type": "login",
        }

        # WARNING: /data/project/himo/core/bots/page.py:101: UserWarning: Exception:502 Server Error: Server Hangup for url: https://ar.wikipedia.org/w/api.php

        try:
            r11 = self.session.request("POST", self.endpoint, data=r1_params, headers=self.headers)
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

    def get_login_result(self, logintoken: str, username: str, password: str) -> bool:
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
            req = self.session.request("POST", self.endpoint, data=r2_params, headers=self.headers)
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
            self.loged_in()
            return True

        reason = result.get("login", {}).get("reason", "")

        if reason == "Incorrect username or password entered. Please try again.":
            logger.debug(f"user:{username}, pass:******")

        return False

    def loged_in(self) -> bool:
        params = {
            "format": "json",
            "action": "query",
            "meta": "userinfo",
            "uiprop": "groups|rights",
        }

        req = ""
        try:
            req = self.session.request("POST", self.endpoint, data=params, headers=self.headers)
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
        # logger.debug(json1)

        if "anon" in userinfo or "temp" in userinfo:
            return False

        self.username_in = userinfo.get("name", "")

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
        logger.debug(f":({self.lang}, {self.family}, {self.username})")

        self.session = _load_session(lang=self.lang, family=self.family, username=self.username)

        self.cookies_file = get_file_name(self.lang, self.family, self.username)

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

        self.ensure_logged_in()

    def ensure_logged_in(self) -> bool:
        logged_in = False

        if len(self.cookie_jar) > 0:
            if self.loged_in():
                logged_in = True
                logger.debug(f"<<green>>Cookie Already logged in with user:{self.username_in}")
        else:
            logged_in = self.log_in()

        if logged_in:
            self.cookie_jar.save(ignore_discard=True, ignore_expires=True)

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


__all__ = [
    "Login",
]
