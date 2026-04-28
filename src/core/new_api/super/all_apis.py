""" """

import functools
import logging

from . import catdepth_new, super_page
from .super_login import Login

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1024)
def _login(lang: str, family: str, username: str) -> Login:
    login_bot = Login(lang, family=family)
    logger.info(f"### <<purple>> make new bot for ({lang}.{family}.org|{username})")
    return login_bot


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
