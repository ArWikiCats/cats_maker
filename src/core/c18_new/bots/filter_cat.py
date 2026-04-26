"""
Usage:
from ..bots.filter_cat import filter_cats_text
"""

import logging
import re

from ....config import settings
from ...wiki_api import get_deleted_pages
from ..tools_bots.temp_bot import templatequery, templatequerymulti

logger = logging.getLogger(__name__)


Skippe_Cat = [
    "تصنيف:مقالات ويكيبيدية تضمن نصوصا من الطبعة العشرين لكتاب تشريح جرايز (1918)",
    "تصنيف:Webarchive template wayback links",
    "تصنيف:Templates generating hCalendars",
    "تصنيف:Templates generating hCards and Geo",
    "تصنيف:قوالب معلومات مباني",
    "تصنيف:قوالب بحقول إحداثيات",
    "تصنيف:قوالب لغة-س",
    "تصنيف:قوالب معلومات",
    "تصنيف:قوالب تستند على وحدات لوا",
    "تصنيف:قوالب تستخدم بيانات من ويكي بيانات",
    "تصنيف:قوالب تستخدم قالب بيانات القالب",
    "تصنيف:صفحات توضيح",
    "",
    "",
    "",
    "",
]


page_false_templates = ["شطب", "مقالات متعلقة", "بذرة", "ويكي بيانات", "تستند على"]

if settings.category.stubs:
    page_false_templates.remove("بذرة")


def filter_cats_text(final_cats, ns, text_new):
    len_first = len(final_cats)

    logger.debug("<<lightred>> last<<lightyellow>>final_cats")
    logger.debug(final_cats)

    textremove = re.sub(r"\s*\|\s*", "|", text_new)

    for item in final_cats[:]:
        if ns not in [10, 14]:
            if item.startswith("تصنيف:قوالب") or item.startswith("تصنيف:صناديق تصفح"):
                logger.info(f"remove templates cat {item}. ")
                if item in final_cats:
                    final_cats.remove(item)
                continue

        if not item.startswith("تصنيف:"):
            logger.debug(f"item {item} not startswith تصنيف:")
            if item in final_cats:
                final_cats.remove(item)
            continue

        if item in Skippe_Cat:
            logger.info(f"<<lightred>>Category {item} in Skippe_Cat")
            if item in final_cats:
                final_cats.remove(item)
            continue
        # ---s
        if item in get_deleted_pages():
            logger.info(f"<<lightred>>Category {item} had in get_deleted_pages()")
            if item in final_cats:
                final_cats.remove(item)
            continue

        if textremove.find("{{لا للتصنيف الميلادي}}") != -1:
            if item.find("(الميلادي)") != -1 or item.find("(قبل الميلاد)") != -1:
                if item in final_cats:
                    final_cats.remove(item)
                continue

        if textremove.find("تصنيف:متوفون") != -1:
            # if item.find("أشخاص على قيد الحياة") != -1 or item.find("أشخاص_على_قيد_الحياة") != -1:
            if item.find("أشخاص أحياء") != -1 or item.find("أشخاص_أحياء") != -1:
                if item in final_cats:
                    final_cats.remove(item)
                continue

        for rr in page_false_templates:
            if item.find(rr) != -1:
                if item in final_cats:
                    final_cats.remove(item)
                logger.info(f"Remove cat:{item} it has {rr}")
                continue

        if textremove.find(item + "]]") != -1 or textremove.find(item + "|") != -1:
            if item in final_cats:
                final_cats.remove(item)
            continue

    listu = "|".join(final_cats)
    safo = templatequerymulti(listu, "ar")

    for item in final_cats[:]:
        cat_template = False
        if safo and item in safo:
            logger.info(f'<<lightgreen>> find "{item}" item in safo :')
            logger.debug(safo[item])
            cat_template = safo[item].get("templates", "")
        else:
            logger.info(f'<<lightred>> Cant find "{item}" item at safo ')
            cat_template = templatequery(item, "ar")

        if cat_template:
            if ("قالب:تحويل تصنيف" in cat_template) or ("قالب:delete" in cat_template) or ("قالب:حذف" in cat_template):
                logger.info(
                    f"<<lightred>>Category {item} had {{{{تحويل تصنيف}}}} or {{{{delete}}}} so it is skipped! please edit en.wiki interwiki"
                )
                if item in final_cats:
                    final_cats.remove(item)
                continue

            if not settings.category.stubs and "قالب:تصنيف مخفي" in cat_template:
                logger.info(f"<<lightred>>Category {item} had {{{{تصنيف مخفي}}}} so it is skipped! ")
                if item in final_cats:
                    final_cats.remove(item)
                continue

            if "قالب:تصنيف تتبع" in cat_template:
                logger.info(f"<<lightred>>Category {item} had {{{{تصنيف تتبع}}}} so it is skipped! ")
                if item in final_cats:
                    final_cats.remove(item)
                continue

    fff = len_first - len(final_cats)

    logger.info(f"len removed items: {fff} ")

    return final_cats
