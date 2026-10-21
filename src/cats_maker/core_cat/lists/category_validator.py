"""
Core module for category validation logic.

Encapsulates page status checks and category pair validation with explicit dependencies.
"""

import logging
from typing import Any

from ...config import Settings
from ...config.constants import AR_FALSE_TEMPLATES, EN_FALSE_TEMPLATES_LOWERS
from ...shared.newapi import AllAPIS
from ..c18.models import ValidationResult

logger = logging.getLogger(__name__)


class CategoryValidator:
    """Service for validating Arabic and foreign categories on Wikipedia."""

    def __init__(
        self,
        settings_provider: Any | None = None,
        api_loader: Any | None = None,
    ) -> None:
        self.settings_provider = settings_provider or Settings
        self.api_loader = api_loader or AllAPIS

    def check_page_status(
        self,
        site: str,
        title: str,
        expected_langlink: str | None,
        template_blacklist: list[str],
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
        sitr_api = self.api_loader.load(site, "wikipedia")
        info = sitr_api.newapi().get_page_info_from_wikipedia(title)

        if not info:
            logger.info(f"not found:({title})")
            return ValidationResult(valid=False, reason=f"Page not found: {title}")

        if not info.get("exists"):
            logger.info(f"({title}) not exists")
            return ValidationResult(valid=False, reason=f"Page does not exist: {title}")

        if info.get("is_redirect_page"):
            logger.info(f"({title}) is_redirect_page")
            return ValidationResult(valid=False, reason=f"Page is a redirect: {title}")

        if expected_langlink:
            langlink = info.get("langlinks", {}).get("ar" if is_ar else "en", "")
            if langlink and langlink != expected_langlink:
                logger.info(f"langlink mismatch ({langlink}) != ({expected_langlink})")
                return ValidationResult(
                    valid=False,
                    reason=f"Langlink mismatch: {langlink} != {expected_langlink}",
                )

        main_settings = self.settings_provider.get_instance()

        templates = info.get("templates", {})
        template_prefix = "قالب:" if is_ar else "Template:"
        for target_temp in templates:
            target_temp2 = target_temp.replace(template_prefix, "")
            if is_ar:
                if target_temp2 in template_blacklist and not main_settings.category.keep:
                    logger.info(f"{title} has template:{target_temp2}")
                    return ValidationResult(
                        valid=False,
                        reason=f"Blacklisted template: {target_temp2}",
                    )
            else:
                if target_temp2.lower() in EN_FALSE_TEMPLATES_LOWERS and not main_settings.category.keep:
                    logger.info(f"{title} has template:{target_temp2}")
                    return ValidationResult(
                        valid=False,
                        reason=f"Blacklisted template: {target_temp2}",
                    )

        return ValidationResult(valid=True)

    def validate_categories_for_new_cat(self, arcat: str, encat: str, wiki: str = "en") -> ValidationResult:
        """Validate a pair of Arabic and foreign categories."""
        arcat2 = f"تصنيف:{arcat}"
        encat2 = f"Category:{encat}"

        en_result = self.check_page_status(
            site=wiki,
            title=encat2,
            expected_langlink=arcat2,
            template_blacklist=AR_FALSE_TEMPLATES,
            is_ar=False,
        )
        if not en_result.valid:
            return en_result

        ar_result = self.check_page_status(
            site="ar",
            title=arcat2,
            expected_langlink=encat2,
            template_blacklist=AR_FALSE_TEMPLATES,
            is_ar=True,
        )
        if not ar_result.valid:
            return ar_result

        return ValidationResult(valid=True)


__all__ = [
    "CategoryValidator",
]
