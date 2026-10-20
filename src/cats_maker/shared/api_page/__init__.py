""" """

from __future__ import annotations

import functools
import logging
import os
import sys

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def _load_bot_credentials() -> tuple[str, str]:
    return (
        os.getenv("WIKIPEDIA_BOT_USERNAME", ""),
        os.getenv("WIKIPEDIA_BOT_PASSWORD", ""),
    )


@functools.lru_cache(maxsize=1)
def _load_himo_credentials() -> tuple[str, str]:
    return (
        os.getenv("WIKIPEDIA_HIMO_USERNAME", ""),
        os.getenv("WIKIPEDIA_HIMO_PASSWORD", ""),
    )


def load_credentials(mr_or_bot: str | None = None) -> tuple[str, str]:
    if mr_or_bot is None:
        mr_or_bot = "mr" if "workibrahem" in sys.argv else "bot"

    if mr_or_bot == "mr":
        return _load_himo_credentials()
    return _load_bot_credentials()


__all__ = [
    "load_credentials",
]
