from __future__ import annotations

import logging

from ...config import Settings
from .maps import WikiReplicaMaps
from .replica_db import WikiReplicaBaseDB

logger = logging.getLogger(__name__)


class WikiReplicaDB(WikiReplicaBaseDB):
    """
    Toolforge-specific subclass that handles wiki shard resolution and credential loading.
    """

    def __init__(
        self,
        wiki_identifier: str,
        settings: Settings | None = None,
        maps: WikiReplicaMaps | None = None,
        safe_load: bool = False,
    ) -> None:
        self.settings = settings or Settings.get_instance()
        self.maps = maps or WikiReplicaMaps.get_instance()
        # self.maps = WikiReplicaMaps(
        #     WikiReplicaBaseDB(
        #         dbname="meta_p",
        #         host="s7.analytics.db.svc.wikimedia.cloud",
        #     )
        # )

        # wiki_identifier can be "arwiki", "enwiki", "ar", etc.
        info = self.maps.resolve_wiki(wiki_identifier)
        if not info:
            logger.error("Unknown wiki: %s", wiki_identifier)
            if not safe_load:
                raise ValueError(f"Unknown wiki: {wiki_identifier}")
            return

        dbname = info["dbname"]
        slice_name = info.get("slice", "s1")  # Default to s1 if not found, but it should be there
        host = f"{slice_name}.analytics.db.svc.wikimedia.cloud"

        logger.info("Resolved wiki '%s' -> dbname='%s', host='%s'", wiki_identifier, dbname, host)

        super().__init__(
            dbname=f"{dbname}_p",
            host=host,
            user=self.settings.analytics_database.user,
            password=self.settings.analytics_database.password,
        )

    @staticmethod
    def can_use_sql() -> bool:
        settings = Settings.get_instance()
        return settings.analytics_database.use_sql and settings.analytics_database.can_use_sql()

    @classmethod
    def load(cls, wiki_identifier: str) -> WikiReplicaDB:
        return cls(wiki_identifier=wiki_identifier)


__all__ = [
    "WikiReplicaDB",
]
