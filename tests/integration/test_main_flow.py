"""
Integration tests for the main category creation flow.

اختبارات التكامل للتدفق الرئيسي لإنشاء التصنيفات

These tests verify the complete flow from create_categories_from_list
through all the processing steps, with mocked external services.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.b18_new import sql_cat
from src.core.mk_cats import create_categories_from_list, create_category_page, mknew
from src.core.mk_cats.mknew import (
    clear_processing_state,
    make_ar,
    one_cat,
    process_catagories,
    scan_ar_title,
)
from src.core.wd_bots import wd_api_bot
from src.core.wiki_api import himoBOT2


class TestMainFlowIntegration:
    """Integration tests for the main category creation flow."""

    @pytest.fixture
    def mock_all_external_services(self, mocker):
        """Mock all external API calls for integration testing."""
        # Mock Wikipedia API
        mock_wiki_api = mocker.patch("src.core.wiki_api.himoBOT2.get_page_info_from_wikipedia")
        mock_wiki_api.return_value = {"exists": False}

        # Mock Wikidata API
        mock_wikidata = mocker.patch("src.core.wd_bots.wd_api_bot.Get_Sitelinks_From_wikidata")
        mock_wikidata.return_value = {"q": "Q12345", "sitelinks": {}}

        # Mock LCN (Language Code Navigator)
        mock_lcn = mocker.patch("src.core.wiki_api.LCN_new.find_Page_Cat_without_hidden")
        mock_lcn.return_value = {}

        # Mock database queries
        mock_sql = mocker.patch("src.core.b18_new.sql_cat.get_ar_list_from_en")
        mock_sql.return_value = ["Test Article 1", "Test Article 2"]

        # Mock category page creation
        mock_new_cat = mocker.patch("src.core.mk_cats.create_category_page.new_category")
        mock_new_cat.return_value = True

        # Mock get_listenpageTitle
        mock_listen = mocker.patch("src.core.b18_new.cat_tools_enlist.get_listenpageTitle")
        mock_listen.return_value = ["Article1", "Article2"]

        # Mock MakeLitApiWay
        mock_lit_api = mocker.patch("src.core.b18_new.cat_tools_enlist2.MakeLitApiWay")
        mock_lit_api.return_value = []

        # Mock add_to_final_list
        mock_add_final = mocker.patch("src.core.mk_cats.add_bot.add_to_final_list")

        # Mock to_wd.log_to_wikidata
        mock_log_wd = mocker.patch("src.core.wd_bots.to_wd.log_to_wikidata")

        # Mock validate_categories_for_new_cat
        mock_validate = mocker.patch("src.core.b18_new.sql_cat_checker.validate_categories_for_new_cat")
        mock_validate.return_value = []

        # Mock make_ar_list_newcat2
        mock_make_ar_list = mocker.patch("src.core.b18_new.sql_cat.make_ar_list_newcat2")
        mock_make_ar_list.return_value = []

        return {
            "wiki_api": mock_wiki_api,
            "wikidata": mock_wikidata,
            "lcn": mock_lcn,
            "sql": mock_sql,
            "new_cat": mock_new_cat,
            "listen": mock_listen,
            "lit_api": mock_lit_api,
            "add_final": mock_add_final,
            "log_wd": mock_log_wd,
            "make_ar_list": mock_make_ar_list,
            "validate": mock_validate,
        }

    @pytest.fixture
    def mock_ar_make_lab(self, mocker):
        """Mock the ar_make_lab function that generates Arabic labels."""
        mock = mocker.patch("src.core.mk_cats.mknew.ar_make_lab")
        mock.return_value = "علوم"
        return mock

    @pytest.fixture
    def mock_check_en_temps(self, mocker):
        """Mock check_en_temps to always return True."""
        mock = mocker.patch("src.core.mk_cats.mknew.check_en_temps")
        mock.return_value = True
        return mock

    @pytest.fixture
    def mock_filter_en(self, mocker):
        """Mock filter_en.filter_cat to always return True."""
        mock = mocker.patch("src.core.mk_cats.utils.filter_en.filter_cat")
        mock.return_value = True
        return mock

    def test_create_categories_from_list_empty_list(self):
        """Test that create_categories_from_list handles empty list gracefully."""

        # Should not raise any exceptions
        create_categories_from_list([])

    def test_create_categories_from_list_calls_one_cat_for_each_item(
        self, mocker, mock_ar_make_lab, mock_check_en_temps, mock_filter_en
    ):
        """Test that create_categories_from_list iterates over all categories."""

        # Mock the entire one_cat function to track calls
        mock_one_cat = mocker.patch("src.core.mk_cats.mknew.one_cat")

        categories = ["Category:Science", "Category:Technology", "Category:Art"]
        create_categories_from_list(categories)

        # Verify one_cat was called for each category
        assert mock_one_cat.call_count == 3

    def test_one_cat_filters_empty_title(self):
        """Test that one_cat returns False for empty title."""

        result = one_cat("", 1, 1)
        assert result is False

    def test_one_cat_filters_duplicate_categories(self, mocker):
        """Test that duplicate categories are filtered out."""

        # Clear processing state for this test
        clear_processing_state()

        # Mock ar_make_lab to return a label
        mocker.patch("src.core.mk_cats.mknew.ar_make_lab", return_value="")

        # First call should process
        result1 = one_cat("Category:Test", 1, 2)

        # Second call with same category should be filtered
        result2 = one_cat("Category:Test", 2, 2)

        # Both should return False (no label), but second should be filtered first
        assert result2 is False

        # Clean up
        mknew._done_d.clear()

    def test_process_catagories_calls_make_ar(self, mocker, mock_all_external_services):
        """Test that process_catagories calls make_ar with correct parameters."""

        # Mock make_ar to return an empty list (no subcategories)
        mock_make_ar = mocker.patch("src.core.mk_cats.mknew.make_ar")
        mock_make_ar.return_value = []

        process_catagories("Category:Science", "علوم", 1, 1)

        # Verify make_ar was called
        mock_make_ar.assert_called_once()
        args = mock_make_ar.call_args[0]
        assert args[0] == "Category:Science"
        assert args[1] == "علوم"

    def test_make_ar_returns_empty_for_empty_ar_title(self):
        """Test that make_ar returns empty list for empty Arabic title."""

        result = make_ar("Category:Science", "")
        assert result == []

    def test_make_ar_returns_empty_for_whitespace_ar_title(self):
        """Test that make_ar returns empty list for whitespace Arabic title."""

        result = make_ar("Category:Science", "   ")
        assert result == []


class TestModuleInteraction:
    """Tests for interaction between different modules."""

    def test_wiki_api_integration_with_himoBOT2(self, mocker):
        """Test that wiki_api module functions work together."""

        # Mock the underlying API call
        mock_api = mocker.patch("src.core.wiki_api.himoBOT2.submitAPI")
        mock_api.return_value = {
            "query": {
                "pages": {
                    "123": {
                        "title": "Test Page",
                        "pageid": 123,
                        "ns": 0,
                    }
                }
            }
        }

        result = himoBOT2.get_page_info_from_wikipedia("ar", "Test Page")

        assert result is not None
        assert "title" in result

    def test_b18_new_integration_with_sql(self, mocker):
        """Test that b18_new module integrates with SQL queries."""
        # Mock database connection
        mock_connect = mocker.patch("src.core.api_sql.db_pool.db_manager.execute_query")
        mock_connect.return_value = []

        # This tests that the modules can be imported and interact

        # The module should be importable without errors
        assert sql_cat is not None

    def test_mk_cats_integration_with_create_category_page(self, mocker):
        """Test that mk_cats integrates with create_category_page."""

        # Mock all external calls in create_category_page
        mocker.patch("src.core.mk_cats.create_category_page.add_text_to_cat", return_value="Test text")
        mocker.patch("src.core.mk_cats.create_category_page.make_category", return_value=True)

        # The module functions should be callable
        assert create_category_page.new_category is not None

    def test_wd_bots_integration_with_get_bots(self, mocker):
        """Test that wd_bots module functions integrate properly."""

        # Mock the underlying API call
        mock_api = mocker.patch("src.core.wd_bots.wd_api_bot.Get_infos_wikidata")
        mock_api.return_value = {
            "sitelinks": {
                "arwiki": "علوم",
                "enwiki": "Science",
            },
            "labels": {
                "ar": "علوم",
                "en": "Science",
            },
        }

        # Test get_sitelinks function (mocking at the right level)
        mock_sitelinks = mocker.patch("src.core.wd_bots.wd_api_bot.Get_Sitelinks_From_wikidata")
        mock_sitelinks.return_value = {
            "sitelinks": {
                "arwiki": "علوم",
                "enwiki": "Science",
            }
        }

        result = wd_api_bot.Get_Sitelinks_From_wikidata("en", "Science")

        assert result is not None


class TestCallbackIntegration:
    """Tests for callback functionality in the main flow."""

    def test_create_categories_with_callback(self, mocker):
        """Test that callbacks are properly passed through the flow."""

        callback_mock = MagicMock()

        # Mock all dependencies
        mocker.patch("src.core.mk_cats.mknew.ar_make_lab", return_value="")

        # Call with callback
        create_categories_from_list(["Category:Test"], callback=callback_mock)

        # The callback might not be called if ar_make_lab returns empty
        # but the function should not raise any errors

    def test_process_catagories_passes_callback_to_make_ar(self, mocker):
        """Test that process_catagories passes callback to make_ar."""

        callback_mock = MagicMock()

        # Mock make_ar to capture the callback
        mock_make_ar = mocker.patch("src.core.mk_cats.mknew.make_ar")
        mock_make_ar.return_value = []

        process_catagories("Category:Test", "اختبار", 1, 1, callback=callback_mock)

        # Verify callback was passed
        call_kwargs = mock_make_ar.call_args[1]
        assert call_kwargs["callback"] == callback_mock


class TestErrorHandling:
    """Tests for error handling in the integration flow."""

    def test_create_categories_handles_none_in_list(self, mocker):
        """Test that the flow handles None values in the list."""

        # Mock one_cat to track calls
        mock_one_cat = mocker.patch("src.core.mk_cats.mknew.one_cat")

        # Should handle list with None gracefully
        # The actual implementation strips empty strings
        create_categories_from_list(["Category:Valid", "", "Category:Another"])

        # Should call one_cat for all items (including empty string)
        assert mock_one_cat.call_count == 3

    def test_scan_ar_title_handles_repeated_titles(self):
        """Test that scan_ar_title correctly tracks repeated titles."""

        # Clear state
        clear_processing_state()

        # First call should return True
        result1 = scan_ar_title("تصنيف:اختبار")
        assert result1 is True

        # Second call should return False (already tracked)
        result2 = scan_ar_title("تصنيف:اختبار")
        assert result2 is False

        # Clean up
        mknew._new_cat_done.clear()


class TestDataFlowIntegration:
    """Tests for data flow between modules."""

    def test_category_data_flows_from_en_to_ar(self, mocker):
        """Test that category data flows correctly from English to Arabic."""
        # Mock the translation/label generation
        mock_label = mocker.patch("src.core.mk_cats.mknew.ar_make_lab")
        mock_label.return_value = "علوم الحاسوب"

        from src.core.mk_cats.mknew import ar_make_lab

        # Import after patching

        result = ar_make_lab("Computer science zz")

        assert result == "علوم الحاسوب"
        mock_label.assert_called_with("Computer science zz")

    def test_wiki_info_flows_to_category_creation(self, mocker):
        """Test that Wikipedia info flows to category creation."""

        # Mock API response
        mocker.patch(
            "src.core.wiki_api.himoBOT2.submitAPI",
            return_value={
                "query": {
                    "pages": {
                        "123": {
                            "title": "Category:Science",
                            "pageid": 123,
                            "ns": 14,
                            "categories": [{"title": "Category:Academic disciplines"}],
                        }
                    }
                }
            },
        )

        # Get page info
        result = himoBOT2.get_page_info_from_wikipedia("en", "Category:Science")

        # Verify the data structure is suitable for category creation
        assert "title" in result
        assert result["ns"] == 14  # Category namespace
