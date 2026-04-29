"""
Tests for template_query.py

This module tests template query functions for Wikipedia categories.
"""

import pytest

from src.core.new_c18.constants import SKIP_CATEGORIES
from src.core.new_c18.tools.template_query import TemplateCache, _cache, get_templates


class TestSkipCategories:
    """Tests for SKIP_CATEGORIES constant"""

    def test_skip_categories_contains_living_people(self):
        """Test that living people categories are in skip list"""
        assert "تصنيف:أشخاص على قيد الحياة" in SKIP_CATEGORIES
        assert "تصنيف:أشخاص أحياء" in SKIP_CATEGORIES


class TestTemplateCache:
    """Tests for TemplateCache class"""

    def test_returns_none_for_missing_cache(self):
        """Test that cache miss returns None"""
        cache = TemplateCache()
        result = cache.get("nonexistent_link", "ar")
        assert result is None


class TestGetTemplates:
    """Tests for get_templates function"""

    def test_returns_none_for_skip_categories(self):
        """Test that skip categories return None"""
        result = get_templates("تصنيف:أشخاص على قيد الحياة", "ar")
        assert result is None

    def test_returns_none_for_living_people(self):
        """Test that living people category returns None"""
        result = get_templates("تصنيف:أشخاص أحياء", "ar")
        assert result is None

    def test_returns_cached_value_if_available(self, mocker):
        """Test that cached values are returned without API call"""
        # Clear cache first
        _cache._store["ar"]["cached_test"] = {"cached_test": {"templates": ["قالب:تصنيف ويكيميديا"]}}

        result = get_templates("cached_test", "ar")
        assert result == ["قالب:تصنيف ويكيميديا"]

        # Clean up
        del _cache._store["ar"]["cached_test"]

    def test_calls_find_lcn_for_uncached_link(self, mocker):
        """Test that find_LCN is called for uncached links"""
        mock_find_lcn = mocker.patch(
            "src.core.new_c18.tools.template_query.find_LCN",
            return_value={"test": {"templates": ["قالب:test"]}},
        )

        # Use unique key to avoid cache
        result = get_templates("unique_test_link_123", "ar")

        mock_find_lcn.assert_called_once()

    def test_returns_none_when_no_templates_found(self, mocker):
        """Test that None is returned when no templates are found"""
        mocker.patch("src.core.new_c18.tools.template_query.find_LCN", return_value={"test": {}})

        result = get_templates("no_templates_link", "ar")
        assert result is None

    def test_returns_dict_for_batch_query(self, mocker):
        """Test that dict is returned for batch template queries"""
        mocker.patch(
            "src.core.new_c18.tools.template_query.find_LCN",
            return_value={"test1": {"templates": ["قالب:test"]}, "test2": {"templates": ["قالب:test2"]}},
        )

        result = get_templates(["test1", "test2"], "ar")
        assert isinstance(result, dict)

    def test_returns_none_when_find_lcn_returns_none_for_batch(self, mocker):
        """Test that None is returned when find_LCN returns None for batch"""
        mocker.patch("src.core.new_c18.tools.template_query.find_LCN", return_value=None)

        result = get_templates(["null_result_link"], "ar")
        assert result is None
