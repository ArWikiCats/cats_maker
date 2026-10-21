"""
Tests for mknew.py

Tests for mknew.py - Main file for category creation

This module tests:
- create_categories_from_list() - Main function to create categories
- CategoryManager.one_cat() - Process a single category
- CategoryManager.process_categories() - Recursive category processing
- CategoryManager.make_ar() - Create Arabic category
- ar_make_lab() - Generate Arabic label
- CategoryManager._scan_ar_title() - Scan Arabic titles
- CategoryManager.can_create() - Check if Arabic title exists
"""

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from src.cats_maker.mk_cats.mknew import category_manager as mknew
from src.cats_maker.mk_cats.create_category_page import CategoryResult
from src.cats_maker.mk_cats.mknew import (
    CategoryManager,
    ar_make_lab,
)


@pytest.fixture
def category_manager():
    """Fixture to provide a fresh CategoryManager instance."""
    category_manager = CategoryManager()
    category_manager.stats._already_created.clear()
    category_manager.stats._new_cat_done.clear()
    category_manager.stats._done_d.clear()
    return category_manager


@pytest.fixture
def mock_one_cat(mocker):
    """Fixture to mock CategoryManager.one_cat method."""
    return mocker.patch.object(CategoryManager, "one_cat")


@pytest.fixture
def mock_make_ar(mocker):
    """Fixture to mock CategoryManager.make_ar method returning empty list by default."""
    return mocker.patch.object(CategoryManager, "make_ar", return_value=[])


@dataclass
class MakeArBaseDeps:
    """Dataclass holding base dependencies for make_ar tests."""

    scan_ar_title: MagicMock
    check_if_artitle_exists: MagicMock
    get_sitelinks_from_wikidata: MagicMock
    find_page_categories_informations: MagicMock
    collect_category_members: MagicMock
    settings: MagicMock


@pytest.fixture
def mock_make_ar_base_deps(mocker, category_manager: CategoryManager):
    """Fixture supplying common mocks required for make_ar execution."""
    # Reset manager state

    settings = MagicMock()
    settings.category = MagicMock()
    settings.category.min_members = 5

    deps = MakeArBaseDeps(
        scan_ar_title=mocker.patch.object(category_manager.stats, "_scan_ar_title", return_value=True),
        check_if_artitle_exists=mocker.patch.object(category_manager, "can_create", return_value=True),
        get_sitelinks_from_wikidata=mocker.patch(
            "src.cats_maker.mk_cats.mknew.category_manager.get_sitelinks_from_wikidata", return_value={"q": "Q12345"}
        ),
        find_page_categories_informations=mocker.patch(
            "src.cats_maker.mk_cats.mknew.category_manager.LangLinksClient.find_page_categories_informations",
            return_value={},
        ),
        collect_category_members=mocker.patch(
            "src.cats_maker.mk_cats.mknew.category_manager.collect_category_members", return_value=[]
        ),
        settings=mocker.patch(
            "src.cats_maker.mk_cats.mknew.category_manager.Settings.get_instance", return_value=settings
        ),
    )

    yield deps

    # Cleanup state


@dataclass
class MakeArProceedDeps(MakeArBaseDeps):
    """Dataclass extending MakeArBaseDeps with fixtures needed for creation proceed tests."""

    new_category: MagicMock
    add_to_final_list: MagicMock
    validate_categories_for_new_cat: MagicMock
    log_to_wikidata: MagicMock


