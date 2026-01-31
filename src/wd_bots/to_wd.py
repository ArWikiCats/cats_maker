#!/usr/bin/python3
"""
Wikidata functions for cats_maker_new bot
"""
import functools
import logging

from . import NewHimoAPIBot
from .wd_desc import wwdesc

logger = logging.getLogger(__name__)

wikimedia_category_descraptions = {  # Wikimedia category
    "ace": "kawan Wikimèdia",
    "af": "Wikimedia-kategorie",
    "an": "categoría de Wikimedia",
    "ar": "تصنيف ويكيميديا",
    # "arz":"ويكيبيديا:تصنيف",
    "ast": "categoría de Wikimedia",
    "ba": "Викимедиа категорияһы",
    "bar": "Wikimedia-Kategorie",
    "be": "катэгорыя ў праекце Вікімедыя",
    "be-tarask": "катэгорыя ў праектах Вікімэдыі",
    # "be-tarask": "катэгорыя ў праекце Вікімэдыя",
    "bg": "категория на Уикимедия",
    "bho": "विकिमीडिया श्रेणी",
    "bjn": "tumbung Wikimedia",
    "bn": "উইকিমিডিয়া বিষয়শ্রেণী",
    "br": "pajenn rummata eus Wikimedia",
    "bs": "kategorija na Wikimediji",
    "bug": "kategori Wikimedia",
    "ca": "categoria de Wikimedia",
    # "ce":"Викимедиа проектан категореш",
    # "ceb":"Wikimedia:Kategorisasyon",
    "ckb": "پۆلی ویکیمیدیا",
    "cs": "kategorie na projektech Wikimedia",
    "cy": "tudalen categori Wikimedia",
    "da": "Wikimedia-kategori",
    "de": "Wikimedia-Kategorie",
    "de-at": "Wikimedia-Kategorie",
    "de-ch": "Wikimedia-Kategorie",
    "el": "κατηγορία εγχειρημάτων Wikimedia",
    "en": "Wikimedia category",
    # "en-ca": "Wikimedia category",
    # "en-gb": "Wikimedia category",
    "eo": "kategorio en Vikimedio",
    "es": "categoría de Wikimedia",
    "et": "Wikimedia kategooria",
    "eu": "Wikimediako kategoria",
    "fa": "ردهٔ ویکی‌پدیا",
    "fi": "Wikimedia-luokka",
    "fr": "page de catégorie d'un projet Wikimédia",  # page de catégorie de Wikimedia",
    "fy": "Wikimedia-kategory",
    "gl": "categoría de Wikimedia",
    "gsw": "Wikimedia-Kategorie",
    "gu": "વિકિપીડિયા શ્રેણી",
    "he": "קטגוריה במיזמי ויקימדיה",
    "hi": "विकिमीडिया श्रेणी",
    "hr": "kategorija u wikimediju",
    "hu": "Wikimédia-kategória",
    "hy": "Վիքիմեդիայի նախագծի կատեգորիա",
    "id": "kategori Wikimedia",
    "ilo": "kategoria ti Wikimedia",
    "it": "categoria di un progetto Wikimedia",
    "ja": "ウィキメディアのカテゴリ",
    "kaa": "Wikimedia kategoriyası",
    "ko": "위키미디어 분류",
    "ky": "Wikimedia категориясы",
    "la": "categoria Vicimediorum",
    "lb": "Wikimedia-Kategorie",
    "li": "Wikimedia-categorie",
    "lv": "Wikimedia projekta kategorija",
    "mk": "Викимедиина категорија",
    "nap": "categurìa 'e nu pruggette Wikimedia",
    "nb": "Wikimedia-kategori",
    "nds": "Wikimedia-Kategorie",
    "nl": "Wikimedia-categorie",
    "nn": "Wikimedia-kategori",
    "pl": "kategoria w projekcie Wikimedia",
    "pt": "categoria de um projeto da Wikimedia",
    "pt-br": "categoria de um projeto da Wikimedia",
    "ro": "categorie în cadrul unui proiect Wikimedia",  # https://www.wikidata.org/w/index.php?title=User_talk%3AMr._Ibrahem#c-Vargenau-20250307094900-Romanian_description_for_categories
    "ru": "категория в проекте Викимедиа",
    "sco": "Wikimedia category",
    "se": "Wikimedia-kategoriija",
    "sk": "kategória projektov Wikimedia",
    "sl": "kategorija Wikimedie",  # kategorija Wikimedije  [[wd:Topic:Xjpu4y312bxi699q]]
    "smn": "Wikimedia-luokka",
    "sq": "kategori e Wikimedias",
    "sr": "категорија на Викимедији",
    "sv": "Wikimedia-kategori",
    "sw": "jamii ya Wikimedia",
    "tg": "гурӯҳи Викимедиа",
    "tg-cyrl": "гурӯҳи Викимедиа",
    "tg-latn": "guruhi Vikimedia",
    "tr": "Vikimedya kategorisi",
    "uk": "категорія проєкту Вікімедіа",  # категорія в проекті Вікімедіа [[Topic:Xdnbrl1aqt1lou5u]]
    "vi": "thể loại Wikimedia",
    "yi": "וויקימעדיע קאַטעגאָריע",
    "yo": "ẹ̀ka Wikimedia",
    "yue": "維基媒體分類",
    "zea": "Wikimedia-categorie",
    "zh": "维基媒体分类",
    "zh-cn": "维基媒体分类",
    "zh-hans": "维基媒体分类",
    "zh-hant": "維基媒體分類",
    "zh-hk": "維基媒體分類",
    "zh-mo": "維基媒體分類",
    "zh-my": "维基媒体分类",
    "zh-sg": "维基媒体分类",
    "zh-tw": "維基媒體分類",
}


