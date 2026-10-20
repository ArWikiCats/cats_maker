#!/usr/bin/python3
"""
Data models for managing multi-language portal mappings and aliases.

portals_data_example = {
    "آيسلندا": {"en": "Iceland", "fr": "Islande"},
    "أبخازيا": {"en": "Abkhazia", "fr": "Abkhazie"},
    }
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from ...json_data_read_only.read_data import load_data_from_json_file
from .portal_allieas import ALIASES_DATA

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PortalEntry:
    """
    Represents a single portal item with languages and aliases.
    """

    ar: str
    en: str = ""
    fr: str = ""
    aliases: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(
        cls,
        arabic_title: str,
        data: dict[str, str],
        aliases: list[str] | None = None,
    ) -> PortalEntry:
        """Create a PortalEntry instance from raw dict data and aliases."""
        return cls(
            ar=arabic_title,
            en=data.get("en", ""),
            fr=data.get("fr", ""),
            aliases=aliases or [],
        )

    def get_lang(self, lang: str) -> str:
        """Retrieve value for a given language attribute dynamically."""
        return getattr(self, lang.lower(), "")

    @property
    def ar_lower(self) -> str:
        """Arabic title in lowercase."""
        return self.ar.lower()

    @property
    def en_lower(self) -> str:
        """English title in lowercase."""
        return self.en.lower()

    @property
    def fr_lower(self) -> str:
        """French title in lowercase."""
        return self.fr.lower()


@dataclass
class PortalCatalog:
    """Collection of portal entries providing translation lookups and aliases."""

    entries: list[PortalEntry] = field(default_factory=list)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, dict[str, str]],
        aliases_map: dict[str, list[str]] | None = None,
    ) -> PortalCatalog:
        """Construct a PortalCatalog from nested dictionaries and optional aliases map."""
        aliases_map = aliases_map or {}
        entries = [
            PortalEntry.from_dict(
                arabic_title=ar_title,
                data=trans,
                aliases=aliases_map.get(ar_title, []),
            )
            for ar_title, trans in data.items()
        ]
        return cls(entries=entries)  # pyright: ignore[reportCallIssue]

    def get_alias_mapping(self, case_insensitive: bool = True) -> dict[str, str]:
        """Generate a dictionary mapping all aliases to their main Arabic portal title."""
        alias_to_main: dict[str, str] = {}
        for entry in self.entries:
            for alias in entry.aliases:
                key = alias.lower() if case_insensitive else alias
                alias_to_main[key] = entry.ar

        return alias_to_main

    def resolve_alias(self, name: str) -> str | None:
        """
        Resolve an alias or Arabic variant to its canonical Arabic portal title.

        :param name: Portal name or alias (can use underscores or spaces).
        :return: Main Arabic title if found, otherwise None.
        """
        clean_name = name.replace("_", " ").strip()
        clean_name_lower = clean_name.lower()

        # 1. Check if it directly matches a main Arabic title
        ar_titles_lower = {entry.ar_lower: entry.ar for entry in self.entries if entry.ar}
        if clean_name_lower in ar_titles_lower:
            return ar_titles_lower[clean_name_lower]

        # 2. Check if it matches a known alias
        alias_map = self.get_alias_mapping(case_insensitive=True)
        return alias_map.get(clean_name_lower)

    def translate_portal_name(
        self,
        name: str,
        target_lang: str,
    ) -> tuple[str, str]:
        """
        Translate a portal name or alias to/from Arabic based on the target language.

        :param name: Portal name or alias to look up.
        :param target_lang: Target language code ('en' or 'fr').
        :return: Tuple of (translated_name, arabic_name).
        """
        target_lang = target_lang.lower()
        clean_name = name.replace("_", " ").strip()
        clean_name_lower = clean_name.lower()

        # Try to resolve alias or main Arabic title (can return None now)
        main_ar = self.resolve_alias(clean_name) or clean_name

        # Map lookup using case-insensitive matches
        ar_to_target_lower = self.get_mapping(from_lang="ar", to_lang=target_lang, case_insensitive=True)

        # 1. Match as Arabic title or alias (if main_ar is found)
        if main_ar:
            main_ar_lower = main_ar.lower()
            if main_ar_lower in ar_to_target_lower:
                return ar_to_target_lower[main_ar_lower], main_ar

        # 2. Match as Target language name (e.g., input was English or French name)
        target_to_ar_lower = self.get_mapping(from_lang=target_lang, to_lang="ar", case_insensitive=True)
        if clean_name_lower in target_to_ar_lower:
            main_ar = target_to_ar_lower[clean_name_lower]
            proper_target = self.get_mapping(from_lang="ar", to_lang=target_lang).get(main_ar, clean_name)
            return proper_target, main_ar

        # Fallback if no match was found anywhere
        return clean_name, main_ar

    def get_mapping(
        self,
        from_lang: str,
        to_lang: str,
        case_insensitive: bool = False,
    ) -> dict[str, str]:
        """
        Generate a translation mapping dictionary between language attributes.
        """
        from_lang = from_lang.lower()
        to_lang = to_lang.lower()
        mapping: dict[str, str] = {}

        for entry in self.entries:
            source_val = entry.get_lang(from_lang)
            target_val = entry.get_lang(to_lang)

            # Skip entries where either source or target string is empty
            if not source_val or not target_val:
                continue

            if case_insensitive:
                source_val = source_val.lower()

            mapping[source_val] = target_val

        return mapping

    # --- Direct helper methods replacing explicit dictionaries ---

    def ar_list(self, case_insensitive: bool = False) -> list[str]:
        """Get Arabic mapping."""
        if case_insensitive:
            return [entry.ar_lower for entry in self.entries if entry.ar]

        return [entry.ar for entry in self.entries if entry.ar]

    def get_ar_to_en(self, case_insensitive: bool = False) -> dict[str, str]:
        """Get Arabic to English translation mapping."""
        if case_insensitive:
            return {entry.ar_lower: entry.en for entry in self.entries if entry.ar and entry.en}
        return {entry.ar: entry.en for entry in self.entries if entry.ar and entry.en}

    def get_en_to_ar(self, case_insensitive: bool = False) -> dict[str, str]:
        """Get English to Arabic translation mapping."""
        if case_insensitive:
            return {entry.en_lower: entry.ar for entry in self.entries if entry.en and entry.ar}
        return {entry.en: entry.ar for entry in self.entries if entry.en and entry.ar}

    def get_ar_to_fr(self, case_insensitive: bool = False) -> dict[str, str]:
        """Get Arabic to French translation mapping."""
        if case_insensitive:
            return {entry.ar_lower: entry.fr for entry in self.entries if entry.ar and entry.fr}
        return {entry.ar: entry.fr for entry in self.entries if entry.ar and entry.fr}

    def get_fr_to_ar(self, case_insensitive: bool = False) -> dict[str, str]:
        """Get French to Arabic translation mapping."""
        if case_insensitive:
            return {entry.fr_lower: entry.ar for entry in self.entries if entry.fr and entry.ar}
        return {entry.fr: entry.ar for entry in self.entries if entry.fr and entry.ar}

    def resolve_portal_names(self, x, lang):
        resolved = x.replace("_", " ")

        if lang == "en":
            portals_ar_to_en = self.get_ar_to_en()
            if resolved in portals_ar_to_en:
                return portals_ar_to_en[resolved], resolved

            portals_en_to_ar = self.get_en_to_ar()
            if resolved in portals_en_to_ar:
                return resolved, portals_en_to_ar[resolved]

        if lang == "fr":
            portals_ar_to_fr = self.get_ar_to_fr()
            if resolved in portals_ar_to_fr:
                return portals_ar_to_fr[resolved], resolved

            portals_fr_to_ar = self.get_fr_to_ar()
            if resolved in portals_fr_to_ar:
                return resolved, portals_fr_to_ar[resolved]

        return resolved, x


portals_data = load_data_from_json_file("new_portal_list.json") or {}

# Build catalog with both data and aliases
PORTALS_CATALOG = PortalCatalog.from_dict(
    data=portals_data,
    aliases_map=ALIASES_DATA,
)

__all__ = [
    "PortalCatalog",
    "PORTALS_CATALOG",
]
