"""
Tests for src/mk_cats/mknew.py

اختبارات لملف mknew.py - الملف الرئيسي لإنشاء التصنيفات

This module tests:
- create_categories_from_list() - Main function to create categories
- one_cat() - Process a single category
- process_catagories() - Recursive category processing
- make_ar() - Create Arabic category
- ar_make_lab() - Generate Arabic label
- scan_ar_title() - Scan Arabic titles
- check_if_artitle_exists() - Check if Arabic title exists
"""

from unittest.mock import MagicMock, patch

import pytest


class TestCheckIfArtitleExists:
    """Tests for check_if_artitle_exists function."""

    pass


class TestArMakeLab:
    """Tests for ar_make_lab function."""

    def test_returns_empty_when_filter_fails(self, mocker):
        """Test that ar_make_lab returns empty string when filter_cat fails."""
        mocker.patch("src.mk_cats.mknew.filter_cat", return_value=False)

        from src.mk_cats.mknew import ar_make_lab

        result = ar_make_lab("Category:Test")

        assert result == ""

    def test_returns_empty_when_no_resolver(self, mocker):
        """Test that ar_make_lab returns empty when resolve_arabic_category_label is None."""
        mocker.patch("src.mk_cats.mknew.filter_cat", return_value=True)
        mocker.patch("src.mk_cats.mknew.resolve_arabic_category_label", None)

        from src.mk_cats.mknew import ar_make_lab

        result = ar_make_lab("Category:Science")

        assert result == ""

    def test_returns_label_when_resolver_exists(self, mocker):
        """Test that ar_make_lab returns label when resolver exists."""
        mocker.patch("src.mk_cats.mknew.filter_cat", return_value=True)
        mock_resolver = MagicMock(return_value="علوم")
        mocker.patch("src.mk_cats.mknew.resolve_arabic_category_label", mock_resolver)

        from src.mk_cats.mknew import ar_make_lab

        result = ar_make_lab("Category:Science")

        assert result == "علوم"


class TestScanArTitle:
    """Tests for scan_ar_title function."""

    def test_returns_false_for_already_created(self, mocker):
        """Test that scan_ar_title returns False for already created titles."""
        from src.mk_cats import mknew

        # Add title to _already_created
        mknew._already_created.clear()
        mknew._already_created.append("تصنيف:علوم")

        result = mknew.scan_ar_title("تصنيف:علوم")

        assert result is False

        # Cleanup
        mknew._already_created.clear()

    def test_returns_true_for_new_title(self, mocker):
        """Test that scan_ar_title returns True for new titles."""
        from src.mk_cats import mknew

        # Clear state
        mknew._already_created.clear()
        mknew._new_cat_done.clear()

        result = mknew.scan_ar_title("تصنيف:جديد")

        assert result is True

        # Cleanup
        mknew._already_created.clear()
        mknew._new_cat_done.clear()

    def test_tracks_title_in_newcat_done(self, mocker):
        """Test that scan_ar_title tracks title in NewCat_Done."""
        from src.mk_cats import mknew

        # Clear state
        mknew._already_created.clear()
        mknew._new_cat_done.clear()

        mknew.scan_ar_title("تصنيف:اختبار")

        assert "تصنيف:اختبار" in mknew._new_cat_done

        # Cleanup
        mknew._new_cat_done.clear()


