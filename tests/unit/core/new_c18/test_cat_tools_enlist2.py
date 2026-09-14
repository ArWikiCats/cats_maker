"""
Tests for category_resolver.py

This module tests category member API functions.
"""

from src.core.new_c18.core.category_resolver import CategoryResolver


class TestMakeLitApiWay:
    """Tests for CategoryResolver.make_lit_api_way method"""

    def test_returns_empty_list_for_empty_title(self, mocker):
        """
        Test that empty list is returned for empty title"""
        resolver = CategoryResolver()
        result = resolver.make_lit_api_way("")
        assert result == []

    def test_returns_empty_list_for_none_title(self, mocker):
        """
        Test that empty list is returned for None title"""
        resolver = CategoryResolver()
        result = resolver.make_lit_api_way(None) # pyright: ignore[reportArgumentType]
        assert result == []