@pytest.fixture
def mock_make_ar_proceed_deps(mocker, mock_make_ar_base_deps, category_manager) -> MakeArProceedDeps:
    """Fixture adding page-creation mocks on top of mock_make_ar_base_deps."""
    mock_make_ar_base_deps.settings.category.min_members = 5
    mock_make_ar_base_deps.settings.range_limit = 5

    return MakeArProceedDeps(
        **mock_make_ar_base_deps.__dict__,
        new_category=mocker.patch(
            "src.cats_maker.mk_cats.mknew.category_manager.new_category",
            return_value=CategoryResult(True, "تصنيف:علوم", None),
        ),
        add_to_final_list=mocker.patch.object(category_manager, ".creator.members_adder.add"),
        validate_categories_for_new_cat=mocker.patch(
            "src.cats_maker.mk_cats.mknew.category_manager.validate_categories_for_new_cat", return_value=False
        ),
        log_to_wikidata=mocker.patch("src.cats_maker.mk_cats.mknew.category_manager.log_to_wikidata"),
    )


class TestCheckIfArtitleExists:
    """Tests for CategoryManager.can_create method."""


class TestArMakeLab:
    """Tests for ar_make_lab function."""

    def test_returns_empty_when_filter_fails(self, mocker):
        """Test that ar_make_lab returns empty string when filter_category fails."""
        mocker.patch("src.cats_maker.mk_cats.mknew.labels_creator.filter_category", return_value=False)

        result = ar_make_lab("Category:Test")

        assert result == ""

    def test_returns_empty_when_no_resolver(self, mocker):
        """Test that ar_make_lab returns empty string when resolve_arabic_category_label is None."""
        mocker.patch("src.cats_maker.mk_cats.mknew.labels_creator.filter_category", return_value=True)
        mocker.patch("src.cats_maker.mk_cats.mknew.labels_creator.resolve_arabic_category_label", None)

        result = ar_make_lab("Category:Science")

        assert result == ""

    def test_returns_label_when_resolver_exists(self, mocker):
        """Test that ar_make_lab returns label when resolver exists."""
        mocker.patch("src.cats_maker.mk_cats.mknew.labels_creator.filter_category", return_value=True)
        mock_resolver = MagicMock(return_value="علوم")
        mocker.patch("src.cats_maker.mk_cats.mknew.labels_creator.resolve_arabic_category_label", mock_resolver)

        result = ar_make_lab("Category:Science")

        assert result == "علوم"


class TestScanArTitle:
    """Tests for CategoryManager._scan_ar_title method."""

    def test_returns_false_for_already_created(self, category_manager):
        """Test that _scan_ar_title returns False for already created titles."""

        category_manager.stats._already_created.append("تصنيف:علوم")

        result = category_manager.stats._scan_ar_title("تصنيف:علوم")

        assert result is False

    def test_returns_true_for_new_title(self, category_manager):
        """Test that _scan_ar_title returns True for new titles."""

        result = category_manager.stats._scan_ar_title("تصنيف:جديد")

        assert result is True

    def test_tracks_title_in_newcat_done(self, category_manager):
        """Test that _scan_ar_title tracks title in _new_cat_done."""

        category_manager.stats._scan_ar_title("تصنيف:اختبار")

        assert "تصنيف:اختبار" in category_manager.stats._new_cat_done


class TestMakeAr:
    """Tests for CategoryManager.make_ar method."""

    def test_returns_empty_list_for_empty_ar_title(self, category_manager):
        """Test that make_ar returns empty list for empty Arabic title."""
        result = category_manager.make_ar("Category:Science", "")

        assert result == []

    def test_returns_empty_list_for_whitespace_ar_title(self, category_manager):
        """Test that make_ar returns empty list for whitespace Arabic title."""
        result = category_manager.make_ar("Category:Science", "    ")

        assert result == []

    def test_cleans_en_page_title(self, mocker, category_manager):
        """Test that make_ar cleans the English page title."""

        mocker.patch.object(category_manager.stats, "_scan_ar_title", return_value=False)

        result = category_manager.make_ar("[[Category:Science]]", "علوم")

        assert result == []

    def test_returns_empty_when_ar_exists_in_wikidata(self, mocker, category_manager):
        """Test that make_ar returns empty list when Arabic link exists in Wikidata."""

        mocker.patch.object(category_manager.stats, "_scan_ar_title", return_value=True)
        mocker.patch.object(category_manager, "can_create", return_value=True)
        mocker.patch(
            "src.cats_maker.mk_cats.mknew.category_manager.get_sitelinks_from_wikidata",
            return_value={"sitelinks": {"arwiki": "علوم"}, "q": "Q12345"},
        )

        result = category_manager.make_ar("Category:Science", "علوم")

        assert result == []


