"""
Low-level MySQL connection and query helpers.

Design decisions
----------------
* ``MysqlConnectionPool`` is a **thread-safe Singleton** that keeps one
  ``pymysql.Connection`` per (host, db) pair and re-establishes it on demand.
  Use it as a context manager to get a cursor with automatic cleanup:

      with MysqlConnectionPool.instance().cursor(host, db) as cur:
          cur.execute(query, params)
          rows = cur.fetchall()

* ``execute_query`` is the preferred one-shot helper: it handles the full
  acquire → execute → fetch → release cycle and returns decoded rows.

* All queries **must** supply parameters via the *values* argument; string
  interpolation into the query text is intentionally unsupported to prevent
  SQL injection.

* Byte values in returned rows are transparently decoded to ``str``.
"""

from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from typing import Any, Generator, Sequence

import pymysql
from pymysql.cursors import DictCursor

from .config import DB_CHARSET, DB_CONNECT_TIMEOUT, DB_READ_TIMEOUT, REPLICA_CNF_PATH
from .exceptions import (
    DatabaseConnectionError,
    DatabaseError,
    DatabaseFetchError,
    QueryExecutionError,
)

logger = logging.getLogger(__name__)

# Type alias for a list of row dicts returned by DictCursor.
Rows = list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Connection pool (Singleton)
# ---------------------------------------------------------------------------


