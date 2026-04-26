"""Low-level MySQL connection and query helpers."""

import functools
import logging
from pathlib import Path
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

from .constants import REPLICA_CNF_FILENAME
from .exceptions import (
    DatabaseConnectionError,
    DatabaseError,
    DatabaseFetchError,
    QueryExecutionError,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Connection config
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=None)
def _build_db_config(host: str, db: str) -> dict[str, Any]:
    """Build a pymysql connection config dict (cached per host+db pair)."""
    return {
        "host": host,
        "database": db,
        "read_default_file": str(Path.home() / REPLICA_CNF_FILENAME),
        "charset": "utf8mb4",
        "use_unicode": True,
        "autocommit": True,
        "cursorclass": DictCursor,
        "connect_timeout": 10,
        "read_timeout": 30,
    }


# ---------------------------------------------------------------------------
# Query execution
# ---------------------------------------------------------------------------


def _is_select_query(query: str) -> bool:
    """Return True if *query* appears to be a SELECT statement."""
    return query.lstrip().upper().startswith("SELECT")


def _run_query(query: str, host: str, db: str, values: tuple | None) -> list[dict]:
    """Connect, execute *query*, and return all rows.

    For non-SELECT statements (INSERT/UPDATE/DELETE) an empty list is
    returned instead of calling ``fetchall``, which would raise.

    Raises:
        DatabaseConnectionError: connection failed.
        QueryExecutionError:     cursor.execute failed.
        DatabaseFetchError:      cursor.fetchall failed.
    """
    config = _build_db_config(host, db)

    try:
        connection = pymysql.connect(**config)
    except pymysql.Error as exc:
        logger.error("DB connection failed: %s", exc)
        raise DatabaseConnectionError(f"Cannot connect to {host}/{db}") from exc

    with connection as conn, conn.cursor() as cursor:
        try:
            cursor.execute(query, values or None)
        except pymysql.Error as exc:
            logger.error("Query execution failed: %s", exc)
            raise QueryExecutionError("Query failed") from exc

        if not _is_select_query(query):
            return []

        try:
            return cursor.fetchall()
        except pymysql.Error as exc:
            logger.error("Fetch failed: %s", exc)
            raise DatabaseFetchError("Could not fetch results") from exc


# ---------------------------------------------------------------------------
# Byte decoding helpers
# ---------------------------------------------------------------------------


def _decode(value: bytes) -> str:
    try:
        return value.decode("utf-8")
    except Exception:
        return str(value)


def decode_bytes_in_list(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Decode any byte values in a list of row dicts to str."""
    return [{k: (_decode(v) if isinstance(v, bytes) else v) for k, v in row.items()} for row in rows]


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def make_sql_connect_silent(
    query: str,
    *,
    host: str,
    db: str,
    values: tuple | None = None,
) -> list[dict]:
    """Execute *query* and return decoded rows; return [] on any error.

    Uses keyword-only args for host/db to prevent accidental positional misuse.
    """
    if not query:
        logger.debug("make_sql_connect_silent called with empty query")
        return []

    try:
        rows = _run_query(query, host=host, db=db, values=values)
    except DatabaseError as exc:
        logger.error("Suppressed database error: %s", exc)
        return []

    return decode_bytes_in_list(rows)


__all__ = ["make_sql_connect_silent", "decode_bytes_in_list"]
