#!/usr/bin/python3
""" """

from ...temp import main_make_temp_no_title
from ..new_api import load_main_api
from ..wd_bots import Get_P373_API
from .categorytext_data import LocalLanguageLinks, category_mapping
from .utils import portal_en_to_ar_lower


def get_page_link_data(title: str, sitecode: str, ns: int = 100) -> list:
    api = load_main_api(sitecode)
    page = api.MainPage(title)

    json1 = page.page_links()

    if not json1:
        return []

    data = []

    # [{'ns': 14, 'title': 'تصنيف:مقالات بحاجة لشريط بوابات', 'exists': True}, {'ns': 14, 'title': 'تصنيف:مقالات بحاجة لصندوق معلومات', 'exists': False}]

    for cx in json1:
        page_ns = int(cx.get("ns"))
        if not cx.get("title") or not cx.get("exists"):
            continue
        if page_ns == ns:
            data.append(cx.get("title"))

    return data


def fetch_commons_category(entitle, Qid):
    template = ""
    P373 = Get_P373_API(q=Qid, titles=entitle, sites="enwiki")

    if P373:
        template = "{{تصنيف كومنز|%s}}" % P373

    return template


def generate_portal_content(title, enca, return_list=False):
    lilo = []
    en_links = get_page_link_data(enca, "en", 100)

    for x in en_links:
        cc = x.replace("Portal:", "")
        if cc.lower() in portal_en_to_ar_lower:
            lilo.append(portal_en_to_ar_lower[cc.lower()])

    # lilo = [ portal_en_to_ar_lower[x.lower()] for x in en_params if x.lower() in portal_en_to_ar_lower ]

    # lilo = []
    for cd in category_mapping:
        portal = category_mapping[cd]
        if title.find(cd) != -1 and portal not in lilo:
            lilo.append(portal)

    for xc in LocalLanguageLinks:
        if xc not in lilo:
            if title.find(" %s " % xc) != -1 or title.startswith("تصنيف:%s " % xc) or title.endswith(" %s" % xc):
                lilo.append(xc)

    litp = ""

    if len(lilo) != 0:
        litp = "|".join(lilo)

        litp = "{{بوابة|%s}}\n" % litp

    if return_list:
        return litp, lilo

    return litp


def generate_category_text(enca, title, Qid):
    ff = main_make_temp_no_title(enca, title)

    text = ""
    text += generate_portal_content(title, enca)
    text += "{{نسخ:#لوموجود:{{نسخ:اسم_الصفحة}}|{{مقالة تصنيف}}|}}\n"
    text += fetch_commons_category(enca, Qid)

    if ff:
        text += "\n%s" % ff

    return text
