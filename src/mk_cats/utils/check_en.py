#!/usr/bin/python3
""" """

import logging

from ...core.new_c18.constants import NO_Templates_lower, SKIP_ENCATS
from ...shared import find_page_data

logger = logging.getLogger(__name__)


def check_en_temps(en_title: str) -> bool:
    if en_title in SKIP_ENCATS:
        logger.debug(f"category: {en_title} in SKIP_ENCATS")
        return False

    category_data = find_page_data(en_title, prop="templates|categories", first_site_code="en")

    if not category_data:
        return True

    templates = category_data.get(en_title, {}).get("templates")

    if not templates:
        return True

    for target_temp in templates:
        target_temp2 = target_temp.lower().replace("template:", "")
        if target_temp2 in NO_Templates_lower:
            logger.warning(f'Category has:"{target_temp2}" in NO_Templates_lower ')
            return False

    return True