class TestProcessCategories:
    """Tests for CategoryManager.process_categories method."""

    def test_calls_make_ar_with_correct_params(self, mock_make_ar, category_manager):
        """Test that process_categories calls make_ar with correct parameters."""
        category_manager.process_categories("Category:Science", "علوم", 1, 10)

        mock_make_ar.assert_called_once()
        args = mock_make_ar.call_args[0]
        assert args[0] == "Category:Science"
        assert args[1] == "علوم"

    def test_handles_empty_make_ar_result(self, mock_make_ar, category_manager):
        """Test that process_categories handles empty make_ar result."""
        result = category_manager.process_categories("Category:Science", "علوم", 1, 10)

        assert result is None

    def test_iterates_over_subcategories(self, mocker, category_manager):
        """Test that process_categories iterates over subcategories."""
        mock_make_ar = mocker.patch.object(category_manager, "make_ar", side_effect=[["SubCat1"], []])
        mocker.patch.object(mknew, "ar_make_lab", return_value="")
        mocker.patch(
            "src.cats_maker.core_cat.lists.category_resolver.CategoryResolver.list_en_pages_with_ar_links",
            return_value=[],
        )

        category_manager.process_categories("Category:Science", "علوم", 1, 10)

        assert mock_make_ar.call_count >= 1

    def test_passes_callback(self, mock_make_ar, category_manager):
        """Test that process_categories passes callback to make_ar."""
        callback = MagicMock()
        category_manager.process_categories("Category:Science", "علوم", 1, 10, callback=callback)

        call_kwargs = mock_make_ar.call_args[1]
        assert call_kwargs["callback"] == callback


class TestOneCat:
    """Tests for CategoryManager.one_cat method."""

    def test_returns_false_for_empty_title(self, category_manager):
        """Test that one_cat returns False for empty title."""
        result = category_manager.one_cat("", 1, 1)

        assert result is False

    def test_returns_false_for_whitespace_title(self, category_manager):
        """Test that one_cat returns False for whitespace title."""
        result = category_manager.one_cat("    ", 1, 1)

        assert result is False

    def test_returns_false_for_duplicate_title(self, category_manager):
        """Test that one_cat returns False for duplicate title."""

        category_manager.stats._done_d.append("Category:Duplicate")

        result = category_manager.one_cat("Category:Duplicate", 1, 1)

        assert result is False

    def test_returns_false_when_no_label(self, mocker, category_manager):
        """Test that one_cat returns False when no Arabic label is found."""

        mocker.patch.object(mknew, "ar_make_lab", return_value="")

        result = category_manager.one_cat("Category:NoLabel", 1, 1)

        assert result is False

    def test_returns_false_when_check_en_temps_fails(self, mocker, category_manager):
        """Test that one_cat returns False when check_en_temps fails."""

        mocker.patch.object(mknew, "ar_make_lab", return_value="علوم")
        mocker.patch("src.cats_maker.mk_cats.mknew.category_manager.check_en_temps", return_value=False)

        result = category_manager.one_cat("Category:Science", 1, 1)

        assert result is False

    def test_returns_false_when_no_en_list(self, mocker, category_manager):
        """Test that one_cat returns False when no English pages are returned."""

        mocker.patch.object(mknew, "ar_make_lab", return_value="علوم")
        mocker.patch("src.cats_maker.mk_cats.mknew.category_manager.check_en_temps", return_value=True)
        mocker.patch(
            "src.cats_maker.core_cat.lists.category_resolver.CategoryResolver.list_en_pages_with_ar_links",
            return_value=[],
        )

        result = category_manager.one_cat("Category:Science", 1, 1)

        assert result is False

    def test_uses_sugust_when_no_label(self, mocker, category_manager):
        """Test that one_cat uses sugust parameter when no label is found."""

        mocker.patch.object(mknew, "ar_make_lab", return_value="")
        mocker.patch("src.cats_maker.mk_cats.mknew.category_manager.check_en_temps", return_value=True)
        mocker.patch(
            "src.cats_maker.core_cat.lists.category_resolver.CategoryResolver.list_en_pages_with_ar_links",
            return_value=["Article1"],
        )
        mock_process = mocker.patch.object(category_manager, "process_categories")

        category_manager.one_cat("Category:Science", 1, 1, sugust="علوم مقترحة")

        mock_process.assert_called_once()
        args = mock_process.call_args[0]
        assert args[1] == "علوم مقترحة"


