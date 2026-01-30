#!/usr/bin/python3
"""

# from .cat_tools2 import Categorized_Page_Generator
# Categorized_Page_Generator(enpageTitle, Type)

"""
import logging

from ..config import settings
from ..new_api.page import CatDepth

logger = logging.getLogger(__name__)

tatone_ns = [0, 14, 10, 100]

if settings.category.stubs:
    tatone_ns = [14]


def Categorized_Page_Generator(enpageTitle, typee):
    # ---
    logger.info(f"Categorized_Page_Generator, enpageTitle:{enpageTitle}")
    # ---
    nss = "all"
    if typee == "cat":
        nss = "14"
    # ---
    NN_cat_member = []
    # ---
    cat_member = CatDepth(
        enpageTitle, sitecode=settings.EEn_site.code, family="wikipedia", depth=0, ns=nss, with_lang="ar"
    )
    # ---
    for title in cat_member:
        if int(cat_member[title]["ns"]) in tatone_ns:
            NN_cat_member.append(title.replace("_", " "))
    # ---
    return NN_cat_member
