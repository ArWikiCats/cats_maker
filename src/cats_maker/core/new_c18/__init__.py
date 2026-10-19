#!/usr/bin/python3
"""new_c18 — Refactored Arabic Wikipedia category generation module."""

from .core.category_generator import fetch_category_members, translate_titles_to_ar
from .core.category_resolver import CategoryResolver
from .core.category_validator import validate_categories_for_new_cat
from .core.cross_wiki_linker import get_english_page_title, get_page_link
from .core.member_lister import MemberLister
from .io.json_store import JsonStore, get_dont_add_pages
from .tools.doc_handler import add_text_to_template
from .tools.sort import sort_categories
from .tools.template_query import get_templates
from .utils.text import clean_category_input, extract_wikidata_qid, normalize_category_title

__all__ = [
    "add_text_to_template",
    "CategoryResolver",
    "clean_category_input",
    "extract_wikidata_qid",
    "fetch_category_members",
    "get_dont_add_pages",
    "get_english_page_title",
    "get_page_link",
    "get_templates",
    "JsonStore",
    "MemberLister",
    "normalize_category_title",
    "sort_categories",
    "translate_titles_to_ar",
    "validate_categories_for_new_cat",
]
