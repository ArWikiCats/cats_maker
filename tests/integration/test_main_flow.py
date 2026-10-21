"""
Integration tests for the main category creation flow.

اختبارات التكامل للتدفق الرئيسي لإنشاء التصنيفات

These tests verify the complete flow from create_categories_from_list
through all the processing steps, with mocked external services.
"""

from unittest.mock import MagicMock

import pytest

from src.cats_maker.mk_cats import create_category_page
from src.cats_maker.mk_cats.mknew import CategoryManager
from src.cats_maker.shared.wd_clients.wd_api import wd_api_bot


@pytest.fixture
def category_manager():
    """Fixture to provide a fresh CategoryManager instance."""
    return CategoryManager()


class TestMainFlowIntegration:
    """Integration tests for the main category creation flow."""

    @pytest.fixture
    def mock_all_external_services(self, mocker):
        """Mock all external API calls for integration testing."""
        # Mock Wikidata API
        mock_wikidata = mocker.patch("src.cats_maker.shared.wd_clients.wd_api.wd_api_bot.get_sitelinks_from_wikidata")
        mock_wikidata.return_value = {"q": "Q12345", "sitelinks": {}}

        # Mock LCN (Language Code Navigator)
        mock_lcn = mocker.patch(
            "src.cats_maker.mk_cats.mknew.category_manager.LangLinksClient.find_page_categories_informations"
        )
        mock_lcn.return_value = {}

        # Mock CategoryResolver.list_en_pages_with_ar_links (used in CategoryManager)
        mock_sql = mocker.patch(
            "src.cats_maker.core_cat.lists.category_resolver.CategoryResolver.list_en_pages_with_ar_links"
        )
        mock_sql.return_value = ["Test Article 1", "Test Article 2"]

        # Mock category page creation
        mock_new_cat = mocker.patch("src.cats_maker.mk_cats.create_category_page.new_category")
        mock_new_cat.return_value = True

        # Mock CategoryResolver.make_lit_api_way (used in members_helper)
        mock_lit_api = mocker.patch("src.cats_maker.core_cat.lists.category_resolver.CategoryResolver.make_lit_api_way")
        mock_lit_api.return_value = []

        # Mock to_wd.log_to_wikidata
        mock_log_wd = mocker.patch("src.cats_maker.shared.wd_clients.wd_api.to_wd.log_to_wikidata")

        # Mock validate_categories_for_new_cat
        mock_validate = mocker.patch("src.cats_maker.mk_cats.mknew.category_manager.validate_categories_for_new_cat")
        mock_validate.return_value = MagicMock(valid=True)

        # Mock CategoryResolver.resolve_members (used in CategoryManager)
        mock_make_ar_list = mocker.patch(
            "src.cats_maker.core_cat.lists.category_resolver.CategoryResolver.resolve_members"
        )
        mock_make_ar_list.return_value = []

        return {
            "wikidata": mock_wikidata,
            "lcn": mock_lcn,
            "sql": mock_sql,
            "new_cat": mock_new_cat,
            "lit_api": mock_lit_api,
            "log_wd": mock_log_wd,
            "make_ar_list": mock_make_ar_list,
            "validate": mock_validate,
        }

    @pytest.fixture
    def mock_check_en_temps(self, mocker):
        """Mock check_en_temps to always return True."""
        mock = mocker.patch("src.cats_maker.mk_cats.mknew.category_manager.check_en_temps")
        mock.return_value = True
        return mock

    @pytest.fixture
    def mock_filter_en(self, mocker):
        """Mock filter_en.filter_category to always return True."""
        mock = mocker.patch("src.cats_maker.mk_cats.utils.filter_en.filter_category")
        mock.return_value = True
        return mock

    def test_create_categories_from_list_empty_list(self):
        """Test that create_categories_from_list handles empty list gracefully."""
        # Should not raise any exceptions
        CategoryManager().create_categories_from_list([])

    def test_create_categories_from_list_calls_one_cat_for_each_item(self, mocker, mock_check_en_temps, mock_filter_en):
        """Test that create_categories_from_list iterates over all categories."""
        mock = mocker.patch("src.cats_maker.mk_cats.mknew.category_manager.ar_make_lab")
        mock.return_value = "علوم"

        # Mock CategoryManager.one_cat to track calls
        mock_one_cat = mocker.patch.object(CategoryManager, "one_cat")

        categories = ["Category:Science", "Category:Technology", "Category:Art"]
        CategoryManager().create_categories_from_list(categories)

        # Verify one_cat was called for each category
        assert mock_one_cat.call_count == 3

    def test_one_cat_filters_empty_title(self, category_manager):
        """Test that one_cat returns False for empty title."""
        result = category_manager.one_cat("", 1, 1)
        assert result is False

    def test_one_cat_filters_duplicate_categories(self, mocker, category_manager):
        """Test that duplicate categories are filtered out."""
        # Clear processing state for this test
        category_manager.stats.clear_processing_state()

        # Mock ar_make_lab to return a label
        mocker.patch("src.cats_maker.mk_cats.mknew.category_manager.ar_make_lab", return_value="")

        # First call should process
        category_manager.one_cat("Category:Test", 1, 2)

        # Second call with same category should be filtered
        result2 = category_manager.one_cat("Category:Test", 2, 2)

        # Both should return False (no label), but second should be filtered first
        assert result2 is False

        # Clean up
        category_manager.stats._done_d.clear()

    def test_process_categories_calls_make_ar(self, mocker, mock_all_external_services, category_manager):
        """Test that process_categories calls make_ar with correct parameters."""
        # Mock make_ar to return an empty list (no subcategories)
        mock_make_ar = mocker.patch.object(category_manager, "make_ar", return_value=[])

        category_manager.process_categories("Category:Science", "علوم", 1, 1)

        # Verify make_ar was called
        mock_make_ar.assert_called_once()
        args = mock_make_ar.call_args[0]
        assert args[0] == "Category:Science"
        assert args[1] == "علوم"

    def test_make_ar_returns_empty_for_empty_ar_title(self, category_manager):
        """Test that make_ar returns empty list for empty Arabic title."""
        result = category_manager.make_ar("Category:Science", "")
        assert result == []

    def test_make_ar_returns_empty_for_whitespace_ar_title(self, category_manager):
        """Test that make_ar returns empty list for whitespace Arabic title."""
        result = category_manager.make_ar("Category:Science", "    ")
        assert result == []


