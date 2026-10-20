""" """

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .loader import FilesBaseWorker

logger = logging.getLogger(__name__)

default_data = {
    "كرة القدم في إفريقيا": ["كرة القدم في أفريقيا"],
    "تاريخ إفريقيا": ["تاريخ أفريقيا"],
}

# ==========================
# FilesBaseWorker
# ==========================


class PortalAllieasWorker(FilesBaseWorker):
    def __init__(self) -> None:
        file: str = "portal_allieas.json"
        self.title = "وحدة:Portal/images/aliases"
        super().__init__(file, self.title, default_data)

    def load_data_from_text(self, text: str) -> dict:
        if not text:
            return {}
        data = {}

        pattern = r"\[(?:\"|')(?P<key>.*?)(?:\"|')\]\s*=\s*\{(?P<value>[.|\w|\W]*?)\}"

        for m in re.finditer(pattern, text):
            key = m.group("key")

            value = m.group("value")
            value = re.sub(r"\s+", " ", value)

            # ["باربادوس",]
            value = value.strip().removesuffix(",")
            value = f"[{value}]"

            try:
                data[key] = json.loads(value)
            except Exception:
                logger.exception(f"Can't load value: {value}")

        return data

    def load_new_data(self) -> dict[str, Any]:

        logger.info(f"Loading: {self.title}")

        text = self.load_text()

        data = self.load_data_from_text(text)

        return data


_local_data = {}


def portal_allieas_loader() -> dict[str, Any]:
    global _local_data

    worker = PortalAllieasWorker()

    _local_data = worker.run()

    return _local_data


__all__ = [
    "PortalAllieasWorker",
    "portal_allieas_loader",
]
