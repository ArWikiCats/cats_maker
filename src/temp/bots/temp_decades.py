#!/usr/bin/python3
"""

from .temp_decades import MakedecadesTemp

"""
import logging
import re

from .load_data import Baco_decades, cacaca

logger = logging.getLogger(__name__)


def MakedecadesTemp(title):
    Caa = False
    logger.info(f" :{title} ", "blue")
    tex = ""
    title = re.sub(r"_", " ", title)

    for texx, ssss in cacaca.items():
        regdd = rf"{texx}عقد (\d+)( ق م| ق\.م|)"
        regex = "تصنيف:" + regdd + "( في |)(.*|)$"
        test = re.sub(r"تصنيف:", "", title)
        test = re.sub(regdd, "", test)
        if title:
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

            if bef:
                dee = "-" + dee

            if dee:
                if dee in Baco_decades:
                    bld = bld.strip()

                    _sss, ass = "", ""
                    if bld:
                        if In:
                            ass = f"|بلد={bld}"
                        elif bld.startswith("حسب"):
                            ass = f"|حسب={bld}"

                    Qrn = str(Baco_decades[dee])
                    _Dee = dee

                    logger.info(f'Dee:"{dee}",bef:"{bef}",In:"{In}",bld:"{bld}"')

                    temp = f"{ssss}عقد"
                    if not texx:
                        temp = "تصنيف عقد"
                    text = f"{{{{{temp}|قرن={Qrn}|عقد={dee}{ass}}}}}"  # noqa
                    return text, temp
                else:
                    logger.info(f"dee {dee} not in Baco_decades")
        else:
            logger.info(f"test = '{test}' ")

    for texx in cacaca:
        p_2 = f"تصنيف:{texx}عقد"
        if title.startswith(p_2):
            tex = texx
            logger.info(f' :{title} , texx:"{texx}"', "blue")

    if Caa:
        logger.info(f' Caa: :{title} , tex:"{tex}"', "blue")
        t_1 = f"تصنيف:{tex}عقد "
        ttt = t_1 + r"(\d+)\s*(في |)(.*|)$"

        decade_ = re.sub(ttt, r"\g<1>", title)
        In = re.sub(ttt, r"\g<2>", title)
        bld = re.sub(ttt, r"\g<3>", title)
        if decade_ == title:
            decade_ = ""
        if bld == title:
            bld = ""
        logger.info(f" decade_:'{decade_}' , bld:'{bld}' ", "blue")
        Y, YY = "", ""

        template = f"{cacaca[tex]}بلد عقد"

        if decade_ in Baco_decades:
            qrn = Baco_decades[decade_]
            template = ""

            decade2 = str(decade_)
            dex = ""

            if len(decade2) == 4:
                Y = decade2[0] + decade2[1]  # + decade2[2]
                YY = decade2[2]
            elif len(decade2) == 3:
                Y = decade2[0]
                YY = decade2[1]  # + decade2[1]
            elif len(decade2) == 2:
                Y, YY = "", ""
                dex = decade2
            else:
                logger.info(f' len(decade2) :"{len(decade2)}".', "red")

            logger.info(f" Y:{Y} , YY:{YY} ,len(decade2): {len(decade2)}.", "red")

            sus = ""
            if not In:
                sus = "|في="
            if dex:
                dex = "|عقد=" + dex

            template = f"{cacaca[tex]}بلد عقد"
            text = f"{{{{{template}|{Y}|{YY}|{dex}|قرن={qrn}|بلد={bld}{sus}}}}}\n"  # noqa

            if not bld:
                template = f"{tex}عقد"
                text = f"{{{{{template}|{Y}|{YY}|قرن={qrn}{sus}}}}}\n"  # noqa

            return text, template
        else:
            logger.info(f"decade_ {decade_} not in Baco_decades")
    return "{{تصنيف موسم}}", "تصنيف موسم"
