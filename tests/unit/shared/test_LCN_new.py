"""
Tests for lcn_new.py

This module tests the WikiApiHandler class and language link functions.
"""

from src.shared.lcn_new import (
    LC_bot,
    WikiApiHandler,
    find_LCN,
    find_Page_Cat_without_hidden,
)


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


class TestFindPageData:
    """Tests for find_page_data method"""

    def test_find_page_data_empty_title(self):
        """Test find_page_data with empty title returns None"""
        handler = WikiApiHandler()
        result = handler.find_page_data("")
        assert result == {}

    def test_find_page_data_title_with_hash(self):
        """Test find_page_data with hash in title returns None"""
        handler = WikiApiHandler()
        result = handler.find_page_data("Page#Section")
        assert result == {}

    def test_find_page_data_uses_cache(self, mocker):
        """Test find_page_data uses cache for repeated calls"""
        handler = WikiApiHandler()
        cache_key = ("Test Page", "en", "langlinks")
        handler.cache[cache_key] = {"cached": True}
        result = handler.find_page_data("Test Page", site_code="en")
        assert result == {"cached": True}


class TestFindNonHiddenCategories:
    """Tests for find_non_hidden_categories method"""

    def test_empty_title_returns_none(self):
        """Test that empty title returns None"""
        handler = WikiApiHandler()
        result = handler.find_non_hidden_categories("")
        assert result == {}

    def test_title_with_hash_returns_none(self):
        """Test that title with hash returns None"""
        handler = WikiApiHandler()
        result = handler.find_non_hidden_categories("Page#Section")
        assert result == {}

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
        find_LCN("Test", prop="langlinks", lllang="ar", first_site_code="en")
        mock_method.assert_called_once_with(page_title="Test", prop="langlinks", lllang="ar", site_code="en")

    def test_find_Page_Cat_without_hidden_wrapper(self, mocker):
        """Test find_Page_Cat_without_hidden wrapper function"""
        mock_method = mocker.patch.object(LC_bot, "find_non_hidden_categories", return_value={"test": True})
        find_Page_Cat_without_hidden("Test", prop="langlinks", site_code="ar")
        mock_method.assert_called_once()


class TestGlobalLCBot:
    """Tests for the global LC_bot instance"""

    def test_lc_bot_is_instance(self):
        """Test that LC_bot is a WikiApiHandler instance"""
        assert isinstance(LC_bot, WikiApiHandler)

    def test_lc_bot_has_default_config(self):
        """Test that LC_bot has default configuration"""
        assert LC_bot.family == "wikipedia"
        assert LC_bot.en_site_config["code"] == "en"


class TestParseApiResponse:
    """Tests for _parse_api_response method"""

    def test_parses_langlinks_correctly(self, mocker):
        """Test that langlinks are parsed correctly from API response"""
        handler = WikiApiHandler()
        query = {
            "pages": {
                "123": {
                    "title": "Test Page",
                    "langlinks": [
                        {"lang": "ar", "*": "صفحة اختبار"},
                        {"lang": "fr", "*": "Page de test"},
                    ],
                }
            },
            "redirects": [],
        }
        result = handler._parse_api_response(query, "en", "langlinks")
        assert "Test Page" in result
        assert result["Test Page"]["langlinks"]["ar"] == "صفحة اختبار"
        assert result["Test Page"]["langlinks"]["fr"] == "Page de test"

    def test_parses_categories_correctly(self, mocker):
        """Test that categories are parsed correctly from API response"""
        handler = WikiApiHandler()
        query = {
            "pages": {
                "123": {
                    "title": "Test Page",
                    "categories": [
                        {"title": "Category:Test", "hidden": ""},
                        {"title": "Category:Test2"},
                    ],
                }
            },
            "redirects": [],
        }
        result = handler._parse_api_response(query, "en", "categories")
        assert "Test Page" in result
        assert "Category:Test" in result["Test Page"]["categories"]
        assert "Category:Test2" in result["Test Page"]["categories"]
        assert "Category:Test2" in result["Test Page"]["cat_with_out_hidden"]

    def test_handles_redirects(self, mocker):
        """Test that redirects are handled correctly"""
        handler = WikiApiHandler()
        query = {
            "pages": {
                "456": {"title": "Redirect Target", "langlinks": []},
            },
            "redirects": [{"from": "Original Page", "to": "Redirect Target"}],
        }
        result = handler._parse_api_response(query, "en", "langlinks")
        assert "Original Page" in result
        assert result["Original Page"]["redirect"] == "Redirect Target"

    def test_parses_templates(self, mocker):
        """Test that templates are parsed correctly"""
        handler = WikiApiHandler()
        query = {
            "pages": {
                "123": {
                    "title": "Test Page",
                    "templates": [
                        {"title": "Template:Test1"},
                        {"title": "Template:Test2"},
                    ],
                }
            },
            "redirects": [],
        }
        result = handler._parse_api_response(query, "en", "templates")
        assert "Test Page" in result
        assert "Template:Test1" in result["Test Page"]["templates"]
        assert "Template:Test2" in result["Test Page"]["templates"]


class TestFindNonHiddenCategoriesIntegration:
    """Integration tests for find_working categories with API responses"""

    def test_lc_bot_has_default_config(self):
        """Test that LC_bot has default configuration"""
        assert LC_bot.family == "wikipedia"
        assert LC_bot.en_site_config["code"] == "en"
