#!/usr/bin/python3
"""Arabic category sorting — refactored from sort_bot.py."""

from __future__ import annotations

import re

from ..constants import ARABIC_ALPHABET

_ARABIC_COLLATION = str.maketrans({ch: f"{i:02d}" for i, ch in enumerate(ARABIC_ALPHABET)})


def arabic_sort_key(text: str) -> str:
    """Custom collation key for Arabic Wikipedia category sorting.

    Maps Arabic characters to digit sequences that sort in the desired
    alphabetical order. Upgrade to pyicu if available.
    """
    return text.translate(_ARABIC_COLLATION)


def sort_text(categorylist: list[str]) -> list[str]:
    """Sort a list of raw category link strings."""
    cleaned = []
    for cat in categorylist:
        inner = cat.replace("[[تصنيف:", "").replace("]]", "")
        key = arabic_sort_key(inner)
        cleaned.append((key, inner))

    cleaned = list(set(cleaned))
    cleaned.sort(key=lambda x: x[0])

    return [f"[[تصنيف:{inner}]]" for _, inner in cleaned]


def sort_categories(text: str, title: str) -> str:
    """Sort categories in a given wikitext.

    Args:
        text: The text that contains the categories to be sorted.
        title: The title of the page that contains the categories.

    Returns:
        The text with the categories sorted.
    """
    new_text = text

    pattern = re.compile(r"(\[\[تصنيف\:(?:.+?)\]\])")
    cats = pattern.findall(text)

    if not cats:
        return text

    for cat in cats:
        new_text = new_text.replace(cat, "")

    cats = sort_text(cats)

    for name in cats[1:]:
        if re.search(r"\[\[(.+?)\|[ \*]\]\]", name) or "[[تصنيف:" + title == name.split("]]")[0].split("|")[0]:
            cats.remove(name)
            cats.insert(0, name)

    if cats == pattern.findall(text):
        return text

    for cat in cats:
        new_text = new_text + "\n" + cat
        new_text = new_text.replace("\r", "").replace("\n\n\n\n", "\n").replace("\n\n\n", "\n")

    return new_text
