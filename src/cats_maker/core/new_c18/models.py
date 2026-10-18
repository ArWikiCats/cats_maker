#!/usr/bin/python3
"""Lightweight dataclasses for the module."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CategoryRef:
    """Reference to a category on a specific wiki."""

    title: str  # normalized, no prefix
    lang: str  # "ar", "en", "fr"


@dataclass
class PageRef:
    """Reference to a wiki page with langlinks."""

    title: str
    namespace: int
    langlinks: dict[str, str]


@dataclass
class WikiPage:
    """Wiki page representation."""

    title: str
    namespace: int
    langlinks: dict[str, str] = field(default_factory=dict)


@dataclass
class Category:
    """Category with associated templates."""

    title: str
    templates: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of category validation."""

    valid: bool
    reason: str | None = None
