""" """

from __future__ import annotations

import wikitextparser as wtp

from ..portal_lists.portals_lists import PORTALS_CATALOG
from ..wtp_utils import WtpUtils


def portal_bars(
    text: str,
    temp_title: str = "شريط بوابات",
    ns: int = 0,
) -> str:

    temp_title = temp_title or "شريط بوابات"

    old_text = text

    texts: list = []
    paramse: list = []

    to_add = {}

    parsed = wtp.parse(text)
    for template in WtpUtils.find_templates(parsed, [temp_title]):
        namestrip = str(template.normal_name()).strip()

        if namestrip != temp_title:
            continue

        texts.append(template.string)

        for param in template.arguments:
            va = str(param.value)  # mwpfh needs upcast to str
            key = str(param.name).strip()

            if not va.strip():
                continue

            if not key.isdigit():
                to_add[key] = va
                continue

            va = PORTALS_CATALOG.resolve_alias(va) or va
            vax = PORTALS_CATALOG.get_en_to_ar(case_insensitive=True).get(va.lower())
            if vax:
                va = vax

            if va not in paramse:
                paramse.append(va)

    paramse.sort()

    ux = "|".join(paramse)

    if to_add:
        to_add_line = "|".join([f"{param}={val}" for param, val in to_add.items()])
        ux = f"{to_add_line}|{ux}"

    newtemp = "{{شريط البوابات|" + ux + "}}"
    newtemp_2 = "{{" + f"{temp_title}|{ux}" + "}}"

    u = 0

    for te in texts:
        u += 1
        if u == 1:
            text = text.replace(te, newtemp, 1)
        else:
            text = text.replace(te, "")

    if text.find(newtemp) == -1:
        return old_text

    text = text.replace("{{شريط البوابات", "{{%s" % temp_title)

    if str(ns) == "14":
        if text.find(newtemp_2) != 0:
            text = newtemp_2 + "\n" + text.replace(newtemp_2, "")

    return text


__all__ = [
    "portal_bars",
]