@functools.lru_cache(maxsize=1)
def get_wd_api_bot() -> NewHimoAPIBot:
    return NewHimoAPIBot(Mr_or_bot="bot", www="www")


def add_label(qid, ar_title) -> None:
    get_wd_api_bot().Labels_API(qid, ar_title, "ar", True, nowait=True, tage="catelabels")


def makejson(property, numeric):
    # ---
    if numeric:
        numeric = numeric.replace("Q", "")
        Q = f"Q{numeric}"
        return {
            "mainsnak": {
                "snaktype": "value",
                "property": property,
                "datavalue": {
                    "value": {
                        "entity-type": "item",
                        "numeric-id": numeric,
                        "id": Q,
                    },
                    "type": "wikibase-entityid",
                },
                "datatype": "wikibase-item",
            },
            "type": "statement",
            "rank": "normal",
        }


def Make_New_item(artitle, entitle, family=""):
    logger.debug(f'<<lightgreen>>* :ar:"{artitle}", english:"{entitle}".')

    enwiki = "enwiki"
    arwiki = "arwiki"

    if family and family != "wikipedia":
        enwiki = f"en{family}"
        arwiki = f"ar{family}"

    data = {
        "sitelinks": {enwiki: {"site": enwiki, "title": entitle}, arwiki: {"site": arwiki, "title": artitle}},
        "labels": {"ar": {"language": "ar", "value": artitle}, "en": {"language": "en", "value": entitle}},
        "claims": {"P31": [makejson("P31", "Q4167836")]},
    }

    summary = f"Bot: New item from [[w:en:{entitle}|{enwiki}]]/[[w:ar:{artitle}|{arwiki}]]."

    new_item_id = get_wd_api_bot().New_API(data, summary, returnid=True, nowait=True, tage="newitems")

    if new_item_id and new_item_id.startswith("Q"):
        NewDesc = {lang: {"language": lang, "value": value} for lang, value in wikimedia_category_descraptions.items()}
        wwdesc(NewDesc, new_item_id, 1, [], tage="newitems")


def Log_to_wikidata(ar, enca, qid):
    if qid:
        get_wd_api_bot().Sitelink_API(qid, ar, "arwiki", nowait=True)
        get_wd_api_bot().Labels_API(qid, ar, "ar", False, nowait=True, tage="catelabels")

    else:
        cd = get_wd_api_bot().Sitelink_API("", ar, "arwiki", enlink=enca, ensite="enwiki", nowait=True)
        if cd is not True:
            Make_New_item(ar, enca, family="wikipedia")
