""" """

from __future__ import annotations


def expend_newline(template, min_len: int = 1, skip_args: list | None = None):
    if not template:
        return template
    if skip_args is None:
        skip_args = []
    """
    Expands newlines in the given template.
    """

    template_name = str(template.normal_name()).strip()
    template.name = f"{template_name}\n"

    to_del: list[str] = []

    template.rm_dup_args_safe()

    for arg in template.arguments:
        value = arg.value.rstrip()

        if len(arg.name.strip()) <= min_len:
            continue

        if arg.name.strip() in skip_args:
            continue

        arg.value = f"{value}\n"

    for aa in to_del:
        template.del_arg(aa)

    return template


__all__ = [
    "expend_newline",
]
