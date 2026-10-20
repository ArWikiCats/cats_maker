"""
Tests for templates.py

This module tests template query functions for Wikipedia categories.
"""

from unittest.mock import MagicMock

from src.cats_maker.core_cat.infrastructure.network.templates import TemplateCache, TemplateClient


class TestTemplateCache:
    """Tests for TemplateCache storage operations."""

    def test_cache_miss_returns_none(self):
        cache = TemplateCache()
        assert cache.get("NonExistent", "ar") is None

    def test_cache_hit_returns_stored_value(self):
        cache = TemplateCache()
        cache.set("Example", "ar", {"templates": ["Test"]})
        assert cache.get("Example", "ar") == {"templates": ["Test"]}

    def test_returns_none_for_missing_cache(self):
        """
        Test that cache miss returns None"""
        cache = TemplateCache()
        result = cache.get("nonexistent_link", "ar")
        assert result is None


class TestGetTemplates:
    """Tests for TemplateClient().get_templates function"""

    def test_returns_none_for_skip_categories(self):
        """
        Test that skip categories return None"""
        result = TemplateClient().get_templates("تصنيف:أشخاص على قيد الحياة", "ar")
        assert result is None

    def test_returns_none_for_living_people(self):
        """
        Test that living people category returns None"""
        result = TemplateClient().get_templates("تصنيف:أشخاص أحياء", "ar")
        assert result is None

    def test_calls_find_lcn_for_uncached_link(self, mocker):
        """
        Test that find_page_data is called for uncached links"""

        langlinks_client = MagicMock()
        langlinks_client.find_page_data = MagicMock(return_value={"test": {"templates": ["قالب:test"]}})

        # Use unique key to avoid cache
        TemplateClient(langlinks_client=langlinks_client).get_templates("unique_test_link_123", "ar")

        langlinks_client.find_page_data.assert_called_once()

    def test_returns_none_when_no_templates_found(self, mocker):
        """
        Test that None is returned when no templates are found"""

        langlinks_client = MagicMock()
        langlinks_client.find_page_data = MagicMock(return_value={"test": {}})

        result = TemplateClient(langlinks_client=langlinks_client).get_templates("no_templates_link", "ar")
        assert result is None

    def test_returns_dict_for_batch_query(self, mocker):
        """
        Test that dict is returned for batch template queries"""
        langlinks_client = MagicMock()
        langlinks_client.find_page_data = MagicMock(
            return_value={"test1": {"templates": ["قالب:test"]}, "test2": {"templates": ["قالب:test2"]}}
        )

        result = TemplateClient(langlinks_client=langlinks_client).get_templates(["test1", "test2"], "ar")
        assert isinstance(result, dict)

    def test_returns_none_when_find_lcn_returns_none_for_batch(self, mocker):
        """
        Test that None is returned when find_page_data returns None for batch"""

        langlinks_client = MagicMock()
        langlinks_client.find_page_data = MagicMock(return_value=None)

        result = TemplateClient(langlinks_client=langlinks_client).get_templates(["null_result_link"], "ar")
        assert result is None


class TestTemplateQueryService:
    """Tests for TemplateClient logic with injected fakes."""

    def test_query_skips_blacklisted_categories(self):
        langlinks_client = MagicMock()
        service = TemplateClient(langlinks_client=langlinks_client, skip_categories={"BadCategory"})

        result = service.query("BadCategory", "ar")
        assert result is None
        langlinks_client.find_page_data.assert_not_called()

    def test_query_returns_cached_data_without_api_call(self):
        cache = TemplateCache()
        cache.set("CachedPage", "ar", {"templates": ["Template1"]})
        langlinks_client = MagicMock()

        service = TemplateClient(langlinks_client=langlinks_client, cache=cache)
        result = service.query("CachedPage", "ar")

        assert result == {"templates": ["Template1"]}
        langlinks_client.find_page_data.assert_not_called()
