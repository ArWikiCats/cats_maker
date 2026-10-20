#!/usr/bin/python3
""" """

from __future__ import annotations

import logging
import re
import sys
from typing import Any

import pywikibot
import wikitextparser as wtp

from ...core1.remove_today.urls_data import ArchiveParamsUrlsData
from ..likeapi import encode as encode2
from ..likeapi import ren
from ..likeapi.ref_temp import ref_temps
from ..wtp_utils import WtpUtils
from . import cosmetic_new
from .dead import fix_dead_param
from .portal_bar import portal_bars

logger = logging.getLogger(__name__)

arsite_1: dict[str, Any] = {}


def py_page(title: str, site: str) -> pywikibot.Page:

    if not arsite_1.get(site):
        arsite_1[site] = pywikibot.Site(site, "wikipedia")

    return pywikibot.Page(arsite_1[site], title)


def _fix_cite_urls(text: str) -> str:
    """
    fix cite urls
    """

    if "fixurl" not in sys.argv:
        return text

    parsed = wtp.parse(text)
    for temp in parsed.templates:
        namestrip = str(temp.normal_name()).strip()

        if namestrip.lower() not in ref_temps:
            continue

        url_params = WtpUtils.get_args(temp, ArchiveParamsUrlsData.URL_PARAMS, check_values=True)

        if not url_params:
            continue

        url_param = url_params[0]

        url = url_param.value.strip()
        new_url = encode2.decode_arabic(url, just_ar_litters=True)

        if new_url != url:
            url_param.value = new_url

    return parsed.string


def fix_portal_bar(
    text: str,
    temp_title: str = "شريط بوابات",
    ns: int = 0,
) -> str:
    text = portal_bars(text, temp_title=temp_title, ns=ns)
    return text


def co_change(text: str, title: str, page_ns: int) -> str:

    cc_toolkit = {}

    try:
        page = py_page(title, "ar")
    except Exception as e:
        logger.error("Error loading page: %s", str(e))
        return text

    cc_toolkit = cosmetic_new.CosmeticChangesToolkit(page, title=title, page_ns=page_ns)

    new_text = text

    if cc_toolkit:
        try:
            new_text = cc_toolkit.change(new_text)
        except Exception:
            logger.exception("Exception:", exc_info=True)

    if isinstance(new_text, str):
        return new_text

    return text


def format_text(text: str) -> str:
    text = text.replace("]] ،<ref>", "]]، <ref>")
    # text = text.replace("و<nowiki/>[[", "و[[")
    text = text.replace("]], [[", "]]، [[")
    text = text.replace("]] و [[", "]] و[[")
    text = text.replace(" فى ", " في ")
    text = text.replace(" التى ليست ", " التي ليست ")

    if text.find("&nbsp;بالمركز الأول&nbsp;") != -1 or text.find("{{Cycling race/infobox|") != -1:
        text = re.sub(r"(\w+)\s*&nbsp;\s*\[\[", r"\g<1> [[", text)
        text = re.sub(r"(\w+)\s*&nbsp;\s*\{\{", r"\g<1> {{", text)
        # ]] &nbsp;
        text = re.sub(r"\]\]\s*&nbsp;\s*(\w+)", r"]] \g<1>", text)
        text = re.sub(r"\}\}\s*&nbsp;\s*(\w+)", r"}} \g<1>", text)
        if text.find("<ref>") != -1:
            text = text.replace("{{مقالات تقبل المصادر المعادلة}}", "")

    return text