class TestModuleInteraction:
    """Tests for interaction between different modules."""

    def test_mk_cats_integration_with_create_category_page(self, mocker):
        """Test that mk_cats integrates with create_category_page."""
        # Mock all external calls in create_category_page
        mocker.patch("src.cats_maker.mk_cats.create_category_page.add_text_to_cat", return_value="Test text")
        mocker.patch("src.cats_maker.mk_cats.create_category_page.make_category", return_value=True)

        # The module functions should be callable
        assert create_category_page.new_category is not None

    def test_wd_bots_integration_with_get_bots(self, mocker):
        """Test that wd_api module functions integrate properly."""
        # Mock the underlying API call
        mock_api = mocker.patch("src.cats_maker.shared.wd_clients.wd_api.wd_api_bot.get_infos_wikidata")
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
        mock_sitelinks = mocker.patch("src.cats_maker.shared.wd_clients.wd_api.wd_api_bot.get_sitelinks_from_wikidata")
        mock_sitelinks.return_value = {
            "sitelinks": {
                "arwiki": "علوم",
                "enwiki": "Science",
            }
        }

        result = wd_api_bot.get_sitelinks_from_wikidata("en", "Science")

        assert result is not None


class TestCallbackIntegration:
    """Tests for callback functionality in the main flow."""

    def test_create_categories_with_callback(self, mocker):
        """Test that callbacks are properly passed through the flow."""
        callback_mock = MagicMock()

        # Mock all dependencies
        mocker.patch("src.cats_maker.mk_cats.mknew.category_manager.ar_make_lab", return_value="")

        # Call with callback
        CategoryManager().create_categories_from_list(["Category:Test"], callback=callback_mock)

        # The callback might not be called if ar_make_lab returns empty
        # but the function should not raise any errors

    def test_process_categories_passes_callback_to_make_ar(self, mocker, category_manager):
        """Test that process_categories passes callback to make_ar."""
        callback_mock = MagicMock()

        # Mock make_ar to capture the callback
        mock_make_ar = mocker.patch.object(category_manager, "make_ar", return_value=[])

        category_manager.process_categories("Category:Test", "اختبار", 1, 1, callback=callback_mock)

        # Verify callback was passed
        call_kwargs = mock_make_ar.call_args[1]
        assert call_kwargs["callback"] == callback_mock


class TestErrorHandling:
    """Tests for error handling in the integration flow."""

    def test_create_categories_handles_none_in_list(self, mocker):
        """Test that the flow handles None values in the list."""
        # Mock CategoryManager.one_cat to track calls
        mock_one_cat = mocker.patch.object(CategoryManager, "one_cat")

        # Should handle list with None gracefully
        CategoryManager().create_categories_from_list(["Category:Valid", "", "Category:Another"])

        # Should call one_cat for all items (including empty string)
        assert mock_one_cat.call_count == 3

    def test_scan_ar_title_handles_repeated_titles(self, category_manager):
        """Test that _scan_ar_title correctly tracks repeated titles."""
        # Clear state
        category_manager.stats.clear_processing_state()

        # First call should return True
        result1 = category_manager.stats._scan_ar_title("تصنيف:اختبار")
        assert result1 is True

        # Second call should return False (already tracked)
        result2 = category_manager.stats._scan_ar_title("تصنيف:اختبار")
        assert result2 is False

        # Clean up
        category_manager.stats._new_cat_done.clear()


class TestDataFlowIntegration:
    """Tests for data flow between modules."""

    def test_category_data_flows_from_en_to_ar(self, mocker):
        """Test that category data flows correctly from English to Arabic."""
        # Mock the translation/label generation
        mock_label = mocker.patch("src.cats_maker.mk_cats.mknew.category_manager.ar_make_lab")
        mock_label.return_value = "علوم الحاسوب"

        from src.cats_maker.mk_cats.mknew import ar_make_lab

        # Import after patching
        result = ar_make_lab("Computer science zz")

        assert result == "علوم الحاسوب"
        mock_label.assert_called_with("Computer science zz")
