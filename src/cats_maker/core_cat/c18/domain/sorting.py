"""Arabic category sorting"""

from __future__ import annotations

import re

from ....config.constants import ARABIC_ALPHABET

_ARABIC_COLLATION = str.maketrans({ch: f"{i:02d}" for i, ch in enumerate(ARABIC_ALPHABET)})


class CategorySorter:
    """Handles Arabic category sorting."""

    def sort_list(self, categorylist: list[str]) -> list[str]:
        """Sort a list of raw category link strings."""
        coded: list = []
        for cat in categorylist:
            clean = cat.replace("[[تصنيف:", "").replace("]]", "")
            key = self.translate_charts(clean)
            coded.append((key, clean))

        coded = sorted(set(coded))
        return [f"[[تصنيف:{item}]]" for _, item in coded]

    def translate_charts(self, clean):
        key = clean.translate(_ARABIC_COLLATION)
        return key

    def sort_in_text(self, text: str, title: str) -> str:
        """Sort all categories inside the page text."""
        pattern = re.compile(r"(\[\[تصنيف\:(?:.+?)\]\])")
        cats = pattern.findall(text)

        if not cats:
            return text

        # Remove old categories
        new_text = text
        for cat in cats:
            new_text = new_text.replace(cat, "")

        # Sort
        sorted_cats = self.sort_list(cats)

        # Keep main category (same as title) at the top if exists
        for cat in sorted_cats[1:]:
            if re.search(r"\[\[(.+?)\|[ \*]\]\]", cat) or cat.startswith(f"[[تصنيف:{title}"):
                sorted_cats.remove(cat)
                sorted_cats.insert(0, cat)

        if sorted_cats == cats:
            return text

            # Append sorted categories
        for cat in sorted_cats:
            new_text += f"\n{cat}"

        new_text = re.sub(r"\n{3,}", "\n\n", new_text)
        return new_text.strip()


__all__ = [
    "CategorySorter",
]
