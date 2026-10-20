# infrastructure/sql/base.py
from __future__ import annotations

from ...new_config import C18Config

from ..wrapper import SharedWrapper


class ReplicaClient:
    """
    A client for interacting with a database replica.

    This class provides a simplified interface to execute read-only queries
    against a specific database replica using a shared wrapper.

    Core Functionality:
        - Initializes a connection context for a specific database replica.
        - Executes safe, parameterized SQL SELECT queries via the replica.

    Constructor Args:
        dbname (str): The name of the database to connect to.
            Defaults to "arwiki".
        wrapper (SharedWrapper | None): An instance of SharedWrapper used to
            manage replica connections and permissions. If None, a new
            SharedWrapper instance is created automatically. Defaults to None.

    Usage Limitations:
        - This client is strictly for read operations (SELECT). Attempting
        other SQL operations may fail or be blocked by the underlying wrapper.
        - If the shared wrapper's `can_use_sql()` method returns False, the
        `select` method will silently return an empty list instead of
        executing the query.

    Example:
        >>> client = ReplicaClient(dbname="enwiki", wrapper=SharedWrapper())
        >>> results = client.select("SELECT page_id FROM page LIMIT 1")
    """

    def __init__(
        self,
        dbname: str = "arwiki",
        wrapper: SharedWrapper | None = None,
        config: C18Config | None = None,
    ) -> None:
        self.dbname = dbname
        self.wrapper = wrapper or SharedWrapper()
        self.config = config or C18Config()

    def select(self, query: str, params: list | None = None) -> list[dict]:
        if not self.wrapper.can_use_sql() or not self.config.use_sql:
            return []

        db = self.wrapper.get_replica(self.dbname)
        return db.select_safe(query, params or [])

    @classmethod
    def load(cls, dbname: str, wrapper: SharedWrapper | None = None) -> ReplicaClient:
        return cls(dbname, wrapper=wrapper)


__all__ = [
    "ReplicaClient",
]
