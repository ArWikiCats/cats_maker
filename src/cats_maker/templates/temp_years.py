#!/usr/bin/python3
"""
!
"""

import logging
import re

from .load_data import cacaca, years_baco

logger = logging.getLogger(__name__)


def make_years_template(title, tex) -> tuple[str, str]:
    logger.info(f' :{title} , tex:"{tex}"')
    if title.find("ق م") != -1 or title.find("ق.م") != -1:
        return "", ""

    t_1 = f"تصنيف:{tex}"
    ttt = t_1 + r"(عام |سنة |)(\d+)\s*(في |)(.*|)$"
    ye = re.sub(ttt, r"\g<2>", title)

    bld = re.sub(ttt, r"\g<4>", title)
    if ye == title:
        ye = ""

    template = f"{cacaca[tex]}بلد"
    logger.info(f" :{title} , ye:{ye}, tex:{tex}")

    second_param, first_param = "", ""

    if ye in years_baco:
        logger.info(f"ye in years_baco {years_baco[ye]}")
        if len(ye) == 4:
            second_param = ye[3]
            first_param = ye[0] + ye[1] + ye[2]
        elif len(ye) == 3:
            second_param = ye[2]
            first_param = ye[0] + ye[1]
        elif len(ye) == 2:
            second_param = ye[1]
            first_param = ye[0]
        elif len(ye) == 1:
            second_param = ye
            first_param = ""
        if bld.startswith("حسب"):
            bld = f"{bld}|في="

        text = f"{{{{{template}|{first_param}|{second_param}|{bld}}}}}"

        logger.info(f" {first_param=}, {second_param=}, {bld=} ")

        if not bld:
            template = f"{cacaca[tex]}سنة"
            text = f"{{{{{template}|{first_param}|{second_param}}}}}"

        logger.info(text)

        return text, template

    return "{{تصنيف موسم}}", "تصنيف موسم"


__all__ = [
    "make_years_template",
]
