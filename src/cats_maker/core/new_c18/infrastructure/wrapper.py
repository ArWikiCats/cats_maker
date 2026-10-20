# infrastructure/shared/wrapper.py
from __future__ import annotations

from typing import Any

from ....database import WikiReplicaDB, get_sql
from ....shared.newapi import MainPage
from ....shared.newapi.client_wiki.all_apis import AllAPIS
from ..new_config import C18Config


class SharedWrapper:
    """Central access point to external shared libraries."""

    def __init__(
        self,
        config: C18Config | None = None,
    ) -> None:
        self.config = config or C18Config()

    def client_request_safe_main_api(
        self,
        params: dict[str, Any],
        code: str,
        family: str = "wikipedia",
    ) -> dict[str, Any]:
        api = AllAPIS.load(code, family)
        data = api.client_request_safe(params) or {}
        return data

    def get_sql(self) -> bool:
        return get_sql()

    def get_replica(self, dbname: str) -> WikiReplicaDB:
        return WikiReplicaDB.load(dbname)


# Convenience singleton (optional)
shared_wrapper = SharedWrapper()


__all__ = [
    "SharedWrapper",
    "shared_wrapper",
    "MainPage",
]
