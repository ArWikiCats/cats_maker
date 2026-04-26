"""
Tests for src/b18_new/cat_tools.py

اختبارات لملف cat_tools.py - أدوات التصنيفات

This module tests:
- templateblacklist - Template blacklist
- nameblcklist - Name blacklist
"""

from unittest.mock import MagicMock, patch

import pytest

from src.b18_new import cat_tools


class TestBlacklists:
    """Tests for template and name blacklists."""

    def test_templateblacklist_exists(self):
        """Test that templateblacklist is defined."""
        from src.b18_new.cat_tools import templateblacklist

        assert templateblacklist is not None
        assert isinstance(templateblacklist, (list, tuple))

    def test_nameblcklist_exists(self):
        """Test that nameblcklist is defined."""
        from src.b18_new.cat_tools import nameblcklist

        assert nameblcklist is not None
        assert isinstance(nameblcklist, list)

    def test_nameblcklist_contains_expected_items(self):
        """Test that nameblcklist contains expected items."""
        from src.b18_new.cat_tools import nameblcklist

        expected_items = [
            "Current events",
            "Articles with",
            "Tracking",
            "Surnames",
            "Given names",
        ]

        for item in expected_items:
            assert item in nameblcklist

    def test_nameblcklist_contains_stubs(self):
        """Test that nameblcklist contains 'stubs'."""
        from src.b18_new.cat_tools import nameblcklist

        # stubs should be in the list by default
        assert "stubs" in nameblcklist
