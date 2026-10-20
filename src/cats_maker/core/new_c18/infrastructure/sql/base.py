# infrastructure/sql/base.py
from __future__ import annotations

from ..wrapper import SharedWrapper


class ReplicaClient:
    def __init__(self, dbname: str = "arwiki", wrapper: SharedWrapper | None = None):
        self.dbname = dbname
        self.wrapper = wrapper or SharedWrapper()

    def select(self, query: str, params: list | None = None) -> list[dict]:
        if not self.wrapper.can_use_sql():
            return []

        db = self.wrapper.get_replica(self.dbname)
        return db.select_safe(query, params or [])


__all__ = [
    "ReplicaClient",
]
