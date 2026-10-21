#!/usr/bin/python3
"""File I/O helpers for the module."""

from __future__ import annotations

import json
import logging
import os
import stat
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_STATGROUP = stat.S_IRWXU | stat.S_IRWXG


class JsonStore:
    """Simple JSON file store with stale detection."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self, empty_data="list") -> list | dict:
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
                logger.exception("Error saving JSON file")

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


__all__ = [
    "JsonStore",
]
