#!/usr/bin/python3
"""new_c18 — Refactored Arabic Wikipedia category generation module."""

from .domain.sorting import CategorySorter
from .infrastructure.network.category_generator import fetch_category_members
from .infrastructure.network.category_resolver import CategoryResolver
from .infrastructure.network.category_validator import validate_categories_for_new_cat
from .infrastructure.network.member_lister import MemberLister
from .io.json_store import DontAddStore, JsonStore
from .tools.doc_handler import add_text_to_template
from .utils.text import clean_category_input, extract_wikidata_qid, normalize_category_title

__all__ = [
    "add_text_to_template",
    "CategoryResolver",
    "clean_category_input",
    "extract_wikidata_qid",
    "fetch_category_members",
    "DontAddStore",
    "JsonStore",
    "MemberLister",
    "normalize_category_title",
    "CategorySorter",
    "validate_categories_for_new_cat",
]