def category_clean(text: str, title: str) -> str:
    """
    !
    """

    oldtext = text

    if not title.startswith("تصنيف:"):
        return text

    text = text.replace("[[category:", "[[تصنيف:")
    text = text.replace("[[Category:", "[[تصنيف:")

    text = text.replace("[[تصنيف:تصنيفات حسب ", "[[Category:تصنيفات حسب ")

    logger.info("<<lightblue>> category_clean: title:%s" % title)

    ter = ""

    if title.endswith("حسب البلد"):
        t2 = title[: -(len("حسب البلد"))].strip()
        # logger.info(f"t2:{t2}")
        text = re.sub(rf"(\[\[{t2})\]\]", r"\g<1>|*]]", text)

    if title.startswith("تصنيف:سنوات في ") or title.endswith("حسب السنة"):
        text = re.sub(r"(\[\[تصنيف\:(?:[^\]\[\|]+) حسب السنة)\]\]", r"\g<1>|*]]", text)
        text = re.sub(r"(\[\[تصنيف\:\s*سنوات في (?:[^\]\[\|]+))\]\]", r"\g<1>|*]]", text)

        ter = title.split(" حسب السنة")[0]

    if title.startswith("تصنيف:عقود في ") or title.endswith("حسب العقد"):
        text = re.sub(r"(\[\[تصنيف\:(?:[^\]\[\|]+) حسب العقد)\]\]", r"\g<1>|*]]", text)
        text = re.sub(r"(\[\[تصنيف\:\s*عقود في (?:[^\]\[\|]+))\]\]", r"\g<1>|*]]", text)

        ter = title.split(" حسب العقد")[0]

    if ter and ter != title:
        ter = ter.replace("تصنيف:", "")
        ter2 = ter.strip().split(" ")[0]
        ter3 = ter2

        if ter2.startswith("ال"):
            ter3 = ter2[2:]

        # work in cat :تصنيف:الطب حسب السنة change [[تصنيف:طب]] to [[تصنيف:طب|*]]
        text = re.sub(rf"(\[\[تصنيف\:(?:{ter2}|{ter3}))\]\]", r"\g<1>|*]]", text)

    term = ""
    year = ""

    mat1 = re.match(r"^تصنيف\:(\w+|\w+ \w+)\sفي (\d\d\d\d|\d\d\d)$", title)
    mat2 = re.match(r"^تصنيف\:(\d\d\d\d|\d\d\d) في (\w+|\w+ \w+)$", title)
    mat3 = re.match(r"^تصنيف\:(\w+|\w+ \w+)\s (\d\d\d\d|\d\d\d)$", title)

    if mat1:
        term = mat1.group(1)
        year = mat1.group(2)
    elif mat2:
        year = mat2.group(1)
        term = mat2.group(2)
    elif mat3:
        year = mat3.group(1)
        term = mat3.group(2)

    dec = ""

    if len(year) == 4:
        dec = year[:2] + "00"
        logger.info(f"<<lightred>> dec:{dec}")

    term4s = {
        "ماساتشوستس": "ماساشوستس",
    }

    if term and year:
        term2 = term.strip().split(" ")[0]
        # if term2.startswith('ال'): term2 = term2[2:]

        term4 = term.strip()  # .replace(' ال',' ')
        # if term4.startswith('ال'): term4 = term4[2:]

        logger.info(f"<<lightyellow>> term:{term},year:{year}")

        if dec:
            text = re.sub(rf"(\[\[تصنيف\:\s*عقد {dec} في {term})\]\]", rf"\g<1>|{year}]]", text)

        # [[Category:2017]] to [[Category:2017|علم]]
        text = re.sub(rf"(\[\[تصنيف\:{year})\]\]", rf"\g<1>|{term2}]]", text)

        # إضافة الاسم كمفتاح للتصنيف
        text = re.sub(rf"(\[\[تصنيف\:{year} حسب البلد)\]\]", rf"\g<1>|{term2}]]", text)
        text = re.sub(
            rf"(\[\[تصنيف\:{year} في الولايات المتحدة حسب الولاية)\]\]",
            rf"\g<1>|{term}]]",
            text,
        )

        # إضافة السنة كمفتاح للتصنيف
        text = re.sub(
            rf"(\[\[تصنيف\:\s*عقد \d\d\d\d في {term})\s*\]\]",
            rf"\g<1>|{year}]]",
            text,
        )
        text = re.sub(
            rf"(\[\[تصنيف\:\s*{term} في\s*عقد \d\d\d\d)\s*\]\]",
            rf"\g<1>|{year}]]",
            text,
        )

        text = re.sub(rf"(\[\[تصنيف\:\s*عقود في {term})\s*\]\]", rf"\g<1>|{year}]]", text)
        text = re.sub(rf"(\[\[تصنيف\:{term} حسب العقد)\s*\]\]", rf"\g<1>|{year}]]", text)

        text = re.sub(rf"(\[\[تصنيف\:{term} حسب السنة)\s*\]\]", rf"\g<1>|{year}]]", text)
        text = re.sub(rf"(\[\[تصنيف\:\s*سنوات في {term})\s*\]\]", rf"\g<1>|{year}]]", text)

        text = re.sub(
            rf"(\[\[تصنيف\:\s*سنوات القرن \d\d في {term})\s*\]\]",
            rf"\g<1>|{year}]]",
            text,
        )

        if term in term4s:
            term4 = term4s[term]
            text = re.sub(rf"(\[\[تصنيف\:{term4} حسب السنة)\s*\]\]", rf"\g<1>|{year}]]", text)
            text = re.sub(
                rf"(\[\[تصنيف\:\s*سنوات في {term4})\s*\]\]",
                rf"\g<1>|{year}]]",
                text,
            )
            text = re.sub(
                rf"(\[\[تصنيف\:\s*سنوات القرن \d\d في {term4})\s*\]\]",
                rf"\g<1>|{year}]]",
                text,
            )

    text = text.replace("[[Category:", "[[تصنيف:")

    if oldtext != text:
        logger.info("<<lightgreen>> category_clean done. ")

    return text


