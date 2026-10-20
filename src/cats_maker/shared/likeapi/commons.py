#!/usr/bin/python3
"""

اضافة قالب كومنز بناءاً على قائمة في ملف


"""

from __future__ import annotations

import logging
import re
import sys

from ..newapi import AllAPIS
from ..wd_clients import WikidataClient

logger = logging.getLogger(__name__)

TARGET_TEMPLATES = [
    "تصنيف كومنز",
    "تصنيف كومنز مضمن",
    "تك",
    "كومنز",
    "Commonsccat",
    "CommonscCat",
    "Commons cat",
    "Commons category",
    "تصانيف كومنز متعددة",
    "Sisterlinks",
    "SisterLinks",
    "روابط شقيقة",
    "وصلات شقيقة",
    "كومنز مضمن",
    "Commons-inline",
    "Sister project links",
]


def addtemplate111(text: str) -> tuple[str, str]:
    template = "{{تصنيف كومنز}}"
    text = text + template
    return text, template


def addtemplate(text: str, title: str, ns: None | int | str = None) -> tuple[str, str]:
    """Add a template to the given text based on the title and namespace.

    This function retrieves a P373 API response based on the provided title
    and appends a specific template to the input text. The template added
    depends on whether the title indicates a category or is in a specific
    namespace. If the title starts with "تصنيف:" or if the namespace is
    equal to 14, a Commons category template is added. Otherwise, a sibling
    links template is appended. The function also checks for existing portal
    links in the text to determine where to insert the new template.

    Args:
        text (str): The original text to which the template will be added.
        title (str): The title used to fetch the P373 API response.
        ns (bool?): A flag indicating the namespace. Defaults to False.

    Returns:
        tuple: A tuple containing the modified text and the template that was added.
    """

    wd_api = WikidataClient.load()

    P373 = wd_api.get_p373_api(qid="", title=title, sites="arwiki")

    template = ""

    if P373:
        logger.info(f"find P373 = {P373}")
        if title.startswith("تصنيف:") or str(ns) == "14":
            template = "{{تصنيف كومنز|" + P373 + "}}"
        else:
            # template = "\n{{روابط شقيقة|commons=" + P373 + "}}"
            template = "\n{{روابط شقيقة}}"

        if title.startswith("تصنيف:") or str(ns) == "14":
            text = template.strip() + "\n" + text
        else:
            pat = r"\{\{شريط بوابات"
            find = re.compile(pat)
            portal = find.findall(text)
            if portal:
                # portal
                # text = re.sub(r'{{شريط بوابات' , template + '\n' + '{{شريط بوابات' , text)
                text = text.replace("{{شريط بوابات", template + "\n" + "{{شريط بوابات")
            else:
                text = text + template

    return text, template


def findtemplate(title: str, text: str, ns: None | int | str = None) -> tuple[str, str]:
    """Find and replace a template in the given text.

    This function searches for a specific template in the provided text and
    replaces it with a new template based on the given title. It uses
    regular expressions to identify the template and performs the
    replacement if a match is found. If no match is found, it returns the
    original text unchanged along with an empty string.

    Args:
        title (str): The title to be used for the new template.
        text (str): The text in which to search for the template.
        ns (bool?): A flag indicating whether to use namespace.
            Defaults to False.

    Returns:
        tuple: A tuple containing the modified text and the template used.
    """

    linetest = r"\{\{\s*(" + "|".join(TARGET_TEMPLATES) + ")"
    test = re.sub(linetest, "", text, flags=re.IGNORECASE | re.DOTALL)

    if test != text:
        logger.info("test != text")
        return text, ""

    newtext, temp = addtemplate(text, title, ns=ns)
    return newtext, temp


def make_text_changes(
    text: str,
    title: str,
    ns: None | int | str = None,
) -> tuple[str, str]:

    newtext = text

    vaild_ns = [0, 14]

    if ns not in vaild_ns and "allns" not in sys.argv:
        # logger.info( 'ns "%s" for page:%s not in vaild_ns' % (ns , title) )
        return text, ""

    # header, body, footer = textlib.extract_sections( text )
    # for hh in body : #_Section(title='=== فبراير ===', content='\n\n')
    # logger.info( hh.title )

    if text.startswith("#تحويل"):
        logger.info("<<lightyellow>> text startswith تحويل")
        return text, ""

    if text.find("{{تحويل تصنيف") != -1:
        logger.info("<<lightyellow>> text has {{تحويل تصنيف")
        return text, ""

    newtext, temp = findtemplate(title, text, ns=ns)

    summary = "بوت: أضاف " + temp

    return newtext, summary


def treat_page(title: str, numb, page_text: str = "") -> None:
    """Treat a Wikipedia page by making text changes.

    This function checks if a specified Wikipedia page exists and if it is
    editable. If the page exists and can be edited, it retrieves the current
    text of the page, applies specified changes to the text, and saves the
    updated text back to the page. Additionally, it outputs information
    about the page being treated, including the title and a numeric
    identifier.

    Args:
        title (str): The title of the Wikipedia page to be treated.
        numb (int): A numeric identifier related to the page treatment.
        page_text (str?): Additional text for processing. Defaults to an empty string.

    Returns:
        str: The updated text of the Wikipedia page after changes have been made.
    """

    ar_api = AllAPIS.load_arwiki()
    page = ar_api.mainpage(title)

    if not page.exists():
        return

    namespace = page.namespace()

    text = page.get_text()

    page_edit = page.can_edit()
    if not page_edit:
        return

    logger.info(f"<<lightyellow>> commons title:{title}, numb:{numb}")

    newtext, summary = make_text_changes(text, title, ns=namespace)

    if isinstance(newtext, str):  # pyright: ignore[reportUnnecessaryIsInstance]
        if newtext != text:
            page.edit(newtext=newtext, summary=summary, nocreate=1)


__all__ = [
    "addtemplate111",
    "addtemplate",
    "findtemplate",
    "make_text_changes",
    "treat_page",
]
