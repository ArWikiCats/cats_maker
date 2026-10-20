"""
en mapping:
https://en.wikipedia.org/w/api.php?action=query&meta=siteinfo&siprop=namespaces|namespacealiases&formatversion=2

ar mapping:
https://ar.wikipedia.org/w/api.php?action=query&meta=siteinfo&siprop=namespaces|namespacealiases&formatversion=2
"""

from __future__ import annotations

from .mapping import Namespace, TitleInfo
from .ns_list import AR_NAMESPACES_DATA, EN_NAMESPACES_DATA


class NamespaceHandler:
    """Handles Wikipedia page titles and namespaces (main <-> talk conversions)."""

    def __init__(self, lang_code: str, namespaces: list[Namespace]) -> None:
        self.lang_code = lang_code
        self.namespaces: dict[int, Namespace] = {x.id: x for x in namespaces}

        self.default_talk_namespace: str = ""

        # Map every prefix (canonical name AND aliases) to its NS ID
        self.prefix_to_ns: dict[str, int] = {}
        for ns_obj in self.namespaces.values():
            # Default talk namespace is 1
            if ns_obj.id == 1:
                self.default_talk_namespace = ns_obj.name

            # name
            if ns_obj.name:
                self.prefix_to_ns[ns_obj.name] = ns_obj.id

            # canonical_name
            if ns_obj.canonical_name:
                self.prefix_to_ns[ns_obj.canonical_name] = ns_obj.id

            # aliases
            for alias in ns_obj.aliases:
                if alias:
                    self.prefix_to_ns[alias] = ns_obj.id

        # Sort prefixes longest-first to avoid partial matching conflicts
        self._sorted_prefixes: list[tuple[str, int]] = sorted(
            self.prefix_to_ns.items(), key=lambda kv: len(kv[0]), reverse=True
        )

        # Precompute talk <-> main namespace ID mappings
        self.main_to_talk_ns: dict[int, int] = {}
        self.talk_to_main_ns: dict[int, int] = {}

        # Odd namespace IDs are talk pages in standard MediaWiki setup
        for ns_obj in self.namespaces.values():
            if ns_obj.is_talk_namespace():
                main_ns = ns_obj.id - 1
                if main_ns in self.namespaces:
                    self.main_to_talk_ns[main_ns] = ns_obj.id
                    self.talk_to_main_ns[ns_obj.id] = main_ns

    def is_talk_namespace(self, namespace: int) -> bool:
        return namespace >= 0 and namespace % 2 == 1

    def _strip_ns_prefix(self, title: str) -> tuple[str, int | None]:
        """
        Extract existing namespace prefix from a title if present.

        Rules applied:
        1) Replace '_' with a space before any processing.
        2) If the title contains no ':', no namespace is detected => return None (no scan against the list; the final
        decision is left to the caller via default_ns/ns).
        3) If it contains ':', check the prefix (before ':') against every AR_NAMESPACES entry (longest first, to avoid
        confusing "نقاش" with "نقاش التصنيف", for example).
        4) If no prefix matches at the ':', scan all AR_NAMESPACES (non-empty text) and check whether the full title starts
        with one of their texts **immediately followed by ':' (after stripping any whitespace in between)**. This prevents
        false matches such as "talksomething" against the "talk" namespace when there is no actual ':' right after the
        namespace word.
        5) If we reach the end with no match at all despite a ':' being present, assume 0 (main) explicitly, since a ':'
        with an unrecognized prefix most likely means a main-namespace title that happens to contain ':' as part of its
        text (e.g. "فيلم: الجزء الثاني").

        Returns:
            (clean_title_without_prefix, ns_id | None)
            None means: "no namespace was detected from the title text itself" — the caller should then use the
            ns/default_ns passed to it.
        """
        clean_title = title.replace("_", " ").strip()

        # Rule 2: no ':' => no namespace detected from the text itself
        if ":" not in clean_title:
            return clean_title, None

        prefix, rest = clean_title.split(":", 1)
        prefix = prefix.strip()

        # Rule 3: standard match of the prefix before ':'
        if prefix in self.prefix_to_ns:
            return rest.strip(), self.prefix_to_ns[prefix]

        # Rule 4: scan all namespaces and check startswith + ':' immediately after
        for ns_text, ns_id in self._sorted_prefixes:
            if clean_title.startswith(ns_text):
                remainder = clean_title[len(ns_text) :].lstrip()
                if remainder.startswith(":"):
                    return remainder[1:].strip(), ns_id

        # Rule 5: ':' is present but nothing matched at all => assume 0 explicitly
        return clean_title, 0

    def get_full_title(self, title: str, ns: int | str) -> str:
        """
        1. Takes a title and ns, returns the formatted full title with prefix.
        """
        ns_id = int(ns)
        base_title, detected_ns = self._strip_ns_prefix(title)

        # Use explicitly passed ns if provided, otherwise fallback to detected ns
        target_ns = ns_id if ns_id in self.namespaces else (detected_ns or 0)
        ns_obj = self.namespaces.get(target_ns)
        prefix = ns_obj.name if ns_obj else ""

        if str(target_ns) == "0" or not prefix:
            return base_title
        return f"{prefix}:{base_title}"

    def get_talk_title(self, title: str, ns: int | str = 0) -> str:
        """
        2. Takes a main/subject title and returns its talk page title.
        """
        ns_id = int(ns)
        base_title, detected_ns = self._strip_ns_prefix(title)

        current_ns = detected_ns if detected_ns is not None else ns_id

        # If it is already a talk page, return as full title
        if current_ns in self.talk_to_main_ns:
            return self.get_full_title(base_title, current_ns)

        # Retrieve mapped talk namespace ID
        talk_ns = self.main_to_talk_ns.get(current_ns)
        if talk_ns is None:
            # Fallback for unmapped main namespaces
            talk_ns = 1

        ns_obj = self.namespaces.get(talk_ns)
        prefix = ns_obj.name if ns_obj else self.default_talk_namespace

        return f"{prefix}:{base_title}"

    def get_main_title(self, title: str, ns: int | str = 1) -> str:
        """
        3. Takes a talk title and returns its main/subject page title.
        """
        ns_id = int(ns)
        base_title, detected_ns = self._strip_ns_prefix(title)

        current_ns = detected_ns if detected_ns is not None else ns_id

        main_ns = self.talk_to_main_ns.get(current_ns, 0)
        ns_obj = self.namespaces.get(main_ns)
        prefix = ns_obj.name if ns_obj else ""

        if str(main_ns) == "0" or not prefix:
            return base_title
        return f"{prefix}:{base_title}"

    def analyze_title(self, title: str, default_ns: int = 0) -> TitleInfo:
        """
        4. Analyzes a title string to determine its cleaned title, namespace ID, and talk status.
        """
        base_title, detected_ns = self._strip_ns_prefix(title)
        resolved_ns = detected_ns if detected_ns is not None else default_ns

        is_talk = self.is_talk_namespace(resolved_ns) if resolved_ns != 0 else False

        return TitleInfo(title=base_title, ns=resolved_ns, is_talk=is_talk)


ar_ns_handler = NamespaceHandler("ar", AR_NAMESPACES_DATA)
en_ns_handler = NamespaceHandler("en", EN_NAMESPACES_DATA)

__all__ = [
    "NamespaceHandler",
    "ar_ns_handler",
    "en_ns_handler",
]