class TestMakeAr:
    """Tests for make_ar function."""

    def test_returns_empty_list_for_empty_ar_title(self):
        """Test that make_ar returns empty list for empty Arabic title."""
        from src.mk_cats.mknew import make_ar

        result = make_ar("Category:Science", "")

        assert result == []

    def test_returns_empty_list_for_whitespace_ar_title(self):
        """Test that make_ar returns empty list for whitespace Arabic title."""
        from src.mk_cats.mknew import make_ar

        result = make_ar("Category:Science", "   ")

        assert result == []

    def test_cleans_en_page_title(self, mocker):
        """Test that make_ar cleans the English page title."""
        from src.mk_cats import mknew

        # Clear state
        mknew._already_created.clear()
        mknew._new_cat_done.clear()

        # Mock all external calls
        mocker.patch.object(mknew, "scan_ar_title", return_value=False)

        result = mknew.make_ar("[[Category:Science]]", "علوم")

        assert result == []

        # Cleanup
        mknew._already_created.clear()
        mknew._new_cat_done.clear()

    def test_returns_empty_when_ar_exists_in_wikidata(self, mocker):
        """Test that make_ar returns empty when Arabic link exists in Wikidata."""
        from src.mk_cats import mknew

        # Clear state
        mknew._already_created.clear()
        mknew._new_cat_done.clear()

        mocker.patch.object(mknew, "scan_ar_title", return_value=True)
        mocker.patch.object(mknew, "check_if_artitle_exists", return_value=True)
        mocker.patch(
            "src.mk_cats.mknew.Get_Sitelinks_From_wikidata",
            return_value={"sitelinks": {"arwiki": "علوم"}, "q": "Q12345"},
        )

        result = mknew.make_ar("Category:Science", "علوم")

        assert result == []

        # Cleanup
        mknew._already_created.clear()
        mknew._new_cat_done.clear()


class TestProcessCatagories:
    """Tests for process_catagories function."""

    def test_calls_make_ar_with_correct_params(self, mocker):
        """Test that process_catagories calls make_ar with correct parameters."""
        mock_make_ar = mocker.patch("src.mk_cats.mknew.make_ar", return_value=[])

        from src.mk_cats.mknew import process_catagories

        process_catagories("Category:Science", "علوم", 1, 10)

        mock_make_ar.assert_called_once()
        args = mock_make_ar.call_args[0]
        assert args[0] == "Category:Science"
        assert args[1] == "علوم"

    def test_handles_empty_make_ar_result(self, mocker):
        """Test that process_catagories handles empty make_ar result."""
        mocker.patch("src.mk_cats.mknew.make_ar", return_value=[])

        from src.mk_cats.mknew import process_catagories

        # Should not raise any exceptions
        result = process_catagories("Category:Science", "علوم", 1, 10)

        assert result is None

    def test_iterates_over_subcategories(self, mocker):
        """Test that process_catagories iterates over subcategories."""
        from src.mk_cats import mknew

        # First call returns subcategories, second call returns empty
        mock_make_ar = mocker.patch.object(mknew, "make_ar", side_effect=[["SubCat1"], []])
        mocker.patch.object(mknew, "ar_make_lab", return_value="")
        mocker.patch("src.mk_cats.mknew.get_ar_list_from_en", return_value=[])

        mknew.process_catagories("Category:Science", "علوم", 1, 10)

        assert mock_make_ar.call_count >= 1

    def test_passes_callback(self, mocker):
        """Test that process_catagories passes callback to make_ar."""
        mock_make_ar = mocker.patch("src.mk_cats.mknew.make_ar", return_value=[])

        from src.mk_cats.mknew import process_catagories

        callback = MagicMock()
        process_catagories("Category:Science", "علوم", 1, 10, callback=callback)

        call_kwargs = mock_make_ar.call_args[1]
        assert call_kwargs["callback"] == callback


