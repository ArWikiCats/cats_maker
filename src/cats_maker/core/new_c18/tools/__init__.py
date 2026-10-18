#!/usr/bin/python3
"""Tool modules for new_c18."""

from .doc_handler import add_text_to_template
from .sort import arabic_sort_key, sort_categories, sort_text
from .template_query import get_templates

__all__ = [
    "add_text_to_template",
    "arabic_sort_key",
    "get_templates",
    "sort_categories",
    "sort_text",
]
