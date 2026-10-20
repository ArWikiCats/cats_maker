#!/usr/bin/python3
""" """

from __future__ import annotations

import logging
import sys
from collections.abc import Iterable, Iterator

import pywikibot
from pywikibot import config, pagegenerators

from .newapi import AllAPIS

logger = logging.getLogger(__name__)

LANG_CODE = "ar"
FAMILY_CODE = "wikipedia"


def fetch_user_new_pages(
    limit: int | str = "max",
    namespace: str = "0",
    user: str = "",
    lang: str = LANG_CODE,
    family: str = FAMILY_CODE,
) -> list[str]:
    api = AllAPIS.load(lang, family)
    new_api = api.newapi()
    generator = new_api.get_newpages(limit=limit, namespace=namespace, user=user)
    return generator


def getusernewpages(lang: str = LANG_CODE, family: str = FAMILY_CODE) -> list[str]:
    usernewpages = ""
    ns = ""
    limit = 100

    for arg in sys.argv:
        arg, _, value = arg.removeprefix("-").partition(":")

        if arg == "usernewpages":
            usernewpages = value
        if arg == "mynewpages":
            usernewpages = "Mr. Ibrahem"
            # ns = "0"
            if value:
                limit = int(value)
        if arg == "limit":
            limit = int(value)
        elif arg == "ns":
            ns = value

    if usernewpages and ns == "":
        ns = "0"

    if usernewpages:
        return fetch_user_new_pages(limit=limit, namespace=ns, user=usernewpages, lang=lang, family=family)

    return []


def do_title(generator) -> Iterator:
    # [page.title(as_link=False) for page in generator]
    for page in generator:
        yield page.title(as_link=False)


def fetch_new_pages(value, lang: str = LANG_CODE, family: str = FAMILY_CODE) -> list[str]:
    api = AllAPIS.load(lang, family)
    new_api = api.newapi()
    return new_api.get_newpages(limit=value, namespace="0", three_houers=True)


def get_gent_list(
    args: Iterable[str] | None = None,
    lang: str = LANG_CODE,
    family: str = FAMILY_CODE,
) -> list | Iterator:

    options = {}

    genFactory = pagegenerators.GeneratorFactory()

    if family == "wikidata" and lang == "www":
        lang = "wikidata"

    config.family = family
    config.mylang = lang

    for arge in pywikibot.handle_args(args):
        arg, _, value = arge.removeprefix("-").partition(":")

        if arg in ("summary", "text"):
            if not value:
                input(f"Please enter a value for {arg}")
            options[arg] = value
        else:
            options[arg] = True

            genFactory.handle_arg(arge)

    _generator = genFactory.getCombinedGenerator()

    if _generator:
        return do_title(_generator)

    generator: list[str] = []

    for arg in sys.argv:
        arg, _, value = arg.removeprefix("-").partition(":")
        if arg == "newpages2":
            generator: list[str] = fetch_new_pages(value, lang=lang, family=family)

    if not generator:
        logger.info("<<lightred>> No pages to work on")
        generator: list[str] = getusernewpages(lang=lang, family=family)

    return generator


__all__ = [
    "fetch_user_new_pages",
    "getusernewpages",
    "do_title",
    "fetch_new_pages",
    "get_gent_list",
]
