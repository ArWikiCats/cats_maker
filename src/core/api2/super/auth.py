""" """

import logging
from typing import Any

import requests

from ....config import settings

logger = logging.getLogger(__name__)


class AuthProvider:
    def __init__(
        self,
        lang: str,
        family: str,
        username: str,
        password: str = "",
        endpoint: str = "",
        user_agent: str = "",
        session: requests.Session | None = None,
        cookies_file: str = "",
    ) -> None:
        self.lang = lang
        self.family = family
        self.username = username
        self.password = password
        self.endpoint = endpoint or f"https://{lang}.{family}.org/w/api.php"
        self.user_agent = user_agent or settings.wikipedia.user_agent
        self.session = session
        self.cookies_file = cookies_file
        self.headers = {"User-Agent": self.user_agent}
        self.username_in = ""
        self.user_table_done = False

    def set_session(self, session: requests.Session) -> None:
        self.session = session

    def log_in(self) -> bool:
        logintoken = self._get_logintoken()
        if not logintoken:
            return False
        return self._get_login_result(logintoken, self.username, self.password)

    def _get_logintoken(self) -> str:
        r1_params = {
            "format": "json",
            "action": "query",
            "meta": "tokens",
            "type": "login",
        }
        try:
            r11 = self.session.request("POST", self.endpoint, data=r1_params, headers=self.headers)
            if not str(r11.status_code).startswith("2"):
                logger.debug(f"<<red>>  {r11.status_code} Server Error: Server Hangup for url: {self.endpoint}")
        except Exception as e:
            logger.warning(f"<<red>> Error getting login token: {e}")
            return ""

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
        if "anon" in userinfo or "temp" in userinfo:
            return False

        self.username_in = userinfo.get("name", "")
        return True

    def make_new_r3_token(self) -> str:
        r3_params = {
            "format": "json",
            "action": "query",
            "meta": "tokens",
        }
        req = self.session.request("POST", self.endpoint, data=r3_params, headers=self.headers)
        if not req:
            return ""
        try:
            jsson = req.json()
        except Exception:
            return ""
        return jsson.get("query", {}).get("tokens", {}).get("csrftoken", "") or ""

    def add_User_tables(self, family: str, table: dict, lang: str = "") -> None:
        langx = self.lang
        if lang and not self.family.startswith("wik"):
            langx = lang

        if family != "" and table["username"] != "" and table["password"] != "":
            if self.family == family or (langx == "ar" and self.family.startswith("wik")):
                self.user_table_done = True
                self.username = table["username"]
                self.password = table["password"]

    def ensure_logged_in(self) -> bool:
        from .transport import load_session

        if not self.session:
            self.session = load_session(lang=self.lang, family=self.family, username=self.username)

        if len(getattr(self.session.cookies, "_cookies", {}).get(".wikipedia.org", {}).get("/w/", [])) > 0:
            if self._logged_in():
                logger.debug(f"<<green>>Cookie Already logged in with user:{self.username_in}")
                return True

        logged_in = self.log_in()
        if logged_in and hasattr(self.session, "cookies"):
            try:
                self.session.cookies.save(ignore_discard=True, ignore_expires=True)
            except Exception:
                pass
        return logged_in


__all__ = [
    "AuthProvider",
]