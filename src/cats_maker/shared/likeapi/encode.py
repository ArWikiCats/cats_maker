#!/usr/bin/python3
""" """

from __future__ import annotations

import logging
import re
import sys

from ..newapi import AllAPIS

logger = logging.getLogger(__name__)

ar_litters = {
    "أ": "%D8%A3",
    "آ": "%D8%A2",
    "إ": "%D8%A5",
    "ا": "%D8%A7",
    "ب": "%D8%A8",
    "ت": "%D8%AA",
    "ث": "%D8%AB",
    "ج": "%D8%AC",
    "ح": "%D8%AD",
    "خ": "%D8%AE",
    "د": "%D8%AF",
    "ذ": "%D8%B0",
    "ر": "%D8%B1",
    "ز": "%D8%B2",
    "س": "%D8%B3",
    "ش": "%D8%B4",
    "ص": "%D8%B5",
    "ض": "%D8%B6",
    "ط": "%D8%B7",
    "ظ": "%D8%B8",
    "ع": "%D8%B9",
    "غ": "%D8%BA",
    "ف": "%D9%81",
    "ق": "%D9%82",
    "ك": "%D9%83",
    "ل": "%D9%84",
    "م": "%D9%85",
    "ن": "%D9%86",
    "ه": "%D9%87",
    "و": "%D9%88",
    "ي": "%D9%8A",
    "ى": "%D9%89",
    "ء": "%D8%A1",
    "ئ": "%D8%A6",
    "ؤ": "%D8%A4",
    "ة": "%D8%A9",
    "ـ": "%D9%80",
    "،": "%D8%8C",
    r"\u0655": "%D9%95",
    r"\u0654": "%D9%94",
    # "":"",
}
#
# %D9%94

litters = ar_litters.copy()

lit2 = {
    # ':':"%3A",
    '"': "%22",
    "'": "%27",
    " ": "%20",
    # "_":"%20",
    "ü": "%C3%BC",
}

if "ar" not in sys.argv:
    litters.update(lit2)


def encode_arabic(label: str, just_ar_litters: bool = False):
    label2 = label

    lits = litters

    if just_ar_litters:
        lits = ar_litters

    for ar, xo in lits.items():
        label2 = label2.replace(ar, xo)

    return label2


def decode_arabic(label: str, just_ar_litters: bool = False):
    label2 = label

    lits = litters

    if just_ar_litters:
        lits = ar_litters

    for ar, xo in lits.items():
        if ar != " ":
            label2 = label2.replace(xo, ar)
            xz = re.escape(xo)
            label2 = re.sub(xz, ar, label2, flags=re.IGNORECASE)

    return label2


def process_page(title: str) -> str:
    """
    Process a single page, adding archive links and making improvements.

    """
    ar_api = AllAPIS.load_arwiki()
    page = ar_api.mainpage(title)

    text = page.get_text()
    ns = page.namespace()

    # Check for various conditions before processing
    if not page.exists():
        logger.info(f'page "{title}" not exists in ar:wikipedia')
        return text

    if page.is_redirect():
        return text

    if not page.can_edit(script="fixref"):
        logger.info('page "%s is not editable', title)
        return text

    vaild_ns = [0]  # [ 0, 10 ]

    if ns not in vaild_ns and "allns" not in sys.argv:  # Only process main namespace by default
        logger.info(f'namespace "{ns}" for page:{title} not in vaild_ns add allns to work on it.')
        return text

    logger.info(f'<<lightyellow>> process_page title:"{title}" ')

    newtext = decode_arabic(text, just_ar_litters=True)

    if newtext == text:
        return text

    page.edit(newtext=newtext, summary="")

    return newtext


__all__ = [
    "encode_arabic",
    "decode_arabic",
    "process_page",
]
