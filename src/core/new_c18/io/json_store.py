#!/usr/bin/python3
"""File I/O helpers for the module."""

from __future__ import annotations

import json
import logging
import os
import stat
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from ....config import settings
from .sql_queries import fetch_dont_add_pages

logger = logging.getLogger(__name__)

_FILENAME_JSON = settings.dont_add_to_pages_path
_STATGROUP = stat.S_IRWXU | stat.S_IRWXG


def _load_json(path: Path, empty_data: str = "list") -> list | dict:
    data: list | dict = [] if empty_data != "dict" else {}

    if not path.is_file():
        logger.warning(f"File not found: {path}")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            os.chmod(path, _STATGROUP)
        except (PermissionError, OSError) as e:
            logger.exception("Error save json file")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error in {path}: {e}")
    except (PermissionError, OSError) as e:
        logger.warning(f"Error reading {path}: {e}")

    return data


def _save_json(data: list | dict, path: Path) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            logger.info(f"<<green>> wrote to {path}")
    except PermissionError:
        logger.error(f"<<red>> PermissionError writing to {path}")
        try:
            os.remove(path)
        except (PermissionError, OSError):
            pass
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            os.chmod(path, _STATGROUP)
            logger.info(f"<<green>> wrote to {path}")
        except (PermissionError, OSError) as e:
            logger.warning(f"<<red>> Error deleting/writing to {path}: {e}")
    except (OSError, Exception) as e:
        logger.warning(f"<<red>> Error writing to {path}: {e}")


class JsonStore:
    """Simple JSON file store with stale detection."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> list | dict:
        return _load_json(self.path)

    def save(self, data: list | dict) -> None:
        _save_json(data, self.path)

    def is_stale(self, days: int = 1) -> bool:
        if not self.path.exists():
            return True
        last_modified = datetime.fromtimestamp(os.path.getmtime(self.path))
        return (datetime.now() - last_modified).days >= days


@lru_cache(maxsize=1)
def get_dont_add_pages() -> list[str]:
    """Return the list of pages that should not be categorised.

    Uses a local JSON cache; refreshes from SQL once per day.
    """
    if settings.category.no_dontadd or settings.category.test_mode:
        return []

    if not settings.category.test_add:
        if settings.is_production():
            logger.info("dont get dontadd list in local server")
            return []

    if not _FILENAME_JSON:
        return []

    _filename_json = Path(_FILENAME_JSON)

    store = JsonStore(_filename_json)
    data = store.load()

    last_modified = ""
    if _filename_json.exists():
        last_modified = datetime.fromtimestamp(os.path.getmtime(_filename_json)).strftime("%Y-%m-%d")

    today = datetime.today().strftime("%Y-%m-%d")

    if last_modified != today or not data:
        logger.info(f"<<purple>> last modified: {last_modified}, today: {today}, len: {len(data)}")
        data = fetch_dont_add_pages()
        store.save(data)

    if not data:
        logger.info("dont_list is empty")

    return data if isinstance(data, list) else []