class TestOneCat:
    """Tests for one_cat function."""

    def test_returns_false_for_empty_title(self):
        """Test that one_cat returns False for empty title."""
        from src.mk_cats.mknew import one_cat

        result = one_cat("", 1, 1)

        assert result is False

    def test_returns_false_for_whitespace_title(self):
        """Test that one_cat returns False for whitespace title."""
        from src.mk_cats.mknew import one_cat

        result = one_cat("   ", 1, 1)

        assert result is False

    def test_returns_false_for_duplicate_title(self, mocker):
        """Test that one_cat returns False for duplicate title."""
        from src.mk_cats import mknew

        # Clear and add to _done_d
        mknew._done_d.clear()
        mknew._done_d.append("Category:Duplicate")

        result = mknew.one_cat("Category:Duplicate", 1, 1)

        assert result is False

        # Cleanup
        mknew._done_d.clear()

    def test_returns_false_when_no_label(self, mocker):
        """Test that one_cat returns False when no Arabic label is found."""
        from src.mk_cats import mknew

        # Clear state
        mknew._done_d.clear()

        mocker.patch.object(mknew, "ar_make_lab", return_value="")

        result = mknew.one_cat("Category:NoLabel", 1, 1)

        assert result is False

        # Cleanup
        mknew._done_d.clear()

    def test_returns_false_when_check_en_temps_fails(self, mocker):
        """Test that one_cat returns False when check_en_temps fails."""
        from src.mk_cats import mknew

        # Clear state
        mknew._done_d.clear()

        mocker.patch.object(mknew, "ar_make_lab", return_value="علوم")
        mocker.patch("src.mk_cats.mknew.check_en_temps", return_value=False)

        result = mknew.one_cat("Category:Science", 1, 1)

        assert result is False

        # Cleanup
        mknew._done_d.clear()

    def test_returns_false_when_no_en_list(self, mocker):
        """Test that one_cat returns False when no English list."""
        from src.mk_cats import mknew

        # Clear state
        mknew._done_d.clear()

        mocker.patch.object(mknew, "ar_make_lab", return_value="علوم")
        mocker.patch("src.mk_cats.mknew.check_en_temps", return_value=True)
        mocker.patch("src.mk_cats.mknew.get_ar_list_from_en", return_value=[])

        result = mknew.one_cat("Category:Science", 1, 1)

        assert result is False

        # Cleanup
        mknew._done_d.clear()

    def test_uses_sugust_when_no_label(self, mocker):
        """Test that one_cat uses sugust parameter when no label found."""
        from src.mk_cats import mknew

        # Clear state
        mknew._done_d.clear()

        mocker.patch.object(mknew, "ar_make_lab", return_value="")
        mocker.patch("src.mk_cats.mknew.check_en_temps", return_value=True)
        mocker.patch("src.mk_cats.mknew.get_ar_list_from_en", return_value=["Article1"])
        mock_process = mocker.patch.object(mknew, "process_catagories")

        mknew.one_cat("Category:Science", 1, 1, sugust="علوم مقترحة")

        mock_process.assert_called_once()
        args = mock_process.call_args[0]
        assert args[1] == "علوم مقترحة"

        # Cleanup
        mknew._done_d.clear()


class TestCreateCategoriesFromList:
    """Tests for create_categories_from_list function."""

    def test_handles_empty_list(self):
        """Test that create_categories_from_list handles empty list."""
        from src.mk_cats.mknew import create_categories_from_list

        # Should not raise any exceptions
        create_categories_from_list([])

    def test_calls_one_cat_for_each_item(self, mocker):
        """Test that create_categories_from_list calls one_cat for each item."""
        mock_one_cat = mocker.patch("src.mk_cats.mknew.one_cat")

        from src.mk_cats.mknew import create_categories_from_list

        categories = ["Cat1", "Cat2", "Cat3"]
        create_categories_from_list(categories)

        assert mock_one_cat.call_count == 3

    def test_passes_correct_num_and_lenth(self, mocker):
        """Test that create_categories_from_list passes correct num and lenth."""
        mock_one_cat = mocker.patch("src.mk_cats.mknew.one_cat")

        from src.mk_cats.mknew import create_categories_from_list

        categories = ["Cat1", "Cat2"]
        create_categories_from_list(categories)

        # First call should be (Cat1, 1, 2, ...)
        first_call_args = mock_one_cat.call_args_list[0][0]
        assert first_call_args[1] == 1  # num
        assert first_call_args[2] == 2  # lenth

        # Second call should be (Cat2, 2, 2, ...)
        second_call_args = mock_one_cat.call_args_list[1][0]
        assert second_call_args[1] == 2  # num
        assert second_call_args[2] == 2  # lenth

    def test_passes_callback_to_one_cat(self, mocker):
        """Test that create_categories_from_list passes callback to one_cat."""
        mock_one_cat = mocker.patch("src.mk_cats.mknew.one_cat")

        from src.mk_cats.mknew import create_categories_from_list

        callback = MagicMock()
        create_categories_from_list(["Cat1"], callback=callback)

        call_kwargs = mock_one_cat.call_args[1]
        assert call_kwargs["callback"] == callback


