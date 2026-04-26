"""Utility functions for the service package."""

import logging

from .constants import NS_TEXT_AR, NS_TEXT_EN

logger = logging.getLogger(__name__)


def add_namespace_prefix(title: str, ns: str | int, lang: str = "ar") -> str:
    """Prepend the namespace label to *title*.

    Returns *title* unchanged when namespace is 0 or the label is unknown.
    """
    ns_key = str(ns)
    if not title or ns_key == "0":
        return title

    table = NS_TEXT_AR if lang == "ar" else NS_TEXT_EN
    prefix = table.get(ns_key)

    if not prefix:
        logger.debug("No namespace label found for ns=%s lang=%s", ns_key, lang)
        return title

    return f"{prefix}:{title}"
