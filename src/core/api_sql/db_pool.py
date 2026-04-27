"""Database connection pool and context manager."""

import logging
import threading
from contextlib import contextmanager
from typing import Generator

import pymysql
from pymysql.cursors import DictCursor

from .config import ConfigLoader, DatabaseConfig
from .exceptions import DatabaseConnectionError, DatabaseFetchError, QueryExecutionError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Thread-safe Singleton Database Manager.

    Manages connections using a context manager pattern to ensure
    connections are always closed, even if errors occur.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._config_loader = ConfigLoader()
        self._initialized = True
        logger.info("DatabaseManager initialized.")

    @contextmanager
    def get_connection(self, wiki: str) -> Generator[pymysql.connections.Connection, None, None]:
        """
        Provide a database connection within a context manager.

        Args:
            wiki: The wiki identifier (e.g., 'ar', 'enwiki').

        Yields:
            A pymysql connection object.

        Raises:
            DatabaseConnectionError: If connection fails.
        """
        if not self._config_loader.is_production():
            logger.warning("Attempted to get DB connection in non-production environment.")
            raise DatabaseConnectionError("Database access disabled in non-production environment.")

        config = self._config_loader.get_db_config(wiki)
        conn = None

        try:
            logger.debug("Connecting to %s/%s", config.host, config.database)
            conn = pymysql.connect(
                host=config.host,
                database=config.database,
                read_default_file=str(config.user_file_path),
                charset=config.charset,
                use_unicode=True,
                autocommit=True,
                cursorclass=DictCursor,
                connect_timeout=config.connect_timeout,
                read_timeout=config.read_timeout,
            )
            yield conn
        except pymysql.MySQLError as e:
            logger.error("Database connection error for %s: %s", wiki, e)
            raise DatabaseConnectionError(f"Failed to connect to {wiki}", e)
        finally:
            if conn and conn.open:
                conn.close()
                logger.debug("Connection to %s closed.", wiki)

    def execute_query(self, wiki: str, query: str, params: tuple | list | None = None) -> list[dict]:
        """
        Execute a SELECT query and return results.

        Args:
            wiki: The wiki identifier.
            query: The SQL query string (parameterized).
            params: Parameters for the query.

        Returns:
            List of dictionaries representing rows.
        """
        if not query.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed via execute_query.")

        with self.get_connection(wiki) as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    results = cursor.fetchall()

                    # Decode bytes to strings if necessary
                    return [
                        {k: (v.decode("utf-8") if isinstance(v, bytes) else v) for k, v in row.items()}
                        for row in results
                    ]
            except pymysql.MySQLError as e:
                logger.error("Query execution failed on %s: %s", wiki, e)
                raise QueryExecutionError(f"Query failed on {wiki}", e)


# Global accessor for ease of use, maintaining Singleton behavior
db_manager = DatabaseManager()
