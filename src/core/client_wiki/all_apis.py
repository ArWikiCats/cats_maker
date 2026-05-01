""" """

import logging

from ..api_client import WikiLoginClient
from .categories import catdepth_new
from .pages import super_page

logger = logging.getLogger(__name__)


class ALL_APIS:
    """
    A class that provides access to various API functionalities.
    """

    def __init__(self, lang: str, family: str, username: str, password: str) -> None:
        self.lang = lang
        self.family = family
        self.username = username
        self.password = password
        self.login_bot = self._login()

    def MainPage(self, title: str, *args, **kwargs) -> super_page.MainPage:
        return super_page.MainPage(self.login_bot, title, self.lang, family=self.family)

    def CatDepth(self, title: str, sitecode: str = "", family: str = "", *args, **kwargs):
        return catdepth_new.subcatquery(self.login_bot, title, sitecode=self.lang, family=self.family, **kwargs)

    def _login(self) -> WikiLoginClient:
        client = WikiLoginClient(
            lang=self.lang,
            family=self.family,
            username=self.username,
            password=self.password,
        )
        return client


__all__ = [
    "ALL_APIS",
]
