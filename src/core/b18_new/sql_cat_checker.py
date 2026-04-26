#!/usr/bin/python3
""" """

import logging

from ...config import settings
from ..utils import global_False_entemps
from ..wiki_api import get_page_info_from_wikipedia

logger = logging.getLogger(__name__)

NO_Templates_ar = [
    "تصنيف ويكيبيديا",
    "تحويل تصنيف",
    "تصنيف تتبع",
    "تصنيف تهذيب شهري",
    "تصنيف مخفي",
    "تصنيف بذرة",
    "تصنيف حاوية",
]

NO_Templates_lower = [x.lower() for x in global_False_entemps]

if settings.category.stubs:
    NO_Templates_ar.remove("تصنيف بذرة")
    NO_Templates_ar.remove("تصنيف مخفي")


def check_category_status(wiki, arcat, encat):
    arcat2 = f"تصنيف:{arcat}"
    encat2 = f"Category:{encat}"

    ioio_en = get_page_info_from_wikipedia(wiki, encat2)

    if ioio_en:
        if not ioio_en:
            logger.info(f"<<lightred>> not ioio_en:({encat2})")
            return False

        elif ioio_en:
            if not ioio_en["exists"]:
                logger.info(f"<<lightred>> ioio_en:({encat2}) not exists")
                return False
            elif ioio_en["isRedirectPage"]:
                logger.info(f"<<lightred>> ioio_en:({encat2}) isRedirectPage")
                return False

        ar_link = ioio_en.get("langlinks", {}).get("ar", "")
        if ar_link and ar_link != arcat2:
            logger.info(f"<<lightred>> find ar in encat. ({ar_link}) != ({arcat2}) ")
            return False

        en_temp = ioio_en.get("templates", {})
        for TargetTemp in en_temp:
            Target_Temp2 = TargetTemp.replace("Template:", "")
            if Target_Temp2.lower() in NO_Templates_lower and not settings.category.keep:
                logger.info(f"<<lightred>> encat:{encat2} has temp:{Target_Temp2} ")
                return False

    return True


def check_arabic_category_status(arcat, encat):
    arcat2 = f"تصنيف:{arcat}"
    encat2 = f"Category:{encat}"

    # فحص التصنيف العربي
    ioio_ar = get_page_info_from_wikipedia("ar", arcat2)

    if not ioio_ar:
        logger.info(f"<<lightred>> not ioio_ar:({arcat2})")
        return False

    elif ioio_ar:
        if not ioio_ar["exists"]:
            logger.info(f"<<lightred>> ioio_ar:({arcat2}) not exists")
        elif ioio_ar["isRedirectPage"]:
            logger.info(f"<<lightred>> ioio_ar:({arcat2}) isRedirectPage")
            return False

    if ioio_ar:
        en_link = ioio_ar.get("langlinks", {}).get("en", "")
        if en_link and en_link != encat2:
            logger.info(f"<<lightred>> find en in ioio_ar. ({en_link}) != ({encat2}) ")
            return False

        ar_temp = ioio_ar.get("templates", {})
        for TargetTemp in ar_temp:
            TargetTemp2 = TargetTemp.replace("قالب:", "")
            if TargetTemp2 in NO_Templates_ar and not settings.category.keep:
                logger.info(f"<<lightred>> arcat2:{arcat2} has temp:{TargetTemp2} ")
                return False
    return True


def validate_categories_for_new_cat(arcat, encat, wiki="en"):
    encat = encat.replace("Category:Category:", "Category:")
    encat = encat.replace("category:", "").replace("Category:", "").replace("Catégorie:", "")
    encat = encat.replace("_", " ")

    arcat = arcat.replace("تصنيف:تصنيف:", "").replace("تصنيف:", "").replace("_", " ")

    en_is_okay = check_category_status(wiki, arcat, encat)

    if not en_is_okay:
        return False

    ar_is_okay = check_arabic_category_status(arcat, encat)

    if not ar_is_okay:
        return False

    return True
