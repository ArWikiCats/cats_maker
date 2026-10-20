""" """

from __future__ import annotations

from dataclasses import dataclass, field
from typing import NamedTuple


class TitleInfo(NamedTuple):
    title: str
    ns: int
    is_talk: bool


@dataclass(frozen=True)
class Namespace:
    """
    "4": { "id": 4, "case": "first-letter", "name": "ويكيبيديا", "subpages": true, "canonical": "Project", "content": false, "nonincludable": false }
    """

    id: int
    name: str
    canonical_name: str = ""
    aliases: list[str] = field(default_factory=list)
    has_talk_ns: bool | None = None

    def is_talk_namespace(self) -> bool:
        return self.id >= 0 and self.id % 2 == 1

    @classmethod
    def load(
        cls,
        id: int,
        name: str,
        canonical_name: str,
        aliases: list[str] | None = None,
    ) -> Namespace:
        return cls(
            id=id,
            name=name,
            canonical_name=canonical_name,
            aliases=aliases or [],
        )


__all__ = [
    "Namespace",
    "TitleInfo",
]
