#!/usr/bin/python3
"""Category validation logic (merged from sql_cat_checker.py)."""

from __future__ import annotations

import logging

from ....config import settings
from ...utils import global_False_entemps
from ...wiki_api import get_page_info_from_wikipedia
from ..constants import NO_TEMPLATES_AR, NO_TEMPLATES_AR_WITHOUT_STUBS
from ..models import ValidationResult

logger = logging.getLogger(__name__)


def _get_no_templates() -> frozenset[str]:
    """Return the appropriate template blacklist based on settings."""
    if settings.category.stubs:
        return NO_TEMPLATES_AR_WITHOUT_STUBS
    return NO_TEMPLATES_AR


def _get_false_templates() -> frozenset[str]:
    """Return lower-cased false templates from global helper."""
    return frozenset(x.lower() for x in global_False_entemps)


def _check_page_status(
    site: str,
    title: str,
    expected_langlink: str | None,
    template_blacklist: frozenset[str],
    is_ar: bool = False,
) -> ValidationResult:
    """Generic page status checker.

    Args:
        site: Wiki site code.
        title: Full page title with namespace prefix.
        expected_langlink: Expected langlink title to match, or None.
        template_blacklist: Set of template names that invalidate the page.
        is_ar: Whether this is an Arabic page (affects template prefix).
    """
    info = get_page_info_from_wikipedia(site, title)

    if not info:
        logger.info(f"<<lightred>> not found:({title})")
        return ValidationResult(valid=False, reason=f"Page not found: {title}")

    if not info.get("exists"):
        logger.info(f"<<lightred>> ({title}) not exists")
        return ValidationResult(valid=False, reason=f"Page does not exist: {title}")

    if info.get("isRedirectPage"):
        logger.info(f"<<lightred>> ({title}) isRedirectPage")
        return ValidationResult(valid=False, reason=f"Page is a redirect: {title}")

    if expected_langlink:
        langlink = info.get("langlinks", {}).get("ar" if is_ar else "en", "")
        if langlink and langlink != expected_langlink:
            logger.info(f"<<lightred>> langlink mismatch ({langlink}) != ({expected_langlink})")
            return ValidationResult(
                valid=False,
                reason=f"Langlink mismatch: {langlink} != {expected_langlink}",
            )

    templates = info.get("templates", {})
    template_prefix = "قالب:" if is_ar else "Template:"
    for target_temp in templates:
        target_temp2 = target_temp.replace(template_prefix, "")
        if is_ar:
            if target_temp2 in template_blacklist and not settings.category.keep:
                logger.info(f"<<lightred>> {title} has temp:{target_temp2}")
                return ValidationResult(
                    valid=False,
                    reason=f"Blacklisted template: {target_temp2}",
                )
        else:
            if target_temp2.lower() in _get_false_templates() and not settings.category.keep:
                logger.info(f"<<lightred>> {title} has temp:{target_temp2}")
                return ValidationResult(
                    valid=False,
                    reason=f"Blacklisted template: {target_temp2}",
                )

    return ValidationResult(valid=True)


def validate_categories_for_new_cat(arcat: str, encat: str, wiki: str = "en") -> ValidationResult:
    """Validate a pair of Arabic / English (or French) categories.

    Returns a ValidationResult instead of a bare bool.
    """
    arcat2 = f"تصنيف:{arcat}"
    encat2 = f"Category:{encat}"

    en_result = _check_page_status(
        site=wiki,
        title=encat2,
        expected_langlink=arcat2,
        template_blacklist=_get_no_templates(),
        is_ar=False,
    )
    if not en_result.valid:
        return en_result

    ar_result = _check_page_status(
        site="ar",
        title=arcat2,
        expected_langlink=encat2,
        template_blacklist=_get_no_templates(),
        is_ar=True,
    )
    if not ar_result.valid:
        return ar_result

    return ValidationResult(valid=True)
