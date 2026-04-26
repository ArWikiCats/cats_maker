#!/usr/bin/python3
"""

from .temp_cent import Make_Cent_temp

"""

import logging
import re

from .load_data import Baco_centries, cacaca

logger = logging.getLogger(__name__)


def Make_Cent_temp(title):
    logger.info(f" :{title} ", "blue")
    Caa = False
    tex = ""
    title = re.sub(r"_", " ", title)

    for texx, cttt in cacaca.items():
        regex = rf"تصنيف\:{texx}القرن (\d+)( ق م| ق\.م|)"
        regex = regex + "( في |)(.*|)$"
        test = re.sub(regex, "", title)
        if not test:
            dee = re.sub(regex, r"\g<1>", title)
            bef = re.sub(regex, r"\g<2>", title)
            In = re.sub(regex, r"\g<3>", title)
            bld = re.sub(regex, r"\g<4>", title)

            if dee == title:
                dee = ""
            if bef == title:
                bef = ""
            if In == title:
                In = ""
            if bld == title:
                bld = ""
            bld = bld.strip()
            logger.info(f'dee:"{dee}",bef:"{bef}",In:"{In}",bld:"{bld}"')

            sss, ass = "", ""
            if bld:
                if In:
                    ass = f"|بلد={bld}"
                elif bld.startswith("حسب"):
                    ass = f"|حسب={bld}"

            if bef:
                sss = "-"
            if dee:
                temp = f"{cttt}قرن"
                if not texx:
                    temp = "سنوات في القرن"
                text = f"{{{{{temp}|{sss}{dee}{ass}}}}}"  # noqa
                return text, temp

    for texx in cacaca:
        p_2 = f"تصنيف:{texx}القرن"
        if title.startswith(p_2):
            tex = texx
            Caa = True

    if Caa:
        logger.info(f' Make Cent_temp:{title} , tex:"{tex}"', "blue")
        t_1 = f"تصنيف:{tex}القرن "
        ttt = t_1 + r"(\d+)\s*( ق م| ق\.م|)\s*(في |)(.*|)$"

        cent = re.sub(ttt, r"\g<1>", title)
        _Baoo = re.sub(ttt, r"\g<2>", title)
        In = re.sub(ttt, r"\g<3>", title)
        bld = re.sub(ttt, r"\g<4>", title)
        if cent == title:
            cent = ""
        if bld == title:
            bld = ""

        elff = 0
        logger.info(f'cent:"{cent}",bld:"{bld}"')
        if cent in Baco_centries:
            logger.info(f"cent {cent} in Baco_centries")
            elff = Baco_centries[cent]
            cent = int(cent)

            bld = bld.strip()
            if bld.startswith("حسب"):
                bld = bld + "|في="
            sdsd = str(cent - 1) + "0"
            if elff != 1 or cent == 10:
                sdsd = str(cent - 1)
            if sdsd == "00":
                sdsd = ""
            before = str(cent - 1)
            if before == "0":
                before = "1 ق م"
            template = f"{cacaca[tex]}بلد قرن"

            text = (
                f"{{{{{template}|{sdsd}|قرن={cent}|سابق={before}|لاحق={cent + 1}|ألفية={elff}|بلد={bld}}}}}\n"  # noqa
            )
            if not bld:
                template = f"{cacaca[tex]}قرن"
                text = f"{{{{{template}|{sdsd}|قرن={cent}|سابق={before}|لاحق={cent + 1}|ألفية={elff}}}}}\n"  # noqa

            return text, template

    return "{{تصنيف موسم}}", "تصنيف موسم"
