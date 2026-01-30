#!/usr/bin/python3
""" """
import functools
import logging

from ..new_api.page import MainPage, SuperMainPage
from ..temp import main_make_temp_no_title
from ..utils.skip_cats import skip_encats
from . import categorytext

logger = logging.getLogger(__name__)


@functools.lru_cache
def _load_page(title) -> SuperMainPage:
    page = MainPage(title, "ar")
    return page


def page_put(title, new_text, msg):
    """
    used in tests
    """
    page = _load_page(title)

    text = page.get_text()
    # ---
    if not text:
        logger.info(' text = "" ')
        return False
    # ---
    if not page.exists():
        return False
    # ---
    page_edit = page.can_edit(script="cat")
    # ---
    if not page_edit:
        return False
    # ---
    save = page.save(newtext=new_text, summary=msg, nocreate=1)
    # ---
    return save


def create_Page(text: str, page: SuperMainPage) -> bool:
    """
    used in tests
    """
    new_cat = page.Create(text=text, summary="بوت:إنشاء تصنيف.")
    return new_cat


def add_text_to_cat(text, categories, enca, title, qid, family=""):
    if family != "wikipedia" and family:
        return text

    new_text = text

    if len(categories) > 0:
        # اضافة التصنيفات المعادلة

        caca = "\n".join([f"[[{str(cai)}]]" for cai in categories if cai is not None and cai is not False])

        numadd = str(len(categories))

        suu = "، ".join([f"[[{s}]]" for s in categories if s is not None and s is not False])
        suu = f"({suu})"

        if len(categories) > 6:
            suu = "تصنيف"

        msg = f"بوت: [[مستخدم:Mr.Ibrahembot/التصانیف المعادلة|التصانيف المعادلة]]:+ {numadd} {suu}"

        new_text += f"\n{caca}"

        save = page_put(title, new_text, msg)
        # ---
        if save:
            text = new_text

    p373 = categorytext.fetch_commons_category(enca, qid)

    if p373:
        # اضافة قالب كومنز
        susa = f"بوت: أضاف {p373}"

        new_text += f"\n{p373}"

        save = page_put(title, new_text, susa)

        if save:
            text = new_text

    portalse, portals_list = categorytext.generate_portal_content(title, enca, return_list=True)

    if portalse and portals_list != []:
        # اضافة قالب بوابة
        asds = ",".join([f"بوابة:{dd}" for dd in portals_list])

        sus2 = f"بوت:إضافة بوابة ({asds})"

        new_text = f"{portalse}\n{new_text}"

        save = page_put(title, new_text, sus2)

        if save:
            text = new_text

    temp = main_make_temp_no_title(title)

    if temp:
        new_text += f"\n{temp}"

        save = page_put(title, new_text, "بوت: إضافة قالب تصفح")

        if save:
            text = new_text

    return new_text


def make_category(categories, enca, title, qid, family=""):
    if enca in skip_encats:
        logger.debug(f"<<lightred>> enca: {enca} in skip_encats")
        return False

    if not title.startswith("تصنيف:"):
        logger.debug(f'<<lightreed>> title: {title} not start with "تصنيف:"')
        return False

    caia = ""

    for cai in categories:
        if cai is not None and cai is not False:
            caia = f"\n[[{str(cai)}]]"
            break

    text = "{{نسخ:#لوموجود:{{نسخ:اسم_الصفحة}}|{{مقالة تصنيف}}|}}\n"

    text = text + caia
    text += f"\n\n[[en:{enca}]]"

    page = MainPage(title, "ar")
    # ---
    if page.get_text() or page.exists():
        return False
    # ---
    new_cat = create_Page(text, page)

    if new_cat is not False:
        text = add_text_to_cat(text, categories, enca, title, qid, family="")

    logger.warning(f"<<lightgreen>> New_Cat: {new_cat}")

    return new_cat


def new_category(enca, title, categories, qid, family=""):
    logger.debug(f'<<lightgreen>>* make ar cat:"{title}", for english:"{enca}". ')

    if not title or title == "n":
        logger.debug('<<lightred>> not title or title != "n"')

    New_Cat = make_category(categories, enca, title, qid, family=family)

    susu = f"بوت: [[مستخدم:Mr.Ibrahembot/التصانیف المعادلة|التصانيف المعادلة]]:+ 1 ([[{title}]])"

    if New_Cat is False or New_Cat is not True:
        logger.debug("no1: New_Cat is False")
        logger.debug("return False")
        return False

    return True
