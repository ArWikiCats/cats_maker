""" """

import logging
import os
from http.cookiejar import MozillaCookieJar
from typing import Any

import requests

from ....config import settings
from .auth import AuthProvider
from .client import WikiApiClient
from .cookies_bot import get_file_name
from .handel_errors import HandleErrors

logger = logging.getLogger(__name__)


class Login(HandleErrors):

    def __init__(self, lang: str, family: str = "wikipedia") -> None:
        self.user_login: str = ""
        self.lang: str = lang
        self.family: str = family
        self.r3_token: str = ""
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

    def make_response(
        self,
        params: dict,
        files: Any = None,
        timeout: int = 30,
        do_error: bool = True,
    ) -> dict:
        return self._client.make_response(
            params=params,
            files=files,
            timeout=timeout,
            do_error=do_error,
        )

    def post_it_parse_data(
        self,
        params: dict,
        files: Any = None,
        timeout: int = 30,
    ) -> dict:
        return self._client.post_it_parse_data(
            params=params,
            files=files,
            timeout=timeout,
        )

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
        return self._client.post_params(
            params=params,
            Type=Type,
            addtoken=addtoken,
            GET_CSRF=GET_CSRF,
            files=files,
            do_error=do_error,
            max_retry=max_retry,
        )


__all__ = [
    "Login",
]
