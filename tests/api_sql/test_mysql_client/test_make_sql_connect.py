"""
Tests for src/api_sql/mysql_client.py

اختبارات لملف mysql_client.py - استعلامات SQL

This module tests:
- decode_value() - Decode bytes to string
- decode_bytes_in_list() - Resolve bytes to string
"""

import pytest

from src.core.api_sql.mysql_client import (
    decode_bytes_in_list,
    decode_value,
)


class TestResolveBytes:
    """Tests for decode_bytes_in_list function."""

    def test_resolve_bytes_to_string(self):
        """Test that decode_bytes_in_list converts bytes to string."""
        input_dict = [
            {
                "key1": b"value1",
                "key2": "value2",
            }
        ]

        result = decode_bytes_in_list(input_dict)

        assert result[0]["key1"] == "value1"
        assert result[0]["key2"] == "value2"
        assert isinstance(result[0]["key1"], str)
        assert isinstance(result[0]["key2"], str)


class TestDecodeValue:
    """Tests for decode_value function."""

    def test_decode_bytes_to_string(self):
        """Test that decode_value decodes bytes to string."""

        result = decode_value(b"test_string")

        assert result == "test_string"
        assert isinstance(result, str)

    def test_decode_preserves_string(self):
        """Test that decode_value preserves string input."""

        result = decode_value("already_string")

        assert result == "already_string"

    def test_decode_handles_utf8(self):
        """Test that decode_value handles UTF-8 encoded bytes."""

        result = decode_value("مرحبا".encode("utf-8"))

        assert result == "مرحبا"

    def test_decode_handles_none(self):
        """Test that decode_value handles None input."""

        result = decode_value(None)

        # decode_value converts None to string 'None'
        assert result == "None" or result is None or result == ""
