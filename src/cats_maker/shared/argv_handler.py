"""
Shared sys.argv parser for src/arwikibot/shared.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# dataclass
# ---------------------------------------------------------------------------


@dataclass
class SharedArgv:
    """
    parsed ``sys.argv`` options for ``src/arwikibot/shared``.
    """

    # ----- gent.py (covers both arwiki and wikidata via lang/family) -----
    usernewpages: str | None = None
    mynewpages: bool = False
    mynewpages_limit: int | None = None
    limit: int | None = None
    ns: str | None = None
    newpages2: str | None = None

    # ----- newapi/config.py -----
    bot_ask: bool = False
    bot_no_diff: bool = False
    bot_show_diff: bool = False
    bot_no_false_edit: bool = False
    bot_workibrahem: bool = False
    bot_force_edit: bool = False

    # ----- likeapi/commons.py -----
    auto_save: bool = False

    # ----- likeapi/countries_data.py -----
    file: str | None = None

    # ----- unknown / leftover -----
    unknown: dict[str, list[str]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# parser
# ---------------------------------------------------------------------------


def _norm(arg: str) -> tuple[str, str]:
    """strip leading "-" and split on the first ":".

    Mirrors the original ``arg.removeprefix("-").partition(":")`` idiom.
    """

    key, _, value = arg.removeprefix("-").partition(":")
    return key, value


def parse_argv(argv: list[str] | None = None) -> SharedArgv:
    """Parse the package-wide ``sys.argv`` into a :class:`SharedArgv`.

    Parameters
    ----------
    argv:
        optional explicit argv list. Defaults to ``sys.argv``.

    Notes
    -----
    The special ``-always`` / ``-save`` flags from ``likeapi/commons.py`` are
    matched against the *initial* raw argument (before ``partition``), so
    both spellings (``always`` and ``-always``) reduce to the same key via
    the leading-dash strip and trigger ``auto_save = True``.

    ``gent.py`` is the single consumer of this parser (it now serves both
    arwiki and wikidata via its ``lang``/``family`` parameters):
    they each only use ``usernewpages`` / ``mynewpages`` / ``limit`` / ``ns``
    in ``getusernewpages()`` and ``newpages2`` in ``get_gent_list()``.
    """

    if argv is None:
        argv = sys.argv

    out = SharedArgv()

    for raw in argv:
        key, value = _norm(raw)

        if not key:
            continue

        # ----- gent.py : getusernewpages -----
        if key == "usernewpages":
            out.usernewpages = value
            continue
        if key == "mynewpages":
            out.mynewpages = True
            # original: usernewpages = "Mr. Ibrahem"; if value: limit = int(value)
            if value:
                try:
                    out.mynewpages_limit = int(value)
                except (TypeError, ValueError):
                    pass
            continue
        if key == "limit":
            try:
                out.limit = int(value)
            except (TypeError, ValueError):
                pass
            continue
        if key == "ns":
            out.ns = value
            continue

        # ----- gent.py : get_gent_list -----
        if key == "newpages2":
            out.newpages2 = value
            continue

        # ----- newapi/config.py : Settings._process_argv -----
        if key == "ask":
            out.bot_ask = True
            continue
        if key == "nodiff":
            out.bot_no_diff = True
            continue
        if key == "diff":
            out.bot_show_diff = True
            continue
        if key == "nofa":
            out.bot_no_false_edit = True
            continue
        if key == "workibrahem":
            out.bot_workibrahem = True
            continue
        if key in ("botedit", "editbot"):
            out.bot_force_edit = True
            continue

        # ----- likeapi/commons.py -----
        if key in ("always", "save"):
            out.auto_save = True
            continue

        # ----- likeapi/countries_data.py -----
        if key == "file":
            out.file = value
            continue

        # ----- leftover -----
        out.unknown.setdefault(key, []).append(value)

    return out


shared_options = parse_argv()

__all__ = ["shared_options"]
