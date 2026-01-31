#!/usr/bin/python3
""" """
import functools
import logging
from pathlib import Path
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

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
    # ---
    logger.debug("start :")
    # ---
    params = None
    # ---
    if values:
        params = values
    # ---
    # connect to the database server without error
    # ---
    DB_CONFIG = load_db_config(db, host)
    # ---
    try:
        connection = pymysql.connect(**DB_CONFIG)
    except Exception as e:
        logger.exception(e)
        return []
    # ---
    with connection as conn, conn.cursor() as cursor:
        # ---
        # skip sql errors
        try:
            cursor.execute(query, params)

        except Exception as e:
            logger.exception(e)
            return []
        # ---
        results = []
        # ---
        try:
            results = cursor.fetchall()

        except Exception as e:
            logger.exception(e)
            return []
        # ---
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
    # ---
    for row in rows:
        decoded_row = {}
        for key, value in row.items():
            if isinstance(value, bytes):
                value = decode_value(value)
            decoded_row[key] = value
        decoded_rows.append(decoded_row)
    # ---
    return decoded_rows


def make_sql_connect(query: str, db: str = "", host: str = "", values=None):
    # ---
    if not query:
        logger.debug("query == ''")
        return []
    # ---
    logger.debug("<<lightyellow>> newsql::")
    # ---
    rows = _sql_connect_pymysql(query, db=db, host=host, values=values)
    # ---
    rows = decode_bytes_in_list(rows)
    # ---
    return rows


__all__ = [
    "make_sql_connect",
    "decode_value",
    "decode_bytes_in_list",
]
