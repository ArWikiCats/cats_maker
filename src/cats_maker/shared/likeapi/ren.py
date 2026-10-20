#!/usr/bin/python3
"""

تغيير وسائط قالب


"""

from __future__ import annotations

import logging

import wikitextparser as wtp

from ..to_load.rename_temps import rename_temps_loader
from ..to_load.temps_params import template_params_loader
from .ref_temp import ref_temps
from .renlist import all_cite_refs_params

logger = logging.getLogger(__name__)

templates_params = template_params_loader()
rename_templates = rename_temps_loader()

skip_changes = [
    "harvnb",
    "tls",
    "tl",
    "tlx",
    "tla",
    "قالب:tls",
    "قالب:tl",
]

params_to_del = {
    "صندوق معلومات شخص": [
        "الشريك",
        "شريك",
        "known_for",
    ]
}

for te in templates_params:
    te2 = te.lower().strip()

    is_cite_temp = te in ref_temps or te2 in ref_temps

    if not is_cite_temp:
        continue

    for pa, val in templates_params[te].items():
        # if pa.strip() not in all_cite_refs_params: all_cite_refs_params[pa.strip()] = val

        all_cite_refs_params.setdefault(pa.strip(), val)


def change_text_with_white_space(old, new):

    if old == old.strip() or old.find(old.strip()) == -1:
        return new

    return old.replace(old.strip(), new.strip())


def change_params(text: str, newline: bool = False):

    parsed = wtp.parse(text)

    new_text = text

    for template in parsed.templates:
        if not template:
            continue

        name = str(template.normal_name()).strip()
        name_lower = name.lower()

        tmp_new_params = templates_params.get(name) or templates_params.get(name_lower) or {}

        if not tmp_new_params and name in ref_temps or name_lower in ref_temps:
            # قوالب الاستشهادات
            tmp_new_params = all_cite_refs_params

        n_temp_name = rename_templates.get(name) or rename_templates.get(name_lower) or name

        # تغيير اسم القالب
        if n_temp_name != name and name_lower not in skip_changes:
            logger.info(f"<<yellow>> template ({name}) is changed to ({n_temp_name})")
            try:
                template.name = change_text_with_white_space(str(template.name), n_temp_name)
            except Exception as e:
                logger.info(e)

        if not tmp_new_params:
            tmp_new_params = templates_params.get(n_temp_name) or templates_params.get(n_temp_name.lower()) or {}

        to_del: list[str] = params_to_del.get(name_lower) or params_to_del.get(n_temp_name.lower()) or []

        try:
            # تغيير الوسائط
            if tmp_new_params or to_del:
                # old = template.string

                for arg in template.arguments:
                    param_name = str(arg.name)

                    if param_name.strip() in to_del:
                        template.del_arg(param_name)
                        continue

                    if param_name.strip() in tmp_new_params:
                        new_arg = tmp_new_params[param_name.strip()]

                        # to keep whitespace
                        # arg.name = param_name.replace(param_name.strip(), new_arg)
                        try:
                            arg.name = change_text_with_white_space(param_name, new_arg)
                        except Exception as e:
                            logger.info(e)

                    if newline:
                        try:
                            arg.value = f"{arg.value}\n"
                        except Exception as e:
                            logger.info(e)

                # new = template.string

                # print_s(f'new = {new}')

                # new_text = new_text.replace(old, new)

        except Exception as e:
            logger.info(e)

    new_text = parsed.string

    return new_text


__all__ = [
    "change_text_with_white_space",
    "change_params",
]
