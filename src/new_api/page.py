""" """

from .api_utils import lang_codes
from .api_utils.user_agent import default_user_agent
from .super.login_wrap import LoginWrap

# ---
from .super.S_API import bot_api
from .super.S_Category import catdepth_new
from .super.S_Page import super_page
from .useraccount import User_tables_bot

SuperMainPage = super_page.MainPage
SuperNEW_API = bot_api.NEW_API
User_tables = User_tables_bot
user_agent = default_user_agent()
change_codes = lang_codes.change_codes

logins_cache = {}


def create_login_session(lang, family):
    # ---
    login_bot, logins_cache2 = LoginWrap(lang, family, logins_cache, User_tables)
    # ---
    logins_cache.update(logins_cache2)
    # ---
    return login_bot


def MainPage(title, lang, family="wikipedia") -> SuperMainPage:
    # ---
    login_bot = create_login_session(lang, family)
    # ---
    page = SuperMainPage(login_bot, title, lang, family=family)
    # ---
    return page


def CatDepth(title, sitecode="", family="wikipedia", **kwargs):
    # ---
    login_bot = create_login_session(sitecode, family)
    # ---
    result = catdepth_new.subcatquery(login_bot, title, sitecode=sitecode, family=family, **kwargs)
    # ---
    return result


def NEW_API(lang="", family="wikipedia") -> SuperNEW_API:
    # ---
    login_bot = create_login_session(lang, family)
    # ---
    result = SuperNEW_API(login_bot, lang=lang, family=family)
    # ---
    return result


__all__ = [
    "SuperNEW_API",
    "SuperMainPage",
    "user_agent",
    "MainPage",
    "NEW_API",
    "CatDepth",
    "change_codes",
]
