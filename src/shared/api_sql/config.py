"""
Environment-driven configuration for the service package.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .exceptions import ConfigurationError


@dataclass(frozen=True)
class DatabaseConfig:
    """Immutable database configuration container."""

    host: str
    database: str
    user_file_path: Path
    connect_timeout: int = 10
    read_timeout: int = 30
    charset: str = "utf8mb4"


class ConfigLoader:
    """Loads and validates application configuration."""

    @staticmethod
    def get_db_config(wiki: str) -> DatabaseConfig:
        """
        Resolve database connection details for a specific wiki.

        Args:
            wiki: The wiki identifier (e.g., 'ar', 'enwiki').

        Returns:
            DatabaseConfig object.

        Raises:
            ConfigurationError: If environment variables are missing.
        """
        # In production, these might come from env vars or a secrets manager
        # For Wikimedia Toolforge/Cloud, we often rely on replica.my.cnf
        home = Path.home()
        cnf_path = home / "replica.my.cnf"

        if not cnf_path.exists():
            raise ConfigurationError(f"Replica config file not found at {cnf_path}")

        # Logic to determine host/db name based on wiki code
        # This mimics the original make_labsdb_dbs_p logic but keeps it clean
        normalized_wiki = wiki.removesuffix("wiki").replace("-", "_")

        # Aliases (could be moved to a separate constant file if large)
        aliases = {
            "wikidata": "wikidatawiki",
            "be-x-old": "be_x_old",
            "be_tarask": "be_x_old",
            "be-tarask": "be_x_old",
        }
        normalized_wiki = aliases.get(normalized_wiki, normalized_wiki)

        if "wiki" not in normalized_wiki and not normalized_wiki.endswith("wiktionary"):
            normalized_wiki = f"{normalized_wiki}wiki"

        host = f"{normalized_wiki}.analytics.db.svc.wikimedia.cloud"
        db_name = f"{normalized_wiki}_p"

        return DatabaseConfig(host=host, database=db_name, user_file_path=cnf_path)

    @staticmethod
    def is_production() -> bool:
        """Check if the application is running in production mode."""
        return os.getenv("APP_ENV", "").lower() == "production"
