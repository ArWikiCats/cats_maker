""" """

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Content:
    # text: str = ""
    # newtext: str = ""
    text_html: str = ""
    summary: str = ""
    words: int = 0
    length: int = 0


@dataclass
class Meta:
    is_disambig: bool = False
    can_be_edit: None | bool = None
    # ns: int = 0
    userinfo: dict = field(default_factory=dict)
    create_data: dict = field(default_factory=dict)
    info: dict[str, Any] = field(default_factory=lambda: {"done": False})
    username: str = ""
    Exists: bool = False
    is_redirect: bool = False
    flagged: bool = False
    wikibase_item: str = ""

    def log_create_data(self, page_data) -> None:
        """
        _revisions_example = [
            {
                "revid": 76529179,
                "parentid": 0,
                "minor": False,
                "user": "~2026-49145-25",
                "temp": True,
                "userid": 3029517,
                "timestamp": "2026-09-11T23:05:07Z",
            }
        ]
        """
        self.create_data = {
            "timestamp": page_data["timestamp"],
            "user": page_data.get("user", ""),
            "anon": page_data.get("anon"),
            "temp": page_data.get("temp"),
        }


@dataclass
class RevisionsData:
    revid: str = ""
    newrevid: str = ""
    pageid: str = ""
    timestamp: str = ""
    revisions: list = field(default_factory=list)
    touched: str = ""

    def update_from_edit(self, edit: dict[str, Any]) -> None:
        if edit.get("pageid"):
            self.pageid = edit["pageid"]

        if edit.get("newrevid"):
            self.revid = edit["newrevid"]
            self.newrevid = edit["newrevid"]

        if edit.get("newtimestamp"):
            self.timestamp = edit["newtimestamp"]

        if edit.get("touched"):
            self.timestamp = edit["touched"]


@dataclass
class LinksData:
    back_links: list = field(default_factory=list)
    extlinks: list = field(default_factory=list)
    iwlinks: list = field(default_factory=list)
    links_here: list = field(default_factory=list)
    links: list = field(default_factory=list)
    links2: list = field(default_factory=list)


@dataclass
class CategoriesData:
    categories: dict = field(default_factory=dict)
    hidden_categories: dict = field(default_factory=dict)
    all_categories_with_hidden: dict = field(default_factory=dict)


@dataclass
class TemplateData:
    templates: list = field(default_factory=list)
    templates_api: list = field(default_factory=list)


__all__ = [
    "Content",
    "Meta",
    "RevisionsData",
    "LinksData",
    "CategoriesData",
    "TemplateData",
]