class MysqlConnectionPool:
    """Thread-safe Singleton that caches one connection per (host, db) pair.

    Connections are opened lazily and replaced when they become stale.
    """

    _instance: MysqlConnectionPool | None = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        # _pool maps (host, db) → open pymysql.Connection
        self._pool: dict[tuple[str, str], pymysql.Connection] = {}  # type: ignore[type-arg]
        self._pool_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Singleton access
    # ------------------------------------------------------------------

    @classmethod
    def instance(cls) -> MysqlConnectionPool:
        """Return the process-wide singleton, creating it if necessary."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_config(self, host: str, db: str) -> dict[str, Any]:
        """Return a pymysql ``connect`` keyword-argument dict.

        Credentials come exclusively from the ``replica.my.cnf`` file whose
        path is set by the ``REPLICA_CNF_PATH`` environment variable — no
        passwords are ever hard-coded.
        """
        return {
            "host": host,
            "database": db,
            "read_default_file": str(REPLICA_CNF_PATH),
            "charset": DB_CHARSET,
            "use_unicode": True,
            "autocommit": True,
            "cursorclass": DictCursor,
            "connect_timeout": DB_CONNECT_TIMEOUT,
            "read_timeout": DB_READ_TIMEOUT,
        }

    def _open_connection(self, host: str, db: str) -> pymysql.Connection:  # type: ignore[type-arg]
        """Open and return a new connection, raising ``DatabaseConnectionError`` on failure."""
        config = self._build_config(host, db)
        try:
            conn = pymysql.connect(**config)
            logger.debug("Opened new connection: host=%s db=%s", host, db)
            return conn
        except pymysql.Error as exc:
            logger.error("Connection failed: host=%s db=%s error=%s", host, db, exc)
            raise DatabaseConnectionError(f"Cannot connect to {host}/{db}", original_exception=exc) from exc

    def _get_or_create(self, host: str, db: str) -> pymysql.Connection:  # type: ignore[type-arg]
        """Return a cached connection, reopening it if it is no longer alive."""
        key = (host, db)
        with self._pool_lock:
            conn = self._pool.get(key)
            if conn is not None:
                try:
                    conn.ping(reconnect=False)
                    return conn
                except pymysql.Error:
                    logger.info("Stale connection detected; reconnecting: host=%s db=%s", host, db)
                    try:
                        conn.close()
                    except Exception:  # noqa: BLE001
                        pass
            conn = self._open_connection(host, db)
            self._pool[key] = conn
            return conn

    # ------------------------------------------------------------------
    # Public context manager
    # ------------------------------------------------------------------

    @contextmanager
    def cursor(self, host: str, db: str) -> Generator[DictCursor, None, None]:
        """Yield a ``DictCursor`` for *host*/*db*, closing it on exit.

        Example::

            with MysqlConnectionPool.instance().cursor(host, db) as cur:
                cur.execute("SELECT 1")
                rows = cur.fetchall()
        """
        conn = self._get_or_create(host, db)
        cur: DictCursor = conn.cursor()
        try:
            yield cur
        finally:
            cur.close()

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    def close_all(self) -> None:
        """Close every cached connection.  Call on application teardown."""
        with self._pool_lock:
            for key, conn in list(self._pool.items()):
                try:
                    conn.close()
                    logger.debug("Closed connection: host=%s db=%s", *key)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Error closing connection %s: %s", key, exc)
            self._pool.clear()


# ---------------------------------------------------------------------------
# Query execution
# ---------------------------------------------------------------------------


def _is_select(query: str) -> bool:
    """Return ``True`` when *query* begins with SELECT (case-insensitive)."""
    return query.lstrip().upper().startswith("SELECT")


def execute_query(
    query: str,
    *,
    host: str,
    db: str,
    values: Sequence[Any] | None = None,
) -> Rows:
    """Run *query* against *host*/*db* and return decoded rows.

    Parameters
    ----------
    query:
        A SQL statement.  **Never** interpolate values directly into this
        string; pass them via *values* instead.
    host:
        Database host name.
    db:
        Database name (including the ``_p`` suffix if required).
    values:
        Positional parameters bound to ``%s`` placeholders in *query*.
        Pass ``None`` or omit for parameter-less queries.

    Returns
    -------
    list[dict]
        Decoded rows for SELECT statements; an empty list for DML.

    Raises
    ------
    DatabaseConnectionError
        If the connection cannot be established.
    QueryExecutionError
        If ``cursor.execute`` raises.
    DatabaseFetchError
        If ``cursor.fetchall`` raises.
    """
    if not query or not query.strip():
        logger.debug("execute_query called with an empty query — skipping")
        return []

    params = tuple(values) if values else None

    pool = MysqlConnectionPool.instance()
    with pool.cursor(host, db) as cur:
        try:
            cur.execute(query, params)
        except pymysql.Error as exc:
            logger.error("Query execution failed: host=%s db=%s error=%s", host, db, exc)
            raise QueryExecutionError("Query failed", original_exception=exc) from exc

        if not _is_select(query):
            return []

        try:
            rows: Rows = cur.fetchall()
        except pymysql.Error as exc:
            logger.error("Fetch failed: host=%s db=%s error=%s", host, db, exc)
            raise DatabaseFetchError("Could not fetch results", original_exception=exc) from exc

    return decode_bytes(rows)


# ---------------------------------------------------------------------------
# Byte-decoding helpers
# ---------------------------------------------------------------------------


def _decode_value(value: bytes) -> str:
    try:
        return value.decode("utf-8")
    except Exception:  # noqa: BLE001
        return str(value)


def decode_bytes(rows: Rows) -> Rows:
    """Decode any ``bytes`` values in *rows* to ``str`` in place."""
    return [{k: (_decode_value(v) if isinstance(v, bytes) else v) for k, v in row.items()} for row in rows]


# ---------------------------------------------------------------------------
# Silent wrapper (business-layer helper)
# ---------------------------------------------------------------------------


def execute_query_silent(
    query: str,
    *,
    host: str,
    db: str,
    values: Sequence[Any] | None = None,
) -> Rows:
    """Like ``execute_query`` but returns ``[]`` instead of raising.

    All ``DatabaseError`` subclasses are caught and logged at ERROR level.
    Use this when a failed query should degrade gracefully rather than
    propagate an exception.
    """
    try:
        return execute_query(query, host=host, db=db, values=values)
    except DatabaseError as exc:
        logger.error("Suppressed database error: %s", exc)
        return []


__all__ = [
    "MysqlConnectionPool",
    "Rows",
    "decode_bytes",
    "execute_query",
    "execute_query_silent",
]
