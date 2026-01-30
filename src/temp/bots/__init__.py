#!/usr/bin/python3
"""

# (main_make_temp|MakedecadesTemp|Make_Elff_temp|Make_Cent_temp|Make_years_temp)

بوت لإضافة قالب السنوات للتصنيفات

from .temp import main_make_temp, Make_years_temp

"""
import logging
import re

from ...helps import dump_data
from .load_data import cacaca
from .temp_cent import Make_Cent_temp
from .temp_decades import MakedecadesTemp
from .temp_elff import Make_Elff_temp
from .temp_years import Make_years_temp

logger = logging.getLogger(__name__)


def main_make_temp(enca, title) -> tuple[str, str]:
    title = re.sub(r"_", " ", title)
    logger.info("=====================")
    logger.info(f'main: title:"{title}"')

    if title.find("فيروس كورونا") != -1:
        return "", ""

    if re.match(r"^تصنيف\:\d+$", title):
        return "{{تصنيف موسم}}", "تصنيف موسم"

    if re.match(r"^تصنيف\:\d+ ق م$", title):
        return "{{تصنيف موسم}}", "تصنيف موسم"

    mat = re.match(r"^تصنيف\:(\d\d\d\d\–\d\d\d\d|\d\d\d\d\-\d\d\d\d|\d\d\d\d\–\d\d|\d\d\d\d\-\d\d).*", title)
    if mat:
        text = "{{تصنيف موسم}}\n"
        return text, "تصنيف موسم"

    for month in [
        "يناير",
        "فبراير",
        "مارس",
        "أبريل",
        "مايو",
        "يونيو",
        "يوليو",
        "أغسطس",
        "سبتمبر",
        "أكتوبر",
        "نوفمبر",
        "ديسمبر",
    ]:
        tt = f"تصنيف:{month}"
        tt2 = f"تصنيف:أحداث {month}"
        if title.startswith(tt) or title.startswith(tt2):
            text = f"{{{{تصنيف شهر|{month}}}}}\n"  # noqa
            return text, "تصنيف شهر"

    if title.startswith("تصنيف:صناديق تصفح"):
        text = "{{تصنيف قوالب|النوع=تصفح}}\n"
        return text, "تصنيف قوالب"

    for tex in ["تأسيسات ", "انحلالات "]:
        for numb in range(0, 10):
            t_2 = f"تصنيف:{tex}{numb}"
            t_33 = f"تصنيف:{tex}سنة {numb}"
            t_44 = f"تصنيف:{tex}عام {numb}"
            if title.startswith(t_2) or title.startswith(t_33) or title.startswith(t_44):
                return Make_years_temp(title, tex, return_title=True)

    for texd in ["تصنيف:تأسيسات عقد", "تصنيف:انحلالات عقد", "تصنيف:عقد"]:
        if title.startswith(texd):
            logger.info(f'title.startswith("{texd}" ):')
            return MakedecadesTemp(title)

    for tex in cacaca:
        if title.startswith(f"تصنيف:{tex}القرن"):
            return Make_Cent_temp(title)

        if title.startswith(f"تصنيف:{tex}الألفية"):
            return Make_Elff_temp(title)

    if re.match(r"^تصنيف\:(.*) في القرن (.*)$", title):
        return "{{تصنيف موسم}}", "تصنيف موسم"

    if re.match(r".*\d\d\d\d[\-\–]\d\d$", title):
        return "{{تصنيف موسم}}", "Navseasoncats"

    if not title.startswith("عقد") and not title.startswith("تصنيف:القرن"):
        if re.match(r"^تصنيف\:\d+.*", title) or re.match(r"^تصنيف\:.*\d+$", title):
            return "{{تصنيف موسم}}", "تصنيف موسم"

    if re.match(r"\d\d\d\d[\-\–]\d\d$", title):
        return "{{تصنيف موسم}}", "تصنيف موسم"

    return "", ""


# @dump_data(1)
def main_make_temp_no_title(title) -> str:
    result, _ = main_make_temp("", title)

    return result.strip()


__all__ = [
    "MakedecadesTemp",
    "Make_years_temp",
    "Make_Cent_temp",
    "Make_Elff_temp",
    "main_make_temp",
    "main_make_temp_no_title",
]
