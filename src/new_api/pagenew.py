""" """

import functools
import os

from dotenv import load_dotenv

from .super.all_apis import ALL_APIS

load_dotenv()

username = os.getenv("WIKIPEDIA_BOT_USERNAME", "")
password = os.getenv("WIKIPEDIA_BOT_PASSWORD", "")


@functools.lru_cache(maxsize=1024)
def load_main_api(lang="ar", family="wikipedia") -> ALL_APIS:
    return ALL_APIS(
        lang=lang,
        family=family,
        username=username,
        password=password,
    )


main_api = load_main_api()
MainPage = main_api.MainPage
CatDepth = main_api.CatDepth

__all__ = [
    "MainPage",
    "CatDepth",
]
