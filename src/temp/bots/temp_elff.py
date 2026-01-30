#!/usr/bin/python3
"""

from .temp_elff import Make_Elff_temp

"""
import logging
import re

from .load_data import cacaca

logger = logging.getLogger(__name__)


def Make_Elff_temp(title):
    logger.info(f" Make_Elff_temp :{title} ", "blue")

    title = re.sub(r"الألفية الأولى", "الألفية 1", title)
    title = re.sub(r"الألفية الثانية", "الألفية 2", title)
    title = re.sub(r"الألفية الثالثة", "الألفية 3", title)

    for texx, xdx in cacaca.items():
        regex = rf"تصنيف\:{texx}الألفية (\d+|)( ق م| ق\.م|)"
        regex = regex + "( في |)(.*|)$"
        test = re.sub(regex, "", title)

        if test:
            continue
        elffs = re.sub(regex, r"\g<1>", title)
        bef = re.sub(regex, r"\g<2>", title)
        In = re.sub(regex, r"\g<3>", title)
        bld = re.sub(regex, r"\g<4>", title)

        if elffs == title:
            elffs = ""
        if bef == title:
            bef = ""

        if elffs in ["1", "2", "3"] and bef == "":
            if In == title:
                In = ""
            if bld == title:
                bld = ""
            bld = bld.strip()
            logger.info(f'Make_Elff_temp : elffs:"{elffs}",bef:"{bef}",In:"{In}",bld:"{bld}"')

            temp = f"{xdx}بلد الألفية {elffs}"
            if not texx:
                temp = f"الألفية {elffs} في بلد"
            ass = ""
            if bld:
                ass = f"|{bld}"
                if bld.startswith("حسب"):
                    ass = ass + "|في="
            if not bld:
                temp = f"{xdx} الألفية {elffs}"

            text = f"{{{{{temp}{ass}}}}}"
            return text, temp

    Caas = False
    teg = ""
    for texx in cacaca:
        p_22 = f"تصنيف:{texx}الألفية"
        if title.startswith(p_22):
            teg = texx
            Caas = True
            break
    if not Caas:
        logger.info(" no Caas")
        return "{{تصنيف موسم}}", "تصنيف موسم"

    logger.info(f' Make_Elff_temp:{title} , tex:"{teg}"', "blue")
    t_1 = f"تصنيف:{teg}الألفية"
    ttt = t_1 + r"\s*(\d|الأولى|الثانية|الثالثة|الرابعة|)\s*(في |)(.*|)$"
    logger.info(f'ttt:"{ttt}" ')
    elffs = re.sub(ttt, r"\g<1>", title)
    In = re.sub(ttt, r"\g<2>", title)
    bld = re.sub(ttt, r"\g<3>", title)
    if elffs == title:
        elffs = ""
    if bld == title:
        bld = ""

    logger.info(f'elffs:"{elffs}",bld:"{bld}"')

    if not elffs:
        return "{{تصنيف موسم}}", "تصنيف موسم"

    templatename = f"{cacaca[teg]}بلد الألفية {elffs}"

    bld = bld.strip()
    if bld.startswith("حسب") or bld == "":
        bld = bld + "|في="
    text = f"{{{{{templatename}|{bld}}}}}\n"  # noqa
    if not teg:
        templatename = f"الألفية {elffs} في بلد"
        text = f"{{{{{templatename}|{bld}}}}}\n"  # noqa

    return text, templatename
