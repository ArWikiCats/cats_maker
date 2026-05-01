#!/usr/bin/python3
"""Documentation handler — refactored from text_to_temp_bot.py."""

from __future__ import annotations

import logging
import re

import wikitextparser as wtp

from ...client_wiki import load_main_api
from ..constants import PRE_TEXT, TO_SEARCH, TOSEARCH_AND_REPLACE

logger = logging.getLogger(__name__)


def add_to_text_temps(text: str, final_categories: str) -> str:
    for marker in TOSEARCH_AND_REPLACE:
        if marker in text:
            return text.replace(marker, marker + "\n" + final_categories)
    return text


def add_to_doc_page(text: str, final_categories: str) -> str:
    if text == "":
        return PRE_TEXT + "\n" + final_categories + "\n}}</includeonly>"

    text2 = add_to_text_temps(text, final_categories)
    if text2 != text:
        return text2

    final_categories = final_categories.strip()
    cats2 = []

    for line in final_categories.split("\n"):
        if not line.strip():
            continue
        x2 = line.strip().split("|")[0].strip()
        x3 = x2.strip().split("]]")[0].strip()
        if text.find(x2 + "|") == -1 and text.find(x3 + "]]") == -1:
            cats2.append(line)

    if not cats2:
        return text

    final_categories = "\n".join(cats2)

    pattern = r"<includeonly>[\s\n]+\[\[تصنيف\:"
    find_all = re.search(pattern, text, re.M | re.I)

    if find_all:
        text_string = find_all.group()
        return text.replace(text_string, f"<includeonly>\n{final_categories}\n[[تصنيف:", 1)

    parsed = wtp.parse(text)
    target_temps = {"ملعب آخر", "sandbox other", "ملعب أخر"}

    for template in parsed.templates:
        if not template:
            continue
        template_name = str(template.normal_name()).strip().lower()
        if template_name in target_temps:
            args_2 = template.get_arg("2")
            if args_2 and args_2.value:
                args_2.value += "\n" + final_categories
            else:
                template.set_arg("2", final_categories + "\n")
            return parsed.string

    if "</includeonly>" in text:
        return text.replace("</includeonly>", "\n" + final_categories + "\n</includeonly>", 1)

    temp_new = "<includeonly>{{ملعب آخر||\n" + final_categories + "}}</includeonly>"
    return text + "\n" + temp_new


def _insert_before_tag(text: str, content: str, idx: int) -> str:
    return text[:idx] + content + "\n" + text[idx:]


INSERTION_MARKERS = [
    ("{{توثيق", _insert_before_tag),
    ("{{توثيق شريط}}", _insert_before_tag),
    ("{{توثيق}}", _insert_before_tag),
    ("{{خيارات طي قالب تصفح}}", _insert_before_tag),
    ("{{خيار طوي قالب}}", _insert_before_tag),
    ("{{collapsible option}}", _insert_before_tag),
]


def add_direct(text: str, content: str) -> str:
    for marker, handler in INSERTION_MARKERS:
        idx = text.find(marker)
        if idx != -1:
            return handler(text, content, idx)

    text += "\n<noinclude>" + content + "</noinclude>"
    text = re.sub(r"\<\/noinclude\>\n\<noinclude\>", "</noinclude><noinclude>", text)
    text = re.sub(
        r"\<noinclude\>\s*(.*?)\s*\<\/noinclude\>\s*\<noinclude\>\s*(.*?)\s*\<\/noinclude\>",
        r"<noinclude>\n\g<1>\n\g<2>\n</noinclude>",
        text,
        flags=re.DOTALL,
    )

    if content.strip() not in text:
        text += f"\n<noinclude>{content}</noinclude>"

    return text


def find_doc_and_add(final_categories: str, title: str, create: bool = False) -> bool:
    if any(x in title for x in ["/ملعب", "/مختبر"]):
        logger.info(f"Skipping {title=}")
        return False

    doc_title = f"{title}/شرح"

    api = load_main_api("ar")
    page = api.MainPage(doc_title)
    text = page.get_text()

    if not text and not create:
        logger.info(f' text = "" {doc_title=}')
        return False

    if page.isRedirect():
        return False

    if page.isDisambiguation():
        return False

    if not page.exists() and not create:
        logger.info(f" not exists {doc_title=}")
        return False

    if not page.can_edit(script="cat"):
        return False

    new_text = add_to_doc_page(text, final_categories)

    fi = "، ".join(final_categories.split("\n")).strip()
    fi = fi.replace("[[تصنيف:", "[[:تصنيف:")
    summary = f"بوت [[مستخدم:Mr.Ibrahembot/التصانیف المعادلة|التصانيف المعادلة]]: +({fi})"

    if new_text != text:
        save = page.save(new_text, summary=summary, nocreate=not create)
        if save:
            return True

    return False


def add_text_to_template(text: str, final_categories: str, title: str) -> str:
    """Adds the final categories to the provided text at the appropriate location.

    Args:
        text: The text to add the final categories to.
        final_categories: The final categories to add to the text.
        title: Page title (used to detect /شرح subpages).

    Returns:
        The text with the final categories added.
    """
    logger.info("page.namespace() == 10 ")

    if title.endswith("/شرح"):
        return add_to_doc_page(text, final_categories)

    if any(x in text for x in TOSEARCH_AND_REPLACE):
        return add_to_text_temps(text, final_categories)

    if any(x in text for x in TO_SEARCH):
        return add_direct(text, final_categories)

    added = find_doc_and_add(final_categories, title, create=True)
    if added:
        return text

    return add_direct(text, final_categories)
