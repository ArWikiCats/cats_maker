#!/usr/bin/python3
"""Shared text helpers for the module."""

import logging
import re

logger = logging.getLogger(__name__)


def clean_category_input(category: str, *, lang: str = "ar") -> str:
    """Strip wikitext noise and category prefix from a category string.

    Args:
        category: Raw category string.
        lang: Language code — "ar", "en", or "fr".

    Returns:
        Normalised category title without prefix or brackets.
    """
    cleaned = category.replace("[[", "").replace("]]", "").strip()
    cleaned = cleaned.replace("_", " ")

    prefixes = {
        "ar": "تصنيف:",
        "en": "Category:",
        "fr": "Catégorie:",
    }
    prefix = prefixes.get(lang, "")
    if prefix and cleaned.lower().startswith(prefix.lower()):
        cleaned = cleaned[len(prefix) :].strip()

    return cleaned


def normalize_category_title(title: str, *, lang: str = "ar") -> str:
    """Fully normalise a category title for comparisons.

    Removes duplicate prefixes, brackets, underscores, and normalises spaces.
    """
    title = title.replace("[[", "").replace("]]", "").strip()
    title = title.replace("_", " ")

    if lang == "ar":
        while title.startswith("تصنيف:تصنيف:"):
            title = title[len("تصنيف:") :]
        title = title.removeprefix("تصنيف:")
    elif lang == "en":
        while title.lower().startswith("category:category:"):
            title = title[len("Category:") :]
        if title.lower().startswith("category:"):
            title = title[len("Category:") :]
    elif lang == "fr":
        if title.lower().startswith("catégorie:"):
            title = title[len("Catégorie:") :]

    return title.strip()


def extract_wikidata_qid(text: str) -> str | None:
    """Extract a Wikidata QID from wikitext.

    Returns:
        The QID string if found, otherwise None.
    """
    patterns = [
        re.compile(r"\{\{قيمة ويكي بيانات\/قالب تحقق\s*\|\s*(Q\d+)\s*\}\}"),
        re.compile(r"\{\{قيمة ويكي بيانات\/قالب تحقق\s*\|\s*id\s*\=\s*(Q\d+)\s*\}\}"),
        re.compile(r"\{\{سباق الدراجات\/صندوق معلومات\s*\|\s*(Q\d+)\s*\}\}"),
        re.compile(r"\{\{Cycling race\/infobox\s*\|\s*(Q\d+)\s*\}\}"),
    ]

    for pat in patterns:
        match = pat.search(text)
        if match:
            return match.group(1)

    return None
