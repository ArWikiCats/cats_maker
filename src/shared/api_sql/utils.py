"""Utility functions for the service package."""

import logging

from .constants import NS_TEXT_AR, NS_TEXT_EN

logger = logging.getLogger(__name__)


def add_namespace_prefix(title: str, ns: int | str, lang: str = "ar") -> str:
    """Helper to prepend namespace labels."""
    ns_key = str(ns)
    if not title or ns_key == "0":
        return title

    table = NS_TEXT_AR if lang == "ar" else NS_TEXT_EN
    prefix = table.get(ns_key)

    if not prefix:
        logger.debug("No namespace label found for ns=%s lang=%s", ns_key, lang)
        return title

    return f"{prefix}:{title}"
