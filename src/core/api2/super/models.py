""" """

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Content:
    text_html: str = ""
    summary: str = ""
    words: int = 0
    length: int = 0


@dataclass
class Meta:
    info_loaded: bool = False
    is_Disambig: bool = False
    can_be_edit: bool = False
    userinfo: dict = field(default_factory=dict)
    create_data: dict = field(default_factory=dict)
    username: str = ""
    Exists: str = ""
    is_redirect: str = ""
    flagged: str = ""
    wikibase_item: str = ""


@dataclass
class RevisionsData:
    revid: str = ""
    newrevid: str = ""
    pageid: str = ""
    timestamp: str = ""
    revisions: list = field(default_factory=list)
    touched: str = ""


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
    templates: dict = field(default_factory=dict)
    templates_API: list = field(default_factory=list)


__all__ = [
    "Content",
    "Meta",
    "RevisionsData",
    "LinksData",
    "CategoriesData",
    "TemplateData",
]