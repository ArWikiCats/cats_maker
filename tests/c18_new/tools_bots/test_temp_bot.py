"""
Tests for src/c18_new/tools_bots/temp_bot.py

This module tests template query functions for Wikipedia categories.
"""

import pytest

from src.core.c18_new.tools_bots.temp_bot import (
    SKIP_CATEGORIES,
    _get_from_cache,
    templatequery,
    templatequery_cache,
    templatequerymulti,
)


class TestSkipCategories:
    """Tests for SKIP_CATEGORIES constant"""

    def test_skip_categories_contains_living_people(self):
        """Test that living people categories are in skip list"""
        assert "تصنيف:أشخاص على قيد الحياة" in SKIP_CATEGORIES
        assert "تصنيف:أشخاص أحياء" in SKIP_CATEGORIES


class TestGetFromCache:
    """Tests for _get_from_cache function"""

    def test_returns_none_for_missing_cache(self):
        """Test that cache miss returns None"""
        cached, tup, site_cache = _get_from_cache("nonexistent_link", "ar")
        assert cached is None
        assert tup == ("nonexistent_link", "ar", "templates")


class TestTemplatequery:
    """Tests for templatequery function"""

    def test_returns_false_for_skip_categories(self):
        """Test that skip categories return False"""
        result = templatequery("تصنيف:أشخاص على قيد الحياة", "ar")
        assert result is False

    def test_returns_false_for_living_people(self):
        """Test that living people category returns False"""
        result = templatequery("تصنيف:أشخاص أحياء", "ar")
        assert result is False

    def test_returns_cached_value_if_available(self, mocker):
        """Test that cached values are returned without API call"""
        # Clear cache first
        templatequery_cache["ar"]["cached_test"] = ["قالب:تصنيف ويكيميديا"]

        result = templatequery("cached_test", "ar")
        assert result == ["قالب:تصنيف ويكيميديا"]

        # Clean up
        del templatequery_cache["ar"]["cached_test"]

    def test_calls_find_LCN_for_uncached_link(self, mocker):
        """Test that find_LCN is called for uncached links"""
        mock_find_lcn = mocker.patch(
            "src.core.c18_new.tools_bots.temp_bot.find_LCN", return_value={"test": {"templates": ["قالب:test"]}}
        )

        # Use unique key to avoid cache
        result = templatequery("unique_test_link_123", "ar")

        mock_find_lcn.assert_called_once()

    def test_returns_false_when_no_templates_found(self, mocker):
        """Test that False is returned when no templates are found"""
        mocker.patch("src.core.c18_new.tools_bots.temp_bot.find_LCN", return_value={"test": {}})

        result = templatequery("no_templates_link", "ar")
        assert result is False


class TestTemplatequeryMulti:
    """Tests for templatequerymulti function"""

    def test_returns_false_for_skip_categories(self):
        """Test that skip categories return False"""
        result = templatequerymulti("تصنيف:أشخاص على قيد الحياة", "ar")
        assert result is False

    def test_returns_cached_value_if_available(self, mocker):
        """Test that cached values are returned without API call"""
        templatequery_cache["ar"]["multi_cached_test"] = {"result": "test"}

        result = templatequerymulti("multi_cached_test", "ar")
        assert result == {"result": "test"}

        # Clean up
        del templatequery_cache["ar"]["multi_cached_test"]

    def test_calls_find_LCN_for_uncached_link(self, mocker):
        """Test that find_LCN is called for uncached links"""
        mock_find_lcn = mocker.patch(
            "src.core.c18_new.tools_bots.temp_bot.find_LCN", return_value={"test": {"templates": ["قالب:test"]}}
        )

        result = templatequerymulti("unique_multi_test_link_456", "ar")

        mock_find_lcn.assert_called_once()

    def test_returns_false_when_find_lcn_returns_none(self, mocker):
        """Test that False is returned when find_LCN returns None"""
        mocker.patch("src.core.c18_new.tools_bots.temp_bot.find_LCN", return_value=None)

        result = templatequerymulti("null_result_link", "ar")
        assert result is False
