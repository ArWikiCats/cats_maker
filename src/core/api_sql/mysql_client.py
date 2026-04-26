#!/usr/bin/python3
""" """
import functools
import logging
from pathlib import Path
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

from ...exceptions import (
    DatabaseConnectionError,
    DatabaseError,
    DatabaseFetchError,
    QueryExecutionError,
)

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def load_db_config(db: str, host: str) -> dict[str, Any]:
    # --- 1) تحقق من ملف الإنتاج ~/replica.my.cnf ---
    replica_cnf_path = Path.home() / "replica.my.cnf"
    return {
        "host": host,
        "database": db,
        "read_default_file": str(replica_cnf_path),
        "charset": "utf8mb4",
        "use_unicode": True,
        "autocommit": True,
        "cursorclass": DictCursor,
    }


def _sql_connect_pymysql(query: str, db: str = "", host: str = "", values: tuple = None) -> list:
    """Execute a SQL query and return results.

    Args:
        query: SQL query to execute
        db: Database name
        host: Database host
        values: Parameters for parameterized queries

    Returns:
        List of result rows

    Raises:
        DatabaseConnectionError: If connection to database fails
        QueryExecutionError: If query execution fails
        DatabaseFetchError: If fetching results fails
    """

    logger.debug("start :")

    params = None

    if values:
        params = values

    # connect to the database server without error

    DB_CONFIG = load_db_config(db, host)

    try:
        connection = pymysql.connect(**DB_CONFIG)
    except pymysql.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e

    with connection as conn, conn.cursor() as cursor:

        # Execute query with parameters
        try:
            cursor.execute(query, params)

        except pymysql.Error as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryExecutionError(f"Failed to execute query: {e}") from e

        results = []

        try:
            results = cursor.fetchall()

        except pymysql.Error as e:
            logger.error(f"Failed to fetch results: {e}")
            raise DatabaseFetchError(f"Failed to fetch query results: {e}") from e

        # yield from cursor
        return results


def decode_value(value: bytes) -> str:
    try:
        value = value.decode("utf-8")  # Assuming UTF-8 encoding
    except Exception:
        try:
            value = str(value)
        except Exception:
            return ""
    return value


def decode_bytes_in_list(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decoded_rows = []

    for row in rows:
        decoded_row = {}
        for key, value in row.items():
            if isinstance(value, bytes):
                value = decode_value(value)
            decoded_row[key] = value
        decoded_rows.append(decoded_row)

    return decoded_rows


def make_sql_connect_silent(
    query: str,
    db: str = "",
    host: str = "",
    values=None,
):
    """Execute a SQL query and return decoded results.

    Args:
        query: SQL query to execute
        db: Database name
        host: Database host
        values: Parameters for parameterized queries

    Returns:
        List of decoded result rows, or empty list on error if silent=True
    """

    if not query:
        logger.debug("query == ''")
        return []

    logger.debug("<<lightyellow>> newsql::")

    try:
        rows = _sql_connect_pymysql(query, db=db, host=host, values=values)
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        return []

    rows = decode_bytes_in_list(rows)

    return rows


__all__ = [
    "make_sql_connect_silent",
    "decode_value",
    "decode_bytes_in_list",
]