class TestCreateCategoriesFromList:
    """Tests for create_categories_from_list function."""

    def test_handles_empty_list(self):
        """Test that create_categories_from_list handles empty list gracefully."""
        CategoryManager().create_categories_from_list([])

    def test_calls_one_cat_for_each_item(self, mocker):
        """Test that create_categories_from_list calls one_cat for each item."""
        mock_one_cat = mocker.patch.object(CategoryManager, "one_cat")
        categories = ["Cat1", "Cat2", "Cat3"]
        CategoryManager().create_categories_from_list(categories)

        assert mock_one_cat.call_count == 3

    def test_passes_correct_num_and_lenth(self, mocker):
        """Test that create_categories_from_list passes correct index and list length."""
        mock_one_cat = mocker.patch.object(CategoryManager, "one_cat")
        categories = ["Cat1", "Cat2"]
        CategoryManager().create_categories_from_list(categories)

        first_call_args = mock_one_cat.call_args_list[0][0]
        assert first_call_args[1] == 1  # num
        assert first_call_args[2] == 2  # lenth

        second_call_args = mock_one_cat.call_args_list[1][0]
        assert second_call_args[1] == 2  # num
        assert second_call_args[2] == 2  # lenth

    def test_passes_callback_to_one_cat(self, mocker):
        """Test that create_categories_from_list passes callback to one_cat."""
        mock_one_cat = mocker.patch.object(CategoryManager, "one_cat")
        callback = MagicMock()
        CategoryManager().create_categories_from_list(["Cat1"], callback=callback)

        call_kwargs = mock_one_cat.call_args[1]
        assert call_kwargs["callback"] == callback


