"""Tests for CategoryBatchProcessor (mknew_processor.py)."""

from unittest.mock import MagicMock

import pytest

from src.cats_maker.mk_cats.mknew.mknew_creator import CategoryCreator
from src.cats_maker.mk_cats.mknew.mknew_processor import CategoryBatchProcessor

MODULE = "src.cats_maker.mk_cats.mknew.mknew_processor"
LIST_EN_PAGES = "src.cats_maker.core_cat.lists.category_resolver.CategoryResolver.list_en_pages_with_ar_links"


@pytest.fixture
def mock_one_cat(mocker):
    """Fixture to mock CategoryBatchProcessor.one_cat method."""
    return mocker.patch.object(CategoryBatchProcessor, "one_cat")


@pytest.fixture
def mock_make_ar(mocker):
    """Fixture to mock CategoryCreator.make_ar method returning empty list by default."""
    return mocker.patch.object(CategoryCreator, "make_ar", return_value=[])


class TestProcessCategories:
    """Tests for CategoryBatchProcessor.process_categories method."""

    def test_calls_make_ar_with_correct_params(self, mock_make_ar, category_manager):
        """Test that process_categories calls make_ar with correct parameters."""
        category_manager.processor.process_categories("Category:Science", "علوم", 1, 10)

        mock_make_ar.assert_called_once()
        args = mock_make_ar.call_args[0]
        assert args[0] == "Category:Science"
        assert args[1] == "علوم"

    def test_handles_empty_make_ar_result(self, mock_make_ar, category_manager):
        """Test that process_categories handles empty make_ar result."""
        result = category_manager.processor.process_categories("Category:Science", "علوم", 1, 10)

        assert result is None

    def test_iterates_over_subcategories(self, mocker, category_manager):
        """Test that process_categories iterates over subcategories."""
        mock_make_ar = mocker.patch.object(category_manager.creator, "make_ar", side_effect=[["SubCat1"], []])
        mocker.patch(f"{MODULE}.ar_make_lab", return_value="")
        mocker.patch(LIST_EN_PAGES, return_value=[])

        category_manager.processor.process_categories("Category:Science", "علوم", 1, 10)

        assert mock_make_ar.call_count >= 1

    def test_creates_subcategory_that_has_label_and_pages(self, mocker, category_manager):
        """Test that a subcategory with an Arabic label and English pages is passed to make_ar."""
        mock_make_ar = mocker.patch.object(category_manager.creator, "make_ar", side_effect=[["SubCat1"], []])
        mocker.patch(f"{MODULE}.ar_make_lab", return_value="علوم فرعية")
        mocker.patch(LIST_EN_PAGES, return_value=["Article1"])

        category_manager.processor.process_categories("Category:Science", "علوم", 1, 10)

        assert mock_make_ar.call_count == 2
        assert mock_make_ar.call_args_list[1][0] == ("SubCat1", "علوم فرعية")

    def test_passes_callback(self, mock_make_ar, category_manager):
        """Test that process_categories passes callback to make_ar."""
        callback = MagicMock()
        category_manager.processor.process_categories("Category:Science", "علوم", 1, 10, callback=callback)

        call_kwargs = mock_make_ar.call_args[1]
        assert call_kwargs["callback"] == callback


class TestOneCat:
    """Tests for CategoryBatchProcessor.one_cat method."""

    def test_returns_false_for_empty_title(self, category_manager):
        """Test that one_cat returns False for empty title."""
        result = category_manager.processor.one_cat("", 1, 1)

        assert result is False

    def test_returns_false_for_whitespace_title(self, category_manager):
        """Test that one_cat returns False for whitespace title."""
        result = category_manager.processor.one_cat("    ", 1, 1)

        assert result is False

    def test_returns_false_for_duplicate_title(self, category_manager):
        """Test that one_cat returns False for duplicate title."""
        category_manager.stats._done_d.append("Category:Duplicate")

        result = category_manager.processor.one_cat("Category:Duplicate", 1, 1)

        assert result is False

    def test_returns_false_when_no_label(self, mocker, category_manager):
        """Test that one_cat returns False when no Arabic label is found."""
        mocker.patch(f"{MODULE}.ar_make_lab", return_value="")

        result = category_manager.processor.one_cat("Category:NoLabel", 1, 1)

        assert result is False

    def test_returns_false_when_check_en_temps_fails(self, mocker, category_manager):
        """Test that one_cat returns False when check_en_temps fails."""
        mocker.patch(f"{MODULE}.ar_make_lab", return_value="علوم")
        mocker.patch(f"{MODULE}.check_en_temps", return_value=False)

        result = category_manager.processor.one_cat("Category:Science", 1, 1)

        assert result is False

    def test_returns_false_when_no_en_list(self, mocker, category_manager):
        """Test that one_cat returns False when no English pages are returned."""
        mocker.patch(f"{MODULE}.ar_make_lab", return_value="علوم")
        mocker.patch(f"{MODULE}.check_en_temps", return_value=True)
        mocker.patch(LIST_EN_PAGES, return_value=[])

        result = category_manager.processor.one_cat("Category:Science", 1, 1)

        assert result is False

    def test_uses_sugust_when_no_label(self, mocker, category_manager):
        """Test that one_cat uses sugust parameter when no label is found."""
        mocker.patch(f"{MODULE}.ar_make_lab", return_value="")
        mocker.patch(f"{MODULE}.check_en_temps", return_value=True)
        mocker.patch(LIST_EN_PAGES, return_value=["Article1"])
        mock_process = mocker.patch.object(category_manager.processor, "process_categories")

        category_manager.processor.one_cat("Category:Science", 1, 1, sugust="علوم مقترحة")

        mock_process.assert_called_once()
        args = mock_process.call_args[0]
        assert args[1] == "علوم مقترحة"


class TestCreateCategoriesFromList:
    """Tests for CategoryBatchProcessor.create_categories_from_list method."""

    def test_handles_empty_list(self, category_manager):
        """Test that create_categories_from_list handles empty list gracefully."""
        category_manager.processor.create_categories_from_list([])

    def test_calls_one_cat_for_each_item(self, mock_one_cat, category_manager):
        """Test that create_categories_from_list calls one_cat for each item."""
        category_manager.processor.create_categories_from_list(["Cat1", "Cat2", "Cat3"])

        assert mock_one_cat.call_count == 3

    def test_passes_correct_num_and_lenth(self, mock_one_cat, category_manager):
        """Test that create_categories_from_list passes correct index and list length."""
        category_manager.processor.create_categories_from_list(["Cat1", "Cat2"])

        first_call_args = mock_one_cat.call_args_list[0][0]
        assert first_call_args[1] == 1  # num
        assert first_call_args[2] == 2  # lenth

        second_call_args = mock_one_cat.call_args_list[1][0]
        assert second_call_args[1] == 2  # num
        assert second_call_args[2] == 2  # lenth

    def test_passes_callback_to_one_cat(self, mock_one_cat, category_manager):
        """Test that create_categories_from_list passes callback to one_cat."""
        callback = MagicMock()
        category_manager.processor.create_categories_from_list(["Cat1"], callback=callback)

        call_kwargs = mock_one_cat.call_args[1]
        assert call_kwargs["callback"] == callback
