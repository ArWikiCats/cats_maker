#!/usr/bin/python3
"""Core logic for c18."""

from ....lists.category_generator import fetch_category_members
from ....lists.category_resolver import CategoryResolver
from ....lists.category_validator import validate_categories_for_new_cat
from .cross_wiki_linker import get_english_page_title, get_page_link

__all__ = [
    "CategoryResolver",
    "fetch_category_members",
    "get_english_page_title",
    "get_page_link",
    "validate_categories_for_new_cat",
]
