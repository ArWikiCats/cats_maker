#!/usr/bin/python3


from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
Dir = str(Path(__file__).parent.parent)

# "الرقم المعياري": ["رقم معياري",  "رقم معياري",  "ردمك",  "ISBN", ],
""""عنوان مترجم": [
    "trans-title",  "trans_title",  "العنوان المترجم",  "trans title",  "transtitle",
    # "العنوان بالعربي",
    # "العنوان باللغة العربية"
],
"عنوان أجنبي": [
    "script-title",  "العنوان الأجنبي",
],"""

newlist_fr_a = {
    "عنوان مترجم": ["trans-title", "trans_title", "trans title", "transtitle"],
    "صيغة": ["التنسيق", "format", "تنسيق", "filetype", "foramt", "formato"],
    "طبعة": [
        "إصدار",
        "الإصدار",
        "الاصدار",
        "اصدار",
        "auflage",
        "baskı",
        "الطبعة",
        "رقم الطبعة",
        "edition",
        "editoin",
        "editon",
        "edizione",
    ],
    "وصلة مكسورة": ["dead-url", "deadurl", "رابط معطوب", "وصلة ميتة"],
    "تاريخ وصلة مكسورة": ["dead-date", "deaddate"],
    "التسجيل": ["url-access"],
    "تاريخ الوصول": ["تاريخ وصول", "access-date", "accessdate", "accessDate"],
    "حالة المسار": ["حالة مسار", "urlstatus", "url-status"],
    "تاريخ أرشيف": ["تاريخ الأرشيف", "archive-date", "تاريخ-الأرشيف", "archivedate"],
    "تنسيق الأرشيف": ["archive-format", "تنسيق-الأرشيف", "تنسيق أرشيف"],
    "مسار أرشيف": [
        "مسار الأرشيف",
        "archive-url",
        "archiveurl",
        "مسار-الأرشيف",
        "رابط الأرشيف",
        "archiv-url",
        "archive url",
        "archive-link",
    ],
    "المؤلفون": [
        "المؤلفين",
        "authors",
        "people",
        "host",
        "credits",
        "أشخاص",
        "مؤلفين مشاركين",
        "مؤلفون",
        "coauthors",
        "المؤلفين المشاركين",
    ],
    "عنوان الكتاب": ["book-title", "booktitle"],
    "الفصل": [
        "chapter",
        "contribution",
        "entry",
        "article",
        "section",
        "قسم",
        "القسم",
        "فصل",
        "chapter_title",
    ],
    "المجلد": ["مجلد", "volume", "vol"],  # "الجزء"
    "وكالة": ["agency", "الوكالة", "service"],
    "المدينة": ["city", "مدينة"],
    "تنسيق الفصل": ["chapter-format", "contribution-format", "section-format"],
    "مسار الفصل": [
        "chapter-url",
        "chapterurl",
        "contribution-url",
        "contributionurl",
        "section-url",
        "sectionurl",
    ],
    "تنسيق المؤتمر": ["conference-format", "event-format"],
    "الدرجة": ["degree"],
    "عنوان المؤتمر": [
        "conference",
        "اسم المؤتمر",
        "المؤتمر",
        "مؤتمر",
        "event",
        "المناسبة",
        "مناسبة",
    ],
    "مسار المؤتمر": ["conference-url", "conferenceurl", "event-url", "eventurl"],
    "تاريخ": ["التاريخ", "date", "air-date", "airdate"],
    "إظهار المؤلفين": ["display-authors", "displayauthors", "إظهار المؤلفون"],
    "إظهار المحررين": ["display-editors", "displayeditors", "display-المحررين"],
    "عدة مؤلفين": ["vauthors", "v-authors"],
    "عدة محررين": ["veditors", "v-editors"],
    "المعرف": ["id", "ID"],
    "تجاهل خطأ ردمك": [
        "ignore-isbn-error",
        "ignoreisbnerror",
        "تجاهل خطأ الرقم المعياري",
        "تجاهل خطأ isbn",
    ],
    "العدد": ["issue", "number", "عدد"],
    "لغة": ["اللغة", "language", "in", "lang"],
    "موقع": ["website", "الموقع", "اسم الموقع", "الموقع الرسمي", "site"],
    "القائمة البريدية": ["اسم القائمة البريدية", "mailing-list", "mailinglist"],
    "مسار الخريطة": ["mapurl", "map-url"],
    "الخريطة": ["map"],
    "تنسيق الخريطة": ["map-format", "mapformat"],
    "شهر": ["mounth", "الشهر", "month"],
    "سنة النشر الأصلية": ["orig-year", "origyear"],
    "آخرون": [
        "المحاور",
        "others",
        "interviewer",
        "interviewers",
        "المحاورون",
        "المحقق",
        "آخر",
        "other",
    ],
    "صفحة": ["p", "الصفحة", "page", "رقم الصفحة", "رقم صفحة"],
    "صفحات": ["الصفحات", "pp", "أرقام الصفحات", "أرقم صفحات", "pages", "أرقام صفحات"],
    "موسوعة": ["encyclopedia", "encyclopaedia", "اسم الموسوعة", "encyclopædia"],
    "صحيفة": [
        "journal",
        "newspaper",
        "اسم الصحيفة",
        "جريدة",
        "الصحيفة",
        "nespaper",
        "newpaper",
        "news",
        "news-paper",
    ],
    "مجلة": ["magazine", "المجلة", "اسم المجلة"],
    "عمل": ["work", "العمل", "من عمل"],
    "دورية": ["periodical", "اسم الدورية"],
    "معجم": ["dictionary", "المعجم", "اسم المعجم"],
    "مكان": ["place", "المكان", "مقر", "المقر", "location", "address", "loaction"],
    "تاريخ النشر": ["publicationdate", "publication-date", "سنة النشر"],
    "مكان النشر": [
        "publication-place",
        "publicationplace",
        "originalort",
        "pulbication-place",
    ],
    "ناشر": [
        "publisher",
        "الناشر",
        "distributor",
        "institution",
        "مصدر",
        "الموزع",
        "المصدر",
        "المؤسسة",
        "اسم المجموعة",
        "publicationtitle",
    ],
    "اقتباس": ["quote", "quotation", "اقتبس"],
    "سلسلة": ["series", "version", "السلسلة"],
    "مسار المسلسل": ["series-link", "serieslink", "وصلة سلسلة"],
    "رقم سلسلة": ["series-number", "series-no", "seriesnumber", "seriesno"],
    "الوقت": ["time", "وقت الوقوع"],
    "عنوان": [
        "title",
        "العنوان",
        "başlık",
        "originaltitel",
        "tile",
        "tite",
        "titel",
        "titel-p",
        "titled",
        "titolo",
        "titre",
        "tytuł",
        "títle",
        "título",
    ],  # "اسم المسلسل",
    "وصلة العنوان": ["title-link", "titlelink"],
    "وصلة الحلقة": ["episode-link", "episodelink"],
    "الحلقة": ["حلقة", "episode"],
    "النوع": ["type", "medium"],
    "مسار": ["url", "المسار", "وصلة", "الرابط", "رابط", "URL"],
    "سنة": ["year", "السنة", "Year", "عام"],
    "سنة الوصول": ["access-year", "accessyear"],
    "مجموعة": ["inset", "in-set"],
    "معرف الرسالة": ["message-id"],
    "دقيقة": ["minutes"],
    "الشبكة": ["network", "net-work"],
    "المقياس": ["scale"],
    "الموسم": ["season"],
    "ورقة": ["sheet"],
    "أوراق": ["sheets"],
    "محطة": ["station", "المحطة"],
    "عبر": ["via", "بواسطة"],
    "مؤلف-وصلة": [
        "author-link",
        "authorlink",
        "وصلة المؤلف",
        "author link",
        "وصلة مؤلف",
    ],
    "محرر-وصلة": [
        "editor-link",
        "editorlink",
        "وصلة المحرر",
        "editor link",
        "وصلة محرر",
    ],
    "مترجم-وصلة": [
        "translator-link",
        "translatorlink",
        "وصلة المترجم",
        "translator link",
        "وصلة مترجم",
    ],
    "الأول": ["first", "given", "الاول"],  # "أول",
    "الأخير": ["last", "surname", "الاخير", "اخير"],  # ,  "أخير"
    "مؤلف": ["author", "المؤلف"],
    "محرر": ["المحرر", "editor"],
    "مترجم": ["translator", "المترجم"],
    "المحررين": ["editors", "المحررون"],
}

