# ---
"""
"""
# ---
import configparser
import os
import functools

from .pages_bots.all_apis import ALL_APIS

project = "/data/project/himo"
# ---
if not os.path.isdir(project):
    project = "I:/core/bots/core1"
# ---
config = configparser.ConfigParser()
config.read(f"{project}/confs/user.ini")

username = config["DEFAULT"].get("botusername", "")
password = config["DEFAULT"].get("botpassword", "")


@functools.lru_cache(maxsize=1024)
def load_main_api(lang="ar") -> ALL_APIS:
    return ALL_APIS(
        lang=lang,
        family="wikipedia",
        username=username,
        password=password,
    )


main_api = load_main_api()
NEW_API = main_api.NEW_API
MainPage = main_api.MainPage
CatDepth = main_api.CatDepth

__all__ = [
    'MainPage',
    'NEW_API',
    'CatDepth',
]