class TestMakeArMinMembers:
    """Tests for minimum members check in make_ar function."""

    def test_returns_empty_when_below_min_members(self, mocker):
        """Test that make_ar returns empty list when members below min_members."""
        from src.mk_cats import mknew

        # Clear state
        mknew._already_created.clear()
        mknew._new_cat_done.clear()

        mocker.patch.object(mknew, "scan_ar_title", return_value=True)
        mocker.patch.object(mknew, "check_if_artitle_exists", return_value=True)
        mocker.patch("src.mk_cats.mknew.Get_Sitelinks_From_wikidata", return_value={"q": "Q12345"})
        mocker.patch("src.mk_cats.mknew.find_Page_Cat_without_hidden", return_value={})
        # Return only 3 members (below default min_members of 5)
        mocker.patch("src.mk_cats.mknew.collect_category_members", return_value=["Article1", "Article2", "Article3"])
        mock_settings = mocker.patch("src.mk_cats.mknew.settings")
        mock_settings.category.min_members = 5

        result = mknew.make_ar("Category:Science", "علوم")

        assert result == []

        # Cleanup
        mknew._already_created.clear()
        mknew._new_cat_done.clear()

    def test_proceeds_when_at_min_members(self, mocker):
        """Test that make_ar proceeds when members equals min_members."""
        from src.mk_cats import mknew

        # Clear state
        mknew._already_created.clear()
        mknew._new_cat_done.clear()

        mocker.patch.object(mknew, "scan_ar_title", return_value=True)
        mocker.patch.object(mknew, "check_if_artitle_exists", return_value=True)
        mocker.patch("src.mk_cats.mknew.Get_Sitelinks_From_wikidata", return_value={"q": "Q12345"})
        mocker.patch("src.mk_cats.mknew.find_Page_Cat_without_hidden", return_value={})
        # Return exactly 5 members (equals default min_members)
        mocker.patch(
            "src.mk_cats.mknew.collect_category_members",
            return_value=["Article1", "Article2", "Article3", "Article4", "Article5"],
        )
        mock_settings = mocker.patch("src.mk_cats.mknew.settings")
        mock_settings.category.min_members = 5
        mock_settings.range_limit = 5
        from src.mk_cats.create_category_page import CategoryResult

        mock_new_category = mocker.patch(
            "src.mk_cats.mknew.new_category", return_value=CategoryResult(True, "تصنيف:علوم", None)
        )
        mocker.patch("src.mk_cats.mknew.add_to_final_list")
        mocker.patch("src.mk_cats.mknew.validate_categories_for_new_cat", return_value=False)
        mocker.patch("src.mk_cats.mknew.log_to_wikidata")

        result = mknew.make_ar("Category:Science", "علوم")

        # Should have proceeded to create the category
        mock_new_category.assert_called_once()

        # Cleanup
        mknew._already_created.clear()
        mknew._new_cat_done.clear()

    def test_proceeds_when_above_min_members(self, mocker):
        """Test that make_ar proceeds when members above min_members."""
        from src.mk_cats import mknew

        # Clear state
        mknew._already_created.clear()
        mknew._new_cat_done.clear()

        mocker.patch.object(mknew, "scan_ar_title", return_value=True)
        mocker.patch.object(mknew, "check_if_artitle_exists", return_value=True)
        mocker.patch("src.mk_cats.mknew.Get_Sitelinks_From_wikidata", return_value={"q": "Q12345"})
        mocker.patch("src.mk_cats.mknew.find_Page_Cat_without_hidden", return_value={})
        # Return 10 members (above default min_members of 5)
        mocker.patch(
            "src.mk_cats.mknew.collect_category_members",
            return_value=["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10"],
        )
        mock_settings = mocker.patch("src.mk_cats.mknew.settings")
        mock_settings.category.min_members = 5
        mock_settings.range_limit = 5
        from src.mk_cats.create_category_page import CategoryResult

        mock_new_category = mocker.patch(
            "src.mk_cats.mknew.new_category", return_value=CategoryResult(True, "تصنيف:علوم", None)
        )
        mocker.patch("src.mk_cats.mknew.add_to_final_list")
        mocker.patch("src.mk_cats.mknew.validate_categories_for_new_cat", return_value=False)
        mocker.patch("src.mk_cats.mknew.log_to_wikidata")

        result = mknew.make_ar("Category:Science", "علوم")

        # Should have proceeded to create the category
        mock_new_category.assert_called_once()

        # Cleanup
        mknew._already_created.clear()
        mknew._new_cat_done.clear()

    def test_custom_min_members_value(self, mocker):
        """Test that make_ar respects custom min_members value."""
        from src.mk_cats import mknew

        # Clear state
        mknew._already_created.clear()
        mknew._new_cat_done.clear()

        mocker.patch.object(mknew, "scan_ar_title", return_value=True)
        mocker.patch.object(mknew, "check_if_artitle_exists", return_value=True)
        mocker.patch("src.mk_cats.mknew.Get_Sitelinks_From_wikidata", return_value={"q": "Q12345"})
        mocker.patch("src.mk_cats.mknew.find_Page_Cat_without_hidden", return_value={})
        # Return 7 members
        mocker.patch(
            "src.mk_cats.mknew.collect_category_members", return_value=["A1", "A2", "A3", "A4", "A5", "A6", "A7"]
        )
        mock_settings = mocker.patch("src.mk_cats.mknew.settings")
        mock_settings.category.min_members = 10  # Custom value higher than 7
        mock_settings.range_limit = 5

        result = mknew.make_ar("Category:Science", "علوم")

        # Should return empty list because 7 < 10
        assert result == []

        # Cleanup
        mknew._already_created.clear()
        mknew._new_cat_done.clear()

    def test_min_members_zero_allows_any(self, mocker):
        """Test that min_members of 0 allows any number of members."""
        from src.mk_cats import mknew

        # Clear state
        mknew._already_created.clear()
        mknew._new_cat_done.clear()

        mocker.patch.object(mknew, "scan_ar_title", return_value=True)
        mocker.patch.object(mknew, "check_if_artitle_exists", return_value=True)
        mocker.patch("src.mk_cats.mknew.Get_Sitelinks_From_wikidata", return_value={"q": "Q12345"})
        mocker.patch("src.mk_cats.mknew.find_Page_Cat_without_hidden", return_value={})
        # Return only 1 member
        mocker.patch("src.mk_cats.mknew.collect_category_members", return_value=["Article1"])
        mock_settings = mocker.patch("src.mk_cats.mknew.settings")
        mock_settings.category.min_members = 0  # Allow any
        mock_settings.range_limit = 5
        from src.mk_cats.create_category_page import CategoryResult

        mock_new_category = mocker.patch(
            "src.mk_cats.mknew.new_category", return_value=CategoryResult(True, "تصنيف:علوم", None)
        )
        mocker.patch("src.mk_cats.mknew.add_to_final_list")
        mocker.patch("src.mk_cats.mknew.validate_categories_for_new_cat", return_value=False)
        mocker.patch("src.mk_cats.mknew.log_to_wikidata")

        result = mknew.make_ar("Category:Science", "علوم")

        # Should have proceeded to create the category
        mock_new_category.assert_called_once()

        # Cleanup
        mknew._already_created.clear()
        mknew._new_cat_done.clear()
