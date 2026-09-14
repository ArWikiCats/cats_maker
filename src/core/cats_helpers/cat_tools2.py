#!/usr/bin/python3
"""

# from .cat_tools2 import categorized_page_generator
# categorized_page_generator(enpage_title, Type)

"""

import logging

from ...config import main_settings
from ...shared.api_page import load_main_api

logger = logging.getLogger(__name__)

tatone_ns = [0, 14, 10, 100]


def categorized_page_generator(enpage_title, typee):
    logger.info(f", enpage_title:{enpage_title}")

    nss = "all"
    if typee == "cat":
        nss = "14"

    NN_cat_member = []

    api = load_main_api(main_settings.en_site.code)
    cat_member = api.catdepth(enpage_title, depth=0, ns=nss, with_lang="ar")

    for title in cat_member:
        if int(cat_member[title]["ns"]) in tatone_ns:
            NN_cat_member.append(title.replace("_", " "))

    return NN_cat_member
