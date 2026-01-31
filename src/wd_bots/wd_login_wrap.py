""" """

# ---
import functools

from ..config import settings
from ..new_api import LoginWrap
from ..new_api.pagenew import password, username

User_tables_bot = {
    "username": username,
    "password": password,
}


@functools.lru_cache(maxsize=1)
def log_in_wikidata(www="www"):
    # ---
    users_data = User_tables_bot
    # ---
    www2 = "test" if settings.wikidata.test_mode else "www"
    # ---
    if www != "www":
        www2 = www
    # ---
    login_bot, _ = LoginWrap(www2, "wikidata", {}, users_data)
    # ---
    return login_bot
