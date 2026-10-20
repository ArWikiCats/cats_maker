#!/usr/bin/python3
""" """

from __future__ import annotations

import logging
import re
from typing import Any

from .loader import FilesBaseWorker

logger = logging.getLogger(__name__)

default_data = {
    "cite av media": "استشهاد بوسائط مرئية ومسموعة",
    "cite book": "استشهاد بكتاب",
    "cite document": "استشهاد بدورية محكمة",
    "cite encyclopedia": "استشهاد بموسوعة",
    "cite interview": "استشهاد بمقابلة",
    "cite journal": "استشهاد بدورية محكمة",
    "cite magazine": "استشهاد بمجلة",
    "cite news": "استشهاد بخبر",
    "cite newspaper": "استشهاد بخبر",
    "cite press release": "استشهاد ببيان صحفي",
    "cite press": "استشهاد ببيان صحفي",
    "cite pressrelease": "استشهاد ببيان صحفي",
    "cite publication": "استشهاد بكتاب",
    "cite report": "استشهاد بتقرير",
    "cite tech report": "استشهاد بتقرير فني",
    "cite tweet": "استشهاد بتغريدة",
    "cite web": "استشهاد بويب",
    "cite work": "استشهاد بكتاب",
}

# ==========================
# FilesBaseWorker
# ==========================


class RenameTempsWorker(FilesBaseWorker):
    def __init__(self) -> None:
        file: str = "rename_templates.json"
        self.title = "ويكيبيديا:AutoWikiBrowser/Template_redirects"
        super().__init__(file, self.title, default_data)

    def load_data_from_text(self, text: str) -> dict:
        if not text:
            return {}

        text = text.replace("{{قا|", "{{tl|")
        lines = text.split("\n")

        data = {}

        for line in lines:
            fas = re.match(r"^\*\s*(.*)\s*\→\s*\'\'\'\s*\{\{tl\s*\|\s*(.*?)\}\}\s*\'\'\'$", line)
            if fas:
                other = fas.group(1).split(",")
                ma = fas.group(2)
                for o in other:
                    mat = re.match(r"^\{\{tl\s*\|\s*(.*?)\}\}$", o.strip())
                    if mat and mat.group(1):
                        data[mat.group(1).lower()] = ma

        return data

    def load_new_data(self) -> dict[str, Any]:

        logger.info(f"Loading: {self.title}")

        text = self.load_text()

        data = self.load_data_from_text(text)

        return data


_local_data = {}


def rename_temps_loader() -> dict[str, Any]:
    global _local_data

    worker = RenameTempsWorker()

    _local_data = worker.run()

    return _local_data


__all__ = [
    "RenameTempsWorker",
    "rename_temps_loader",
]
