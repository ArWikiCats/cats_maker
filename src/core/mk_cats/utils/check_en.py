#!/usr/bin/python3
""" """

import logging

from ...utils import NO_Templates_lower, skip_encats
from ...wiki_api import find_LCN

logger = logging.getLogger(__name__)


def check_en_temps(en_title) -> bool:
    if en_title in skip_encats:
        logger.debug(f"<<lightred>> category: {en_title} in skip_encats")
        return False

    category_data = find_LCN(en_title, prop="templates|categories", first_site_code="en")

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
