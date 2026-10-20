""" """

from __future__ import annotations

import wikitextparser as wtp

from ...core1.remove_today.urls_data import ArchiveParamsUrlsData
from ..likeapi.ref_temp import ref_temps


def fix_dead_param(text: str):
    """
    Fixes dead parameters in the given text.

    Args:
        text (str): The text to fix dead parameters in.

    Returns:
        str: The fixed text.
    """
    newtext = text
    parsed = wtp.parse(text)

    switch = {"yes": "dead", "no": "live"}

    for template in parsed.templates:
        if not template:
            continue

        if not template.string or template.string.strip() == "":
            continue

        name = str(template.normal_name()).strip()

        if name.lower() not in ref_temps:
            continue

        dead = ""

        for dd in ArchiveParamsUrlsData.DEAD_URL_DATE_PARAMS:
            if template.has_arg(dd):
                template.del_arg(dd)

        for x in ArchiveParamsUrlsData.DEAD_URL_PARAMS:
            if not dead:
                ag = template.get_arg(x)
                if ag:
                    for cc in ag.comments:
                        del cc[:]
                    if ag.value and ag.value.strip():
                        ux = ag.value.strip().lower()
                        if ux in ["dead", "live", "yes", "no"]:
                            dead = ux

            if template.has_arg(x):
                template.del_arg(x)

        if not dead:
            continue

        status = ""

        for x in ArchiveParamsUrlsData.URL_STATUS_PARAMS:
            ag = template.get_arg(x)
            if ag:
                for cc in ag.comments:
                    del cc[:]
                if ag.value and ag.value.strip():
                    st = ag.value.strip().lower()
                    if st in ["dead", "live"]:
                        status = st
                        break

        if status:
            continue

        dead = switch.get(dead, dead)

        for x in ArchiveParamsUrlsData.URL_STATUS_PARAMS:
            if template.has_arg(x):
                template.del_arg(x)

        template.set_arg(ArchiveParamsUrlsData.PREFERRED_URL_STATUS_PARAM, dead)

    newtext = parsed.string

    return newtext


__all__ = [
    "fix_dead_param",
]
