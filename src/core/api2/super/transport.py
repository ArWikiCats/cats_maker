""" """

import functools
import logging
import os
from http.cookiejar import MozillaCookieJar
from pathlib import Path
from typing import Any

import requests
from .cookies_bot import get_file_name

from ....config import settings

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1024)
def load_session(lang: str = "", family: str = "", username: str = "") -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": settings.wikipedia.user_agent})
    return s


class Transport:
    def __init__(
        self,
        lang: str,
        family: str,
        username: str,
        cookies_file: str | Path = "",
        user_agent: str = "",
    ) -> None:
        self.lang = lang
        self.family = family
        self.username = username

        self.cookies_file = cookies_file or get_file_name(self.lang, self.family, self.username)
        self.user_agent = user_agent or settings.wikipedia.user_agent
        self.endpoint = f"https://{self.lang}.{self.family}.org/w/api.php"
        self.session: requests.Session | None = None
        self.cookie_jar: MozillaCookieJar | None = None

    def _make_session(self) -> None:
        if self.session is None:
            self.session = load_session(lang=self.lang, family=self.family, username=self.username)
        if self.cookie_jar is None:
            self.cookie_jar = MozillaCookieJar(str(self.cookies_file))
            if os.path.exists(self.cookies_file) and self.family != "mdwiki":
                try:
                    self.cookie_jar.load(ignore_discard=True, ignore_expires=True)
                    logger.debug("We have %d cookies" % len(self.cookie_jar))
                except Exception as e:
                    logger.warning(e)
            if self.session.cookies is not self.cookie_jar:
                self.session.cookies = self.cookie_jar

    def raw_request(
        self,
        params: dict,
        files: Any = None,
        timeout: int = 30,
    ) -> requests.Response | None:
        if self.family == "mdwiki":
            timeout = 60
        args = {
            "files": files,
            "headers": {"User-Agent": self.user_agent},
            "data": params,
            "timeout": timeout,
        }
        self._make_session()
        u_action = params.get("action", "")

        if settings.debug_config.do_post:
            logger.debug("<<green>> dopost:::")
            logger.debug(params)
            logger.debug("<<green>> :::dopost")
            req0 = self.session.request("POST", self.endpoint, **args)
            if req0 and req0.status_code and not str(req0.status_code).startswith("2"):
                logger.debug(f"<<red>>  {req0.status_code} Server Error: Server Hangup for url: {self.endpoint}")
            return req0

        req0 = None
        try:
            req0 = self.session.request("POST", self.endpoint, **args)
        except requests.exceptions.ReadTimeout:
            logger.debug(f"<<red>> ReadTimeout: {self.endpoint=}, {timeout=}")
        except Exception as e:
            logger.warning(f" {self.lang}.{self.family} exception for action '{u_action}': {e}")

        if req0 and req0.status_code and not str(req0.status_code).startswith("2"):
            logger.debug(f"<<red>>  {req0.status_code} Server Error: Server Hangup for url: {self.endpoint}")

        return req0

    def post_it(
        self,
        params: dict,
        files: Any = None,
        timeout: int = 30,
    ) -> requests.Response | None:
        self._make_session()
        req0 = self.raw_request(params, files=files, timeout=timeout)
        if req0 and req0.headers and req0.headers.get("x-database-lag"):
            logger.debug("<<red>> x-database-lag.. ")
            logger.debug(req0.headers)
        return req0


__all__ = [
    "Transport",
    "load_session",
]
