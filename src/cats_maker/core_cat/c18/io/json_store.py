#!/usr/bin/python3
"""File I/O helpers for the module."""

from __future__ import annotations

import json
import logging
import os
import stat
from datetime import datetime
from functools import cached_property
from pathlib import Path

from ....config import Settings
from ..infrastructure.sql.ar_lists import ArCategorySQL

logger = logging.getLogger(__name__)

_STATGROUP = stat.S_IRWXU | stat.S_IRWXG


class JsonStore:
    """Simple JSON file store with stale detection."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self, empty_data="dict") -> list | dict:
        path = self.path

        data: list | dict = [] if empty_data != "dict" else {}

        if not path.is_file():
            logger.warning(f"File not found: {path}")
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                os.chmod(path, _STATGROUP)
            except (PermissionError, OSError):
                logger.exception("Error save json file")

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error in {path}: {e}")
        except (PermissionError, OSError) as e:
            logger.warning(f"Error reading {path}: {e}")

        return data

    def save(self, data: list | dict) -> None:
        path = self.path
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
                logger.info(f"wrote to {path}")
        except PermissionError:
            logger.error(f"PermissionError writing to {path}")
            try:
                os.remove(path)
            except (PermissionError, OSError):
                pass
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                os.chmod(path, _STATGROUP)
                logger.info(f"wrote to {path}")
            except (PermissionError, OSError) as e:
                logger.warning(f"Error deleting/writing to {path}: {e}")
        except (OSError, Exception) as e:
            logger.warning(f"Error writing to {path}: {e}")

    def is_stale(self, days: int = 1) -> bool:
        if not self.path.exists():
            return True
        last_modified = datetime.fromtimestamp(os.path.getmtime(self.path))
        return (datetime.now() - last_modified).days >= days


class DontAddStore:
    """JSON file store for the list of pages that should not be categorised."""

    def __init__(
        self,
        wiki_query_service: ArCategorySQL | None = None,
        store: JsonStore | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.wiki_query_service = wiki_query_service or ArCategorySQL()
        self.store: JsonStore | None = store
        self.settings = settings or Settings.get_instance()

        _FILENAME_JSON = self.settings.paths.dont_add_to_pages_path

        if _FILENAME_JSON and self.store is None:
            _filename_json = Path(_FILENAME_JSON)
            self.store = JsonStore(_filename_json)

    def should_skip(self) -> bool:
        if self.settings.category.no_dontadd or self.settings.category.test_mode:
            return True

        if not self.settings.category.test_add:
            if self.settings.is_production():
                logger.info("dont get dontadd list in local server")
                return True

        return False

    @cached_property
    def _load(self) -> list[str]:
        """Return the list of pages that should not be categorised.

        Uses a local JSON cache; refreshes from SQL once per day.
        """
        if self.should_skip():
            return []

        if self.store is None:
            return []

        data = self.store.load()

        last_modified = ""
        if self.store.path.exists():
            modified_time = os.path.getmtime(self.store.path)
            last_modified = datetime.fromtimestamp(modified_time).strftime("%Y-%m-%d")

        today = datetime.today().strftime("%Y-%m-%d")

        if last_modified != today or not data:
            logger.info(f"last modified: {last_modified}, today: {today}, len: {len(data)}")
            data = self.wiki_query_service.fetch_dont_add_pages()
            self.store.save(data)

        if not data:
            logger.info("dont_list is empty")

        return data if isinstance(data, list) else []

    def get_dont_add_pages(self) -> list[str]:
        return self._load


__all__ = [
    "JsonStore",
    "DontAddStore",
]