newlist_fr = {}

if "newlist_fr_a" not in sys.argv:
    for kk, labb in newlist_fr_a.items():
        newlist_fr[kk] = labb

auth_edits = {}


def add_to(i) -> None:
    auth_edits[f"مؤلف{i}"] = [f"author{i}", f"المؤلف{i}", f"auteur{i}"]
    auth_edits[f"الأول{i}"] = [
        f"أول{i}",
        # f"اول{i}",
        # f"الاول{i}",
        f"given{i}",
        f"first{i}",
    ]
    auth_edits[f"مؤلف{i}-الأول"] = [
        f"مؤلف-الأول{i}",
        f"مؤلف{i} الأول",
        f"مؤلف الأول{i}",
        f"author{i}-given",
        f"author{i}-first",
        f"author-given{i}",
        f"author-first{i}",
    ]
    auth_edits[f"الأخير{i}"] = [
        f"أخير{i}",
        # f"اخير{i}",
        # f"الاخير{i}",
        f"surname{i}",
        f"last{i}",
    ]
    auth_edits[f"مؤلف{i}-الأخير"] = [
        f"مؤلف-الأخير{i}",
        f"مؤلف{i} الأخير",
        f"مؤلف الأخير{i}",
        f"author{i}-last",
        f"author-last{i}",
    ]
    auth_edits[f"مؤلف{i}-وصلة"] = [
        f"وصلة مؤلف{i}",
        f"وصلة المؤلف{i}",
        f"وصلة-المؤلف{i}",
        f"مؤلف{i} وصلة",
        f"وصلة-مؤلف{i}",
        f"المؤلف{i} وصلة",
        f"المؤلف{i}-وصلة",
        f"authorlink{i}",
        f"author{i}-link",
        f"author-link{i}",
    ]

    auth_edits[f"محرر{i}"] = [f"editor{i}", f"المحرر{i}"]
    auth_edits[f"محرر{i}-الأول"] = [
        f"محرر{i} الأول",
        f"محرر-الأول{i}",
        f"محرر الأول{i}",
        f"editor{i}-first",
        f"editor-first{i}",
    ]
    auth_edits[f"محرر{i}-الأخير"] = [
        f"محرر{i}-الأخير",
        f"محرر{i} الأخير",
        f"محرر الأخير{i}",
        f"editor{i}-last",
        f"editor-last{i}",
    ]
    auth_edits[f"محرر{i}-وصلة"] = [  # وصلة-محرر{i}
        f"محرر-وصلة{i}",
        f"وصلة محرر{i}",
        f"وصلة المحرر{i}",
        f"وصلة-المحرر{i}",
        f"محرر{i} وصلة",
        f"وصلة-محرر{i}",
        f"المحرر{i} وصلة",
        f"المحرر{i}-وصلة",
        f"editorlink{i}",
        f"editor{i}-link",
        f"editor-link{i}",
        # f"{i}وصلة محرر",
        # f"{i}وصلة المحرر",
    ]

    auth_edits[f"مترجم{i}"] = [f"translator{i}", f"المترجم{i}"]
    auth_edits[f"مترجم{i}-وصلة"] = [
        f"translator-link{i}",
        f"translator{i}-link",
        f"المترجم{i}-وصلة",
        f"وصلة-مترجم{i}",
        f"وصلة مترجم{i}",
        f"وصلة-المترجم{i}",
    ]
    auth_edits[f"مترجم{i}-الأول"] = [
        f"مترجم-الأول{i}",
        f"مترجم{i} الأول",
        f"مترجم الأول{i}",
        f"translator{i}-first",
        f"translator-first{i}",
        f"translator{i}-given",
        f"translator-given{i}",
        f"المترجم-الأول{i}",
        f"المترجم{i}-الأول",
    ]
    auth_edits[f"مترجم{i}-الأخير"] = [
        f"مترجم-الأخير{i}",
        f"مترجم{i} الأخير",
        f"مترجم الأخير{i}",
        f"translator{i}-last",
        f"translator-last{i}",
        f"المترجم-الأخير{i}",
        f"المترجم{i}-الأخير",
        f"translator-surname{i}",
        f"translator{i}-surname",
    ]

    if isinstance(i, int) and i < 5:
        auth_edits[f"مشارك{i}"] = [f"contributor{i}", f"المشارك{i}"]
        auth_edits[f"مشارك{i}-الأول"] = [
            f"مشارك-الأول{i}",
            f"contributor-first{i}",
            f"contributor{i}-first",
            f"contributor-given{i}",
            f"contributor{i}-given",
        ]
        auth_edits[f"مشارك{i}-الأخير"] = [
            f"مشارك-الأخير{i}",
            f"contributor-last{i}",
            f"contributor{i}-last",
            f"contributor-surname{i}",
            f"contributor{i}-surname",
        ]
        auth_edits[f"مشارك{i}-وصلة"] = [f"contributor{i}-link", f"contributor-link{i}"]

        auth_edits[f"مؤلف{i}-قناع"] = [f"author{i}-mask", f"author-mask{i}"]
        auth_edits[f"محرر{i}-قناع"] = [f"editor{i}-mask", f"editor-mask{i}"]
        auth_edits[f"مترجم{i}-قناع"] = [f"translator{i}-mask", f"translator-mask{i}"]
        auth_edits[f"مشارك{i}-قناع"] = [f"contributor{i}-mask", f"contributor-mask{i}"]


add_to("")

# for x in auth_edits.keys(): logger.info(x)

for i in range(1, 20):
    add_to(i)

for i in range(21, 200):
    auth_edits[f"الأول{i}"] = [f"given{i}", f"first{i}"]
    auth_edits[f"الأخير{i}"] = [f"surname{i}", f"last{i}"]

for new, bb in auth_edits.items():
    # bbnew = bb
    bbnew = [x for x in bb if x != new]

    newlist_fr[new] = bbnew

all_cite_refs_params = {}

for key in newlist_fr:
    for value in newlist_fr[key]:
        all_cite_refs_params[value] = key


__all__ = [
    "add_to",
]
