""" """

import logging

import requests

logger = logging.getLogger(__name__)


class AuthProvider:
    def __init__(
        self,
        lang: str,
        family: str,
        session: requests.Session | None = None,
    ) -> None:
        self.lang = lang
        self.family = family
        self.username = None
        self.password = None
        self.endpoint = f"https://{lang}.{family}.org/w/api.php"
        self.session = session
        self.username_in = ""
        self.user_table_done = False

        self.cookie_jar = False

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
                self.endpoint = f"https://{lang}.{family}.org/w/api.php"

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
            r11 = self.session.request("POST", self.endpoint, data=r1_params)
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
            req = self.session.request("POST", self.endpoint, data=r2_params)
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
            req = self.session.request("POST", self.endpoint, data=params)
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


__all__ = [
    "AuthProvider",
]
