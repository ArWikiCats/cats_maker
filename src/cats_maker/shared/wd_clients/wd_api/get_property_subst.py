#!/usr/bin/python3
""" """

from __future__ import annotations

import json
import logging

from ...newapi import AllAPIS

logger = logging.getLogger(__name__)


def _text_maker(properties: list[str], list_qids: list[str]) -> str:

    qids_rows: list = []

    for qid in list_qids:
        lino = f'"{qid}": '
        lino += "{"

        props: list = []
        for prop in properties:
            props.append(f'"{prop}": [{{{{subst:user:Mr. Ibrahem/line|{qid}|{prop}}}}}]')

        lino += ",".join(props)
        lino += " }"
        qids_rows.append(lino)

    text = "{ " + ", ".join(qids_rows) + " }"

    return text


def get_property_label_for_qids(
    properties: list[str],
    list_qids: list[str],
) -> dict[str, dict[str, str]]:

    text = _text_maker(properties, list_qids)

    api = AllAPIS.load_arwiki()
    jso = api.newapi().parse_text(text, "ويكيبيديا:ملعب")

    if not jso:
        logger.info('jso == ""')
        return {}

    elif jso == text:
        logger.info("<<lightred>> jso == text ")
        return {}

    try:
        newtabe = json.loads(jso)
    except Exception as err:
        logger.info(f"json.loads: {err}")
        return {}

    return newtabe  # type: ignore


__all__ = [
    "get_property_label_for_qids",
]
