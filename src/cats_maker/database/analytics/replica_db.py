from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

import pymysql
import pymysql.connections
import pymysql.cursors

logger = logging.getLogger(__name__)


class RowDecoder:
    """Handles decoding of database row values and byte normalization."""

    @staticmethod
    def decode_value(value: Any) -> str:
        """Decode a single database value to string, falling back safely."""
        try:
            return value.decode("utf-8")  # Assuming UTF-8 encoding
        except BaseException:
            try:
                return str(value)
            except BaseException:
                logger.debug("decode_value: could not decode value, returning empty string")
                return ""

    @classmethod
    def resolve_bytes(cls, rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        """Resolve byte values across a sequence of result rows."""
        decoded_rows: list[dict[str, Any]] = []

        for row in rows:
            decoded_row = {}
            for key, value in row.items():
                if isinstance(value, bytes):
                    value = cls.decode_value(value)
                decoded_row[key] = value
            decoded_rows.append(decoded_row)

        logger.debug("resolve_bytes: decoded %d row(s)", len(decoded_rows))
        return decoded_rows


class WikiReplicaBaseDB:
    """
    A lightweight, well-behaved connection wrapper for Wikimedia wiki replica databases.
    This class is intended for read-only access.
    """

    def __init__(
        self,
        dbname: str,
        host: str,
        user: str,
        password: str,
        port: int = 3306,
        row_decoder: type[RowDecoder] | None = None,
    ) -> None:
        self.dbname = dbname
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.connection: pymysql.connections.Connection | None = None
        self.row_decoder = row_decoder or RowDecoder

    def _ensure_connection(self) -> None:
        if not self.user or not self.password:
            logger.exception("No credentials provided")
            raise pymysql.err.OperationalError("No credentials provided")

        args = {
            "user": self.user,
            "password": self.password,
        }
        if self.connection is None or not self.connection.open:
            logger.debug("Opening connection to %s/%s", self.host, self.dbname)
            try:
                self.connection = pymysql.connect(
                    host=self.host,
                    database=self.dbname,
                    port=self.port,
                    charset="utf8mb4",
                    # force_unicode and use_unicode ensure bytes are converted to strings
                    use_unicode=True,
                    init_command="SET NAMES utf8mb4",  # Forces the connection to use utf8mb4
                    cursorclass=pymysql.cursors.DictCursor,
                    connect_timeout=10,
                    **args,  # type: ignore
                )  # type: ignore
            except pymysql.Error as e:
                logger.error("Failed to connect to %s/%s: %s", self.host, self.dbname, e)
                raise

            logger.debug("Connection to %s/%s established", self.host, self.dbname)

    def _select(
        self,
        query: str,
        params: Sequence[Any] | dict[str, Any] | None = None,
    ):
        """Execute query and return all results as a tuple of dictionaries."""
        self._ensure_connection()
        assert self.connection is not None

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
        except pymysql.Error as e:
            logger.error("Query failed: %s", e)
            logger.info(query)
            raise

        return rows

    def select(
        self,
        query: str,
        params: Sequence[Any] | dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute query and return all results as a list of dictionaries."""
        logger.debug("Executing query on %s/%s: %s", self.host, self.dbname, query)

        rows = self._select(query, params)
        result = self.row_decoder.resolve_bytes(rows)  # pyright: ignore[reportArgumentType]

        logger.debug("Query returned %d row(s)", len(result))
        return result

    def select_one(
        self,
        query: str,
        params: Sequence[Any] | dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Execute query and return the first result or None."""
        results = self.select(query, params)
        logger.debug("select_one: %s row(s) returned", len(results))
        return results[0] if results else None

    def select_safe(
        self,
        query: str,
        params: Sequence[Any] | dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute query safely, catching connection and execution errors."""
        results: list[dict[str, Any]] = []
        try:
            self._ensure_connection()
        except (pymysql.err.OperationalError, pymysql.Error) as e:
            logger.error("Failed to connect to %s/%s: %s", self.host, self.dbname, e)
            return results

        try:
            results = self.select(query, params)
        except (pymysql.ProgrammingError, pymysql.Error):
            logger.exception("Query failed", exc_info=True)
            logger.info(query)

        logger.debug("select_safe returned %d row(s)", len(results))
        return results

    def close(self) -> None:
        if self.connection and self.connection.open:
            logger.debug("Closing connection to %s/%s", self.host, self.dbname)
            self.connection.close()
            self.connection = None

    def __enter__(self) -> WikiReplicaBaseDB:
        self._ensure_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


__all__ = [
    "WikiReplicaBaseDB",
    "RowDecoder",
]
