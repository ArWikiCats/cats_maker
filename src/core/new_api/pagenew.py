""" """

import functools
import os

from dotenv import load_dotenv

from .super import ALL_APIS, Login

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


@functools.lru_cache(maxsize=1024)
def load_login_bot(lang="ar", family="wikipedia") -> Login:
    return load_main_api(lang=lang, family=family).login_bot


__all__ = [
    "load_main_api",
    "load_login_bot",
]
