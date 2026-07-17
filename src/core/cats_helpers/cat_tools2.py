#!/usr/bin/python3
"""

# from .cat_tools2 import Categorized_Page_Generator
# Categorized_Page_Generator(enpage_title, Type)

"""

import logging

from ...config import settings
from ...shared.api_page import load_main_api

logger = logging.getLogger(__name__)

tatone_ns = [0, 14, 10, 100]

if settings.category.stubs:
    tatone_ns = [14]


def Categorized_Page_Generator(enpage_title, typee):
    logger.info(f", enpage_title:{enpage_title}")

    nss = "all"
    if typee == "cat":
        nss = "14"

    NN_cat_member = []

    api = load_main_api(settings.EEn_site.code)
    cat_member = api.CatDepth(enpage_title, depth=0, ns=nss, with_lang="ar")

    for title in cat_member:
        if int(cat_member[title]["ns"]) in tatone_ns:
            NN_cat_member.append(title.replace("_", " "))

    return NN_cat_member