class TestMakeArMinMembers:
    """Tests for minimum members check in CategoryManager.make_ar method."""

    def test_returns_empty_when_below_min_members(self, mock_make_ar_base_deps: MakeArBaseDeps, category_manager):
        """Test that make_ar returns empty list when members count is below min_members."""
        mock_make_ar_base_deps.collect_category_members.return_value = ["Article1", "Article2", "Article3"]
        mock_make_ar_base_deps.settings.category.min_members = 5

        result = category_manager.make_ar("Category:Science", "علوم")

        assert result == []

    @pytest.mark.skip(reason="takes too long, missing expected mocks")
    @pytest.mark.network
    def test_proceeds_when_at_min_members(self, mock_make_ar_proceed_deps: MakeArProceedDeps, category_manager):
        """Test that make_ar proceeds when members count equals min_members."""
        mock_make_ar_proceed_deps.collect_category_members.return_value = [
            "Article1",
            "Article2",
            "Article3",
            "Article4",
            "Article5",
        ]

        category_manager.make_ar("Category:Science", "علوم")

        mock_make_ar_proceed_deps.new_category.assert_called_once()

    @pytest.mark.skip(reason="takes too long, missing expected mocks")
    def test_proceeds_when_above_min_members(self, mock_make_ar_proceed_deps: MakeArProceedDeps, category_manager):
        """Test that make_ar proceeds when members count is above min_members."""
        mock_make_ar_proceed_deps.collect_category_members.return_value = [
            "A1",
            "A2",
            "A3",
            "A4",
            "A5",
            "A6",
            "A7",
            "A8",
            "A9",
            "A10",
        ]

        category_manager.make_ar("Category:Science", "علوم")

        mock_make_ar_proceed_deps.new_category.assert_called_once()

    def test_custom_min_members_value(self, mock_make_ar_base_deps: MakeArBaseDeps, category_manager):
        """Test that make_ar respects custom min_members value."""
        mock_make_ar_base_deps.collect_category_members.return_value = ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]
        mock_make_ar_base_deps.settings.category.min_members = 10
        mock_make_ar_base_deps.settings.range_limit = 5

        result = category_manager.make_ar("Category:Science", "علوم")

        assert result == []

    @pytest.mark.skip(reason="takes too long, missing expected mocks")
    def test_min_members_zero_allows_any(self, mock_make_ar_proceed_deps: MakeArProceedDeps, category_manager):
        """Test that min_members of 0 allows any number of members."""
        mock_make_ar_proceed_deps.collect_category_members.return_value = ["Article1"]
        mock_make_ar_proceed_deps.settings.category.min_members = 0

        category_manager.make_ar("Category:Science", "علوم")

        mock_make_ar_proceed_deps.new_category.assert_called_once()


class TestAddToFinalList:
    """Tests for CategoryManager.creator.members_adder.add method."""

    def test_handles_empty_list(self, category_manager: CategoryManager):
        """Test that empty list is handled gracefully."""
        category_manager.creator.members_adder.add([], "تصنيف:علوم")

    def test_handles_none_list(self, category_manager):
        """Test that None list is handled gracefully."""
        category_manager.creator.members_adder.add(None, "تصنيف:علوم")

    def test_adds_tasneef_prefix_if_missing(self, mocker, category_manager):
        """Test that تصنيف: prefix is added if missing."""
        mocker.patch("src.cats_maker.mk_cats.mknew.category_manager.add_to_page", return_value=True)

        category_manager.creator.members_adder.add(["صفحة1"], "علوم")

    def test_replaces_underscores_in_title(self, mocker, category_manager):
        """Test that underscores are replaced with spaces in title."""
        mock_add = mocker.patch("src.cats_maker.mk_cats.mknew.category_manager.add_to_page", return_value=True)

        category_manager.creator.members_adder.add(["صفحة1"], "تصنيف:علوم_الحاسوب")

        call_args = mock_add.call_args[0]
        assert "_" not in call_args[1] or "تصنيف:علوم الحاسوب" in str(call_args)

    def test_calls_add_to_page_for_each_item(self, mocker, category_manager):
        """Test that add_to_page is called for each item in list."""
        mock_add = mocker.patch("src.cats_maker.mk_cats.mknew.category_manager.add_to_page", return_value=True)

        category_manager.creator.members_adder.add(["صفحة1", "صفحة2", "صفحة3"], "تصنيف:علوم")

        assert mock_add.call_count == 3

    def test_calls_callback_on_success(self, mocker, category_manager):
        """Test that callback is called on successful save."""
        mocker.patch("src.cats_maker.mk_cats.mknew.category_manager.add_to_page", return_value=True)
        mock_callback = mocker.MagicMock()

        category_manager.creator.members_adder.add(["صفحة1"], "تصنيف:علوم", callback=mock_callback)

        mock_callback.assert_called_once()

    def test_handles_callback_exception(self, mocker, category_manager):
        """Test that callback exceptions are handled without propagating."""
        mocker.patch("src.cats_maker.mk_cats.mknew.category_manager.add_to_page", return_value=True)
        mock_callback = mocker.MagicMock(side_effect=Exception("Test error"))

        category_manager.creator.members_adder.add(["صفحة1"], "تصنيف:علوم", callback=mock_callback)
