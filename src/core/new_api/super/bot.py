""" """

import functools
import logging
import os
from http.cookiejar import MozillaCookieJar

import requests

from ....config import settings
from .cookies_bot import del_cookies_file, get_file_name
from .params_help import PARAMS_HELPS

logger = logging.getLogger(__name__)

users_by_lang = {}
logins_count = {1: 0}


@functools.lru_cache(maxsize=1024)
def _load_session(lang: str = "", family: str = "", username: str = "") -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": settings.wikipedia.user_agent})
    return s


class LOGIN_HELPS(PARAMS_HELPS):
    def __init__(self) -> None:
        self.cookie_jar = False
        self.session = None

        self.username = getattr(self, "username", "")
        self.family = getattr(self, "family", "")
        self.lang = getattr(self, "lang", "")

        self.endpoint = getattr(self, "endpoint", f"https://{self.lang}.{self.family}.org/w/api.php")

        self.connection = None

        self.password = ""
        self.username_in = ""
        self.cookies_file = ""
        self.user_table_done = False
        self.user_agent = settings.wikipedia.user_agent
        self.headers = {"User-Agent": self.user_agent}

        super().__init__()

    def log_error(self, result, action, params=None) -> None:
        if result not in ["success", 200]:
            logger.error(
                f"page.py: {self.lang}.{self.family}.org user:{self.username}, action:{action}, result:{result}"
            )

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

    def make_new_r3_token(self) -> str:

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

        colors = {"ar": "yellow", "en": "lightpurple"}

        color = colors.get(self.lang, "")

        logins_count[1] += 1
        logger.debug(f"<<{color}>> {self.endpoint} count:{logins_count[1]}")
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

            self.log_error(r11.status_code, "logintoken")

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

    def get_login_result(self, logintoken, username, password) -> bool:
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

        r22 = {}

        if req:
            try:
                r22 = req.json()
            except Exception as e:
                logger.warning(
                    f" {self.lang}.{self.family} error parsing login response: {e} - response: {getattr(req, 'text', '')}"
                )
                logger.debug(req.text)
                return False

        login_result = r22.get("login", {}).get("result", "")

        success = login_result.lower() == "success"

        self.log_error(login_result, "login")

        if success:
            self.loged_in()
            return True

        reason = r22.get("login", {}).get("reason", "")

        # logger.warning(r22)

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
            self.log_error("failed", "userinfo")
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

        self.log_error(result_x, "userinfo")

        # logger.debug(json1)

        if "anon" in userinfo or "temp" in userinfo:
            return False

        self.username_in = userinfo.get("name", "")
        users_by_lang[self.lang] = self.username_in

        return True

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

        loged_t = False

        if len(self.cookie_jar) > 0:
            if self.loged_in():
                loged_t = True
                logger.debug(f"<<green>>Cookie Already logged in with user:{self.username_in}")
        else:
            loged_t = self.log_in()

        if loged_t:
            self.cookie_jar.save(ignore_discard=True, ignore_expires=True)

    def _handle_server_error(self, req0, action, params=None):
        if req0 and req0.status_code:

            self.log_error(req0.status_code, action, params=params)

            if not str(req0.status_code).startswith("2"):
                logger.debug(f"<<red>>  {req0.status_code} Server Error: Server Hangup for url: {self.endpoint}")

    def raw_request(self, params, files=None, timeout=30):

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
            self.log_error("ReadTimeout", u_action, params=params)
            logger.debug(f"<<red>> ReadTimeout: {self.endpoint=}, {timeout=}")

        except Exception as e:
            self.log_error("Exception", u_action, params=params)
            logger.warning(f" {self.lang}.{self.family} exception for action '{u_action}': {e}")

        self._handle_server_error(req0, u_action, params=params)

        return req0

    def post_it(self, params, files=None, timeout=30):

        params = self.params_w(params)

        if not self.username_in:
            self.username_in = users_by_lang.get(self.lang, "")

        if not self.session:
            self.make_new_session()

        if not self.username_in:
            logger.debug("<<red>> no username_in.. action:" + params.get("action"))
            # return {}

        req0 = self.raw_request(params, files=files, timeout=timeout)

        if not req0:
            logger.debug("<<red>> no req0.. ")
            return req0

        if req0.headers and req0.headers.get("x-database-lag"):
            logger.debug("<<red>> x-database-lag.. ")
            logger.debug(req0.headers)
            # raise

        return req0

    def post_it_parse_data(self, params, files=None, timeout=30) -> dict:

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

                del_cookies_file(self.cookies_file)

                self.username_in = ""
                _load_session.cache_clear()
                self.make_new_session()

                return self.post_it_parse_data(params, files, timeout)

        return data
