#!/usr/bin/python3
""" """

from __future__ import annotations

import logging
from typing import Any

import wikitextparser as wtp

from .loader import FilesBaseWorker

logger = logging.getLogger(__name__)

default_data = {
    "USCongRep-start": {"state": "الولاية", "congresses": "الكونجرس"},
    "USCongRep-row": {"state": "الولاية", "congress": "الكونجرس", "senators": "الشيوخ", "representatives": "النواب"},
    "معلومات انتخابات": {
        "after_party": "الحزب_بعد",
        "after_election": "بعد_الانتخاب",
        "before_party": "الحزب_قبل",
        "before_election": "قبل_الانتخاب",
        "party1": "حزب1",
        "image1": "صورة1",
        "leader1": "قائد1",
    },
}

default_data["uscongrep-start"] = default_data["USCongRep-start"]
default_data["uscongrep-row"] = default_data["USCongRep-row"]


def gt_argv(temp, x) -> str:
    if temp.has_arg(x):
        arg = temp.get_arg(x)
        if arg and arg.value and arg.value.strip():
            return arg.value.strip()

    return ""


def get_new_params(text: str) -> dict:
    """
    text lines example:
    * <code>{{AWB rename template parameter|مرجع ويب|journal|صحيفة}}</code>
    """

    new_params: dict[str, dict[str, str]] = {}

    parsed = wtp.parse(text)

    for template in parsed.templates:
        if not template:
            continue

        template_name = str(template.normal_name()).strip()

        if template_name.lower() != "awb rename template parameter":
            continue

        te = gt_argv(template, "1").lower().strip()

        if not te:
            continue

        if te not in new_params:
            new_params[te] = {}

        item_from = gt_argv(template, "2").strip()
        item_to = gt_argv(template, "3").strip()

        if not item_from or not item_to:
            continue

        new_params[te][item_from] = item_to

    return new_params


# ==========================
# FilesBaseWorker
# ==========================


class TempsParamsWorker(FilesBaseWorker):
    def __init__(self) -> None:
        file: str = "temps_params.json"
        self.title = "ويكيبيديا:AutoWikiBrowser/Rename_template_parameters"
        super().__init__(file, self.title, default_data)

    def load_data_from_text(self, text: str) -> dict:
        if not text:
            return {}

        new_params = get_new_params(text)

        data: dict[str, dict[str, str]] = {}

        for temp, params in new_params.items():
            if temp in data:
                data[temp].update(params)
            else:
                data[temp] = params

        return data

    def load_new_data(self) -> dict[str, Any]:

        logger.info(f"Loading: {self.title}")

        text = self.load_text()

        data = self.load_data_from_text(text)

        return data


_local_data = {}


def template_params_loader() -> dict[str, Any]:
    global _local_data

    worker = TempsParamsWorker()

    _local_data = worker.run()

    return _local_data


__all__ = [
    "TempsParamsWorker",
    "gt_argv",
    "get_new_params",
    "template_params_loader",
]
