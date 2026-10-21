#!/usr/bin/python3
""" """

import logging

from ...config.constants import EN_FALSE_TEMPLATES_LOWERS, SKIP_ENCATS
from ...core_cat.c18.infrastructure.network.langlinks import LangLinksClient

logger = logging.getLogger(__name__)


def check_en_temps(en_title: str) -> bool:
    if en_title in SKIP_ENCATS:
        logger.debug(f"category: {en_title} in SKIP_ENCATS")
        return False

    category_data = LangLinksClient().find_page_data(en_title, prop="templates|categories", site_code="en")

    if not category_data:
        return True

    templates = category_data.get(en_title, {}).get("templates")

    if not templates:
        return True

    for target_temp in templates:
        target_temp2 = target_temp.lower().replace("template:", "")
        if target_temp2 in EN_FALSE_TEMPLATES_LOWERS:
            logger.warning(f'Category has:"{target_temp2}" in EN_FALSE_TEMPLATES_LOWERS ')
            return False

    return True


__all__ = [
    "check_en_temps",
]