def minis_clean(text: str) -> str:
    """
    !
    """
    text = re.sub(
        r"\{\{\#ifeq\:\{\{SUBPAGENAME\}\}\|sandbox\|\|",
        "{{#ifeq:{{SUBPAGENAME}}|ملعب||",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\=\s*usage\s*\=", "= الاستخدام =", text)

    text = re.sub(
        r"\=\s*infoboxes using this template\s*\=",
        "= صناديق معلومات تستخدم هذا القالب =",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\=\s*References\s*\=", "= مراجع =", text, flags=re.IGNORECASE)
    text = re.sub(r"\=\s*Notes\s*\=", "= ملاحظات =", text, flags=re.IGNORECASE)
    text = re.sub(r"\=\s*see also\s*\=", "= طالع أيضاً =", text, flags=re.IGNORECASE)

    text = re.sub(r"\=\s*tracking categories\s*\=", "= تصانيف التتبع =", text, flags=re.IGNORECASE)
    text = re.sub(r"\=\s*templatedata\s*\=", "= بيانات القالب =", text, flags=re.IGNORECASE)
    text = re.sub(r"\=\s*description\s*\=", "= وصف =", text, flags=re.IGNORECASE)
    text = re.sub(r"\=\s*examples\s*\=", "= أمثلة =", text, flags=re.IGNORECASE)
    text = re.sub(r"\=\s*options\s*\=", "= خيارات =", text, flags=re.IGNORECASE)

    text = re.sub(r"\=\s*Parameters\s*\=", "= المعلمات =", text, flags=re.IGNORECASE)

    text = re.sub(
        r"\<\!\-\- Please place categories where indicated at the bottom of this page and interwikis at Wikidata \(see \[\[(Wikipedia\:Wikidata|ويكيبيديا:ويكي بيانات)\]\]\) \-\-\>",
        "<!-- فضلاً أضف التصانيف أسفل الصفحة. ووصلات الانترويكي في ويكي بيانات  (أنظر [[ويكيبيديا:ويكي بيانات]]) -->",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\<\!\-\- (Categories and interwikis go at the bottom of this page.|Categories go at the bottom of this page and interwikis go in Wikidata.) \-\-\>",
        "<!-- فضلاً أضف التصانيف أسفل الصفحة. ووصلات الانترويكي في ويكي بيانات  -->",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\<\!\-\- (Categories go here, and interwikis go in Wikidata|Categories and interwikis go here:) \-\-\>",
        "<!-- التصانيف هنا، ووصلات الانترويكي في ويكي بيانات  -->",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\<\!\-\- EDIT TEMPLATE DOCUMENTATION BELOW THIS LINE \-\-\>",
        "<!-- تعديل صفحة توثيق القالب أسفل هذا السطر -->",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\<\!\-\- Categories below this line\, please\; interwikis at Wikidata \-\-\>",
        "<!-- التصانيف هنا، ووصلات الانترويكي في ويكي بيانات  -->",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\{\{Module\:Location map\/data\/doc\|",
        "{{وحدة:Location map/data/شرح|",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\|\s*subdivision_type\s*\=\s*Country",
        "| subdivision_type = البلد",
        text,
        flags=re.IGNORECASE,
    )

    return text


def replaces_text(changed_text: str, title: str) -> str:
    """
    !
    """

    if changed_text.find("{{مراجع") == -1:
        changed_text = changed_text.replace('<references group="" responsive="0"></references>', "{{مراجع}}")
        changed_text = changed_text.replace("<references />", "{{مراجع}}")

    changed_text = changed_text.replace("{{PAGENAME}}", "{{اسم_الصفحة}}")
    changed_text = changed_text.replace("{{اسم الصفحة}}", "{{اسم_الصفحة}}")

    changed_text = changed_text.replace("{{شريط بوابات|||", "{{شريط بوابات|")
    changed_text = changed_text.replace("{{شريط بوابات||", "{{شريط بوابات|")

    changed_text = changed_text.replace("\n\n\n{{روابط شقيقة", "\n{{روابط شقيقة").replace(
        "\n\n{{روابط شقيقة", "\n{{روابط شقيقة"
    )
    changed_text = changed_text.replace("\n\n\n{{شريط بوابات", "\n{{شريط بوابات").replace(
        "\n\n{{شريط بوابات", "\n{{شريط بوابات"
    )

    changed_text = re.sub(
        r"\{\{(مراجع|روابط رياضية|روابط فنية|مواقع التواصل الاجتماعي)\}\}\{\{",
        "{{" + r"\g<1>" + "}}\n{{",
        changed_text,
    )

    changed_text = changed_text.replace("{{مراجع}}{{", "{{مراجع}}\n{{")
    changed_text = changed_text.replace("}}{{شريط بوابات", "}}\n{{شريط بوابات")
    changed_text = changed_text.replace("}}{{مراجع", "}}\n{{مراجع")
    changed_text = changed_text.replace("}}{{بذرة", "}}\n{{بذرة")

    if changed_text.find("{{مراجع") == -1:
        changed_text = changed_text.replace('<references group="" responsive="0"></references>', "{{مراجع}}")
        changed_text = changed_text.replace("<references />", "{{مراجع}}")

    changed_text = changed_text.replace(f"[[تصنيف:{title}]]", f"[[تصنيف:{title}|*]]")
    changed_text = changed_text.replace(f"[[تصنيف:{title}| ]]", f"[[تصنيف:{title}|*]]")
    changed_text = changed_text.replace(f"[[تصنيف:{title}|{title}]]", f"[[تصنيف:{title}|*]]")

    return changed_text


def do_cosmetic_changes(
    text: str,
    title: str = "",
    page_ns: int | str | None = None,
) -> str:
    changed_text = text

    if page_ns is None:
        page_ns = 0

    changed_text = re.sub(r"\n\n\n+", r"\n\n", changed_text)

    if "nocosme" in sys.argv:
        return text

    # changed_text = ren.change_params( changed_text )

    if "norename" not in sys.argv:
        changed_text = ren.change_params(changed_text)

    try:
        ns_int = int(page_ns)
    except (ValueError, TypeError):
        ns_int = 0
    changed_text = co_change(changed_text, title, ns_int)

    changed_text = replaces_text(changed_text, title)

    if "encode" in sys.argv:
        changed_text = encode2.decode_arabic(changed_text)

    if str(page_ns) == "10":
        changed_text = minis_clean(changed_text)

    if str(page_ns) == "0" or "allns" in sys.argv:
        changed_text = fix_portal_bar(changed_text, ns=0)
        changed_text = _fix_cite_urls(changed_text)

    if str(page_ns) == "14" or title.startswith("تصنيف:"):
        changed_text = category_clean(changed_text, title)
        changed_text = fix_portal_bar(changed_text, temp_title="بوابة", ns=14)

    changed_text = format_text(changed_text)

    changed_text = fix_dead_param(changed_text)

    return changed_text


__all__ = [
    "fix_portal_bar",
    "do_cosmetic_changes",
]
