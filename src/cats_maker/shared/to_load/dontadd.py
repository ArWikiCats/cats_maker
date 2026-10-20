#!/usr/bin/python3
""" """

from __future__ import annotations

import logging
import sys
from typing import Any

from ...database import WikiReplicaDB
from ..petscan import PetScanService
from .loader import FilesBaseWorker

logger = logging.getLogger(__name__)

default_data: dict[str, Any] = {}


def from_sql() -> list[str]:
    queries = """select page_title, page_namespace
        from page, templatelinks, linktarget
        where page_id = tl_from
        and page_namespace in (0, 10)
        and tl_target_id = lt_id
        and lt_namespace = 10
        and lt_title = "لا_للتصنيف_المعادل"
        ;"""

    cats: list = []

    if WikiReplicaDB.can_use_sql():
        db = WikiReplicaDB.load("arwiki")
        result = db.select_safe(queries)
        for row in result:
            page_title = row["page_title"]
            page_namespace = row["page_namespace"]

            if page_namespace == 10:
                page_title = f"قالب:{page_title}"
            cats.append(page_title)

    return cats


def from_petscan() -> list[str]:

    params: dict[str, Any] = {
        "ns": [0, 10],
        "templates_yes": "لا للتصنيف المعادل",
        "lang": "ar",
        "family": "wikipedia",
    }

    dd = PetScanService().search(params)

    cats: list = [x.replace("_", " ") for x in dd.keys()]
    return cats


# ==========================
# FilesBaseWorker
# ==========================


class DontAddWorker(FilesBaseWorker):
    def __init__(self) -> None:
        file: str = "dont_add_to_pages.json"
        super().__init__(file, "", default_data)

    def load_new_data(self) -> dict[str, bool]:

        encats = from_sql()

        if not encats or len(encats) == 0:
            encats = from_petscan()

        data = dict.fromkeys(encats, True)

        return data


_local_data = {}


def dont_add_pages_loader() -> dict[str, Any]:
    global _local_data

    if "nodontadd" in sys.argv:
        return {}

    worker = DontAddWorker()

    _local_data = worker.run()

    return _local_data


__all__ = [
    "DontAddWorker",
    "from_sql",
    "from_petscan",
    "dont_add_pages_loader",
]
