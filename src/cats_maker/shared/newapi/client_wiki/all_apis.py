""" """

from __future__ import annotations

import logging
from typing import Any

from ....config import Settings
from ..api_client import WikiLoginClient
from .bot_api import NewApi
from .categories import catdepth_new
from .pages import super_page

logger = logging.getLogger(__name__)


class AllAPIS:
    """
    A class that provides access to various API functionalities.
    """

    def __init__(
        self,
        lang: str,
        family: str,
        login_bot: WikiLoginClient,
        use_cookies: bool = True,
        cookies_dir: None | str = None,
    ) -> None:
        self.lang = lang
        self.family = family
        self.use_cookies = use_cookies
        self.cookies_dir = cookies_dir
        self.login_bot = login_bot

    def mainpage(self, title: str, *args, **kwargs) -> super_page.MainPage:
        return super_page.MainPage(self.login_bot, title, self.lang, family=self.family)

    def main_page_solve_redirect(
        self,
        title: str,
        *args,
        **kwargs,
    ) -> super_page.MainPage:
        page = super_page.MainPage(self.login_bot, title, self.lang, family=self.family)

        if page.is_redirect():
            target = page.get_redirect_target()
            if target:
                return super_page.MainPage(
                    self.login_bot,
                    target,
                    self.lang,
                    family=self.family,
                )

        return page

    def catdepth(
        self,
        title: str,
        **kwargs,
    ) -> dict[Any, Any]:
        return catdepth_new.subcatquery(
            self.login_bot,
            title,
            site_code=self.lang,
            family=self.family,
            **kwargs,
        )

    def newapi(self, *args, **kwargs) -> NewApi:
        return NewApi(self.login_bot, lang=self.lang, family=self.family)

    def client_request_safe(
        self,
        params: dict[str, Any],
        method: str = "get",
        files=None,
        **kwargs,
    ) -> dict[str, Any]:

        return self.login_bot.client_request_safe(
            params,
            method=method,
            files=files,
            **kwargs,
        )

    @classmethod
    def load(cls, lang: str, family: str = "wikipedia") -> AllAPIS:
        main_settings = Settings.get_instance()

        username, password = main_settings.wikipedia.load_credentials("bot")

        login_bot = WikiLoginClient.load(
            username=username,
            password=password,
            lang=lang,
            family=family,
        )
        return cls(
            lang=lang,
            family=family,
            login_bot=login_bot,
        )

    @classmethod
    def load_arwiki(cls) -> AllAPIS:
        return cls.load(lang="ar", family="wikipedia")


__all__ = [
    "AllAPIS",
]
