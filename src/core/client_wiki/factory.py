""" """

import logging
import functools
import os

from dotenv import load_dotenv

from .all_apis import AllAPIS
from ..api_client import WikiLoginClient

logger = logging.getLogger(__name__)

try:
    load_dotenv()
except Exception:
    logger.info("Failed to load environment variables from .env file.")


@functools.lru_cache(maxsize=1)
def _load_credentials() -> tuple[str, str]:
    username = os.getenv("WIKIPEDIA_BOT_USERNAME", "")
    password = os.getenv("WIKIPEDIA_BOT_PASSWORD", "")
    return username, password


@functools.lru_cache(maxsize=1024)
def load_main_api(
    lang: str = "ar",
    family: str = "wikipedia",
) -> AllAPIS:
    """
    Loads and returns an instance of AllAPIS for the specified language and family, using cached credentials.
    Args:
        lang (str): The language code for the API (e.g., 'en', 'fr').
        family (str, optional): The family of the API (default is 'wikipedia').

    Returns:
        AllAPIS: An instance of the AllAPIS class initialized with the provided language, family, and user credentials.

    Notes:
        - The result of this function is cached with an LRU cache of size 1.
        - Credentials are loaded internally via the _load_credentials() function.
    """
    username, password = _load_credentials()
    return AllAPIS(
        lang=lang,
        family=family,
        username=username,
        password=password,
    )


@functools.lru_cache(maxsize=1024)
def load_login_bot(lang: str = "ar", family: str = "wikipedia") -> WikiLoginClient:
    username, password = _load_credentials()
    return WikiLoginClient(
        lang=lang,
        family=family,
        username=username,
        password=password,
    )


__all__ = [
    "load_main_api",
    "load_login_bot",
]
