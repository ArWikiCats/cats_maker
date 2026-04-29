""" """

import functools
import os

from dotenv import load_dotenv

from .all_apis import ALL_APIS

load_dotenv()

username = os.getenv("WIKIPEDIA_BOT_USERNAME", "")
password = os.getenv("WIKIPEDIA_BOT_PASSWORD", "")


@functools.lru_cache(maxsize=1024)
def load_main_api(lang: str = "ar", family: str = "wikipedia") -> ALL_APIS:
    return ALL_APIS(
        lang=lang,
        family=family,
        username=username,
        password=password,
    )


@functools.lru_cache(maxsize=1024)
def load_login_bot(lang: str = "ar", family: str = "wikipedia"):
    return load_main_api(lang=lang, family=family).login_bot


__all__ = [
    "load_main_api",
    "load_login_bot",
]
