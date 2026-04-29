"""
Tests for LCN_new.py

This module tests the WikiApiHandler class and language link functions.
"""

import pytest

from src.core.wiki_api.LCN_new import (
    LC_bot,
    WikiApiCache,
    WikiApiHandler,
    find_LCN,
    find_Page_Cat_without_hidden,
    get_arpage_inside_encat,
    get_cache_L_C_N,
    set_cache_L_C_N,
)


class TestWikiApiCache:
    """Tests for WikiApiCache class"""

    def test_init_creates_empty_cache(self):
        """Test that WikiApiCache initializes with empty cache"""
        cache = WikiApiCache()
        assert cache.cache == {}

    def test_init_with_custom_max_size(self):
        """Test that WikiApiCache accepts custom max_size"""
        cache = WikiApiCache(max_size=500)
        assert cache.cache == {}

    def test_init_with_custom_ttl(self):
        """Test that WikiApiCache accepts custom ttl_seconds"""
        cache = WikiApiCache(ttl_seconds=1800)
        assert cache.cache == {}


class TestWikiApiHandler:
    """Tests for WikiApiHandler class"""

    def test_init_default_config(self):
        """Test WikiApiHandler default configuration"""
        handler = WikiApiHandler()
        assert handler.family == "wikipedia"
        assert handler.en_site_config["code"] == "en"
        assert handler.en_site_config["family"] == "wikipedia"

    def test_init_custom_site(self):
        """Test WikiApiHandler with custom site configuration"""
        handler = WikiApiHandler(default_en_site_code="de", family="wikisource")
        assert handler.en_site_config["code"] == "de"
        assert handler.family == "wikisource"

    def test_init_empty_cache(self):
        """Test that handler initializes with empty cache"""
        handler = WikiApiHandler()
        assert handler.cache == {}

    def test_init_empty_deleted_list(self):
        """Test that handler initializes with empty deleted list"""
        handler = WikiApiHandler()
        assert handler.deleted == []

    def test_init_api_call_count_zero(self):
        """Test that API call count starts at zero"""
        handler = WikiApiHandler()
        assert handler.api_call_count == 0

    def test_increment_api_call(self):
        """Test API call counter increment"""
        handler = WikiApiHandler()
        count = handler._increment_api_call()
        assert count == 1
        count = handler._increment_api_call()
        assert count == 2

    def test_get_arpage_inside_encat_returns_none_for_missing_key(self):
        """Test get_arpage_inside_encat returns None for missing key"""
        handler = WikiApiHandler()
        result = handler.get_arpage_inside_encat("nonexistent_key")
        assert result is None

    def test_get_arpage_inside_encat_returns_value_for_existing_key(self):
        """Test get_arpage_inside_encat returns value for existing key"""
        handler = WikiApiHandler()
        handler.arpage_inside_en_cat["test_cat"] = ["page1", "page2"]
        result = handler.get_arpage_inside_encat("test_cat")
        assert result == ["page1", "page2"]

    def test_get_deleting_page_returns_list(self):
        """Test get_deleting_page returns deleted list"""
        handler = WikiApiHandler()
        handler.deleted = ["deleted_page"]
        result = handler.get_deleting_page()
        assert result == ["deleted_page"]


class TestFindPageData:
    """Tests for find_page_data method"""

    def test_find_page_data_empty_title(self):
        """Test find_page_data with empty title returns False"""
        handler = WikiApiHandler()
        result = handler.find_page_data("")
        assert result is False

    def test_find_page_data_title_with_hash(self):
        """Test find_page_data with hash in title returns False"""
        handler = WikiApiHandler()
        result = handler.find_page_data("Page#Section")
        assert result is False

    def test_find_page_data_uses_cache(self, mocker):
        """Test find_page_data uses cache for repeated calls"""
        handler = WikiApiHandler()
        cache_key = ("Test Page", "en", "langlinks")
        handler.cache[cache_key] = {"cached": True}
        result = handler.find_page_data("Test Page", site_code="en")
        assert result == {"cached": True}


class TestFindNonHiddenCategories:
    """Tests for find_non_hidden_categories method"""

    def test_empty_title_returns_false(self):
        """Test that empty title returns False"""
        handler = WikiApiHandler()
        result = handler.find_non_hidden_categories("")
        assert result is False

    def test_title_with_hash_returns_false(self):
        """Test that title with hash returns False"""
        handler = WikiApiHandler()
        result = handler.find_non_hidden_categories("Page#Section")
        assert result is False

    def test_uses_cache_for_repeated_calls(self):
        """Test that cached results are returned"""
        handler = WikiApiHandler()
        cache_key = ("Test Page", "ar", "Cat_without_hidden", "")
        handler.cache[cache_key] = {"cached_categories": True}
        result = handler.find_non_hidden_categories("Test Page", site_code="ar")
        assert result == {"cached_categories": True}


class TestBackwardCompatibilityFunctions:
    """Tests for backward compatibility wrapper functions"""

    def test_find_LCN_calls_find_page_data(self, mocker):
        """Test find_LCN wrapper function"""
        mock_method = mocker.patch.object(LC_bot, "find_page_data", return_value={"test": True})
        result = find_LCN("Test", prop="langlinks", lllang="ar", first_site_code="en")
        mock_method.assert_called_once_with(page_title="Test", prop="langlinks", lllang="ar", site_code="en")

    def test_find_Page_Cat_without_hidden_wrapper(self, mocker):
        """Test find_Page_Cat_without_hidden wrapper function"""
        mock_method = mocker.patch.object(LC_bot, "find_non_hidden_categories", return_value={"test": True})
        result = find_Page_Cat_without_hidden("Test", prop="langlinks", site_code="ar")
        mock_method.assert_called_once()

    def test_get_arpage_inside_encat_wrapper(self):
        """Test get_arpage_inside_encat wrapper function"""
        LC_bot.arpage_inside_en_cat["test_key"] = ["value"]
        result = get_arpage_inside_encat("test_key")
        assert result == ["value"]

    def test_set_cache_L_C_N_sets_value(self):
        """Test set_cache_L_C_N sets cache value"""
        set_cache_L_C_N(("test", "key"), "test_value")
        assert LC_bot.cache[("test", "key")] == "test_value"

    def test_get_cache_L_C_N_gets_value(self):
        """Test get_cache_L_C_N gets cache value"""
        LC_bot.cache[("get", "test")] = "cached_value"
        result = get_cache_L_C_N(("get", "test"))
        assert result == "cached_value"

    def test_get_cache_L_C_N_returns_none_for_missing(self):
        """Test get_cache_L_C_N returns None for missing key"""
        result = get_cache_L_C_N(("nonexistent", "key"))
        assert result is None


class TestGlobalLCBot:
    """Tests for the global LC_bot instance"""

    def test_lc_bot_is_instance(self):
        """Test that LC_bot is a WikiApiHandler instance"""
        assert isinstance(LC_bot, WikiApiHandler)

    def test_lc_bot_has_default_config(self):
        """Test that LC_bot has default configuration"""
        assert LC_bot.family == "wikipedia"
        assert LC_bot.en_site_config["code"] == "en"
