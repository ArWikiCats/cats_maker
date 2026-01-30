""" """

# ---
from ..config import settings
from ..new_api import LoginWrap, User_tables_bot

logins_cache = {}


def log_in_wikidata(Mr_or_bot="bot", www="www"):
    # ---
    users_data = User_tables_bot
    # ---
    www2 = "test" if settings.wikidata.test_mode else "www"
    # ---
    if www != "www":
        www2 = www
    # ---
    login_bot, logins_cache2 = LoginWrap(www2, "wikidata", logins_cache, users_data)
    # ---
    logins_cache.update(logins_cache2)
    # ---
    print(logins_cache)
    # ---
    return login_bot
