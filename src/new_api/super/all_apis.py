""" """

import functools
import logging

from . import catdepth_new, super_page
from .super_login import Login

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1024)
def _login(lang, family, username) -> Login:
    login_bot = Login(lang, family=family)
    logger.info(f"### <<purple>> make new bot for ({lang}.{family}.org|{username})")
    return login_bot


class ALL_APIS:
    """
    A class that provides access to various API functionalities.
    Usage:
        from newapi import ALL_APIS
        main_api = ALL_APIS(lang='en', family='wikipedia', username='your_username', password='your_password')
        page = main_api.MainPage('Main Page Title')
        cat_members = main_api.CatDepth('Category Title')
    """

    def __init__(self, lang, family, username, password) -> None:
        self.lang = lang
        self.family = family
        self.username = username
        self.password = password
        self.login_bot = self._login()

    def MainPage(self, title, *args, **kwargs) -> super_page.MainPage:
        return super_page.MainPage(self.login_bot, title, self.lang, family=self.family)

    def CatDepth(self, title, sitecode="", family="", *args, **kwargs):
        # cat_members = CatDepth("RTTNEURO", sitecode="www", family="mdwiki", depth=3, ns="0")
        return catdepth_new.subcatquery(self.login_bot, title, sitecode=self.lang, family=self.family, **kwargs)

    def _login(self) -> Login:
        bot = _login(self.lang, self.family, self.username)
        user_tables = {
            self.family: {
                "username": self.username,
                "password": self.password,
            }
        }
        bot.add_users(user_tables, lang=self.lang)
        return bot


__all__ = [
    "ALL_APIS",
]
