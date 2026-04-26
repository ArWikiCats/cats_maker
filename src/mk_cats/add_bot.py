#!/usr/bin/python3
""" """
import functools
import logging

from ..c18_new.bots.text_to_temp_bot import add_text_to_template
from ..c18_new.dontadd import Dont_add_to_pages_def
from ..c18_new.tools_bots.sort_bot import sort_categories
from ..helps import function_timer
from ..new_api import load_main_api

logger = logging.getLogger(__name__)


def add_text_to_articles(final_categories, newtext):
    if newtext.find("[[تصنيف:") != -1:
        num = newtext.find("[[تصنيف:")
        newtext = f"{(newtext[:num] + final_categories)}\n{newtext[num:]}"

        if newtext.find(final_categories.strip()) == -1:
            newtext = newtext + final_categories
    return newtext


@functools.lru_cache(maxsize=1024)
def _get_page(page_title):

    api = load_main_api("ar")
    page = api.MainPage(page_title)

    text = page.get_text()

    if not text:
        logger.info(' text = "" ')
        return False

    if page.isRedirect():
        return False

    if page.isDisambiguation():
        return False

    if not page.exists():
        return False

    page_edit = page.can_edit(script="cat")

    if not page_edit:
        return False

    return page


@function_timer
def add_to_page(page_title, arcat):

    Dont_add_to_pages = Dont_add_to_pages_def()

    logger.info(f" page_title:{page_title} , cat:{arcat}")

    if page_title in Dont_add_to_pages:
        logger.info(f"<<lightred>> page_title:{page_title} in [[تصنيف:صفحات لا تقبل التصنيف المعادل]]")
        return False

    arcat = arcat.replace("_", " ")
    final_categories = f"\n[[{arcat}]]"

    susu = f"بوت [[مستخدم:Mr.Ibrahembot/التصانیف المعادلة|التصانيف المعادلة]]: +([[{arcat}]])"

    page = _get_page(page_title)

    if not page:
        logger.info(f"<<lightred>> _get_page() failed for {page_title=}, {arcat=}")
        return False

    text = page.get_text()
    ns = page.namespace()

    categories = page.get_categories(with_hidden=False)

    if text.find(f"[[{arcat}]]") != -1 or text.find(f"[[{arcat}|") != -1:
        logger.info(" text.find( final_categories.strip() ) != -1 ")
        return False

    newtext = text

    if ns == 10:
        newtext = add_text_to_template(newtext, final_categories, page_title)
    else:
        newtext = add_text_to_articles(final_categories, newtext)

    if newtext == text:
        return False

    newtext = sort_categories(newtext, page_title)

    save = page.save(newtext=newtext, summary=susu)

    if not save:
        logger.error(f"<<lightred>> page.save() failed for {page_title=}, {arcat=}")
        return False

    return True


def add_to_final_list(final_list, title, callback=None):

    title = title.replace("_", " ")

    if not title.startswith("تصنيف:"):
        title = f"تصنيف:{title}"

    if not final_list:
        return

    for n, page in enumerate(final_list, start=1):
        logger.info(f"<<yellow>> cat:{title} page:{page} n:{n}/{len(final_list)}")
        save = add_to_page(page, title)
        if save and callback:
            try:
                callback(title)
            except Exception as e:
                logger.info(f"<<lightred>> Error in callback: {e}")
