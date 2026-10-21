"""Tests for CategoryCreator (mknew_creator.py) - the make_ar use case."""

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from src.cats_maker.mk_cats.create_category_page import CategoryResult

MODULE = "src.cats_maker.mk_cats.mknew"


@dataclass
class MakeArBaseDeps:
    """Dataclass holding base dependencies for make_ar tests."""

    scan_ar_title: MagicMock
    can_create: MagicMock
    get_sitelinks_from_wikidata: MagicMock
    find_page_categories_informations: MagicMock
    collect_members: MagicMock
    get_instance: MagicMock
    settings: MagicMock


@pytest.fixture
def mock_make_ar_base_deps(mocker, category_manager) -> MakeArBaseDeps:
    """Fixture supplying common mocks required for make_ar execution."""
    settings = MagicMock()
    settings.category = MagicMock()
    settings.category.min_members = 5

    return MakeArBaseDeps(
        scan_ar_title=mocker.patch.object(category_manager.stats, "_scan_ar_title", return_value=True),
        can_create=mocker.patch.object(category_manager.creator.arabic_checker, "can_create", return_value=True),
        get_sitelinks_from_wikidata=mocker.patch(
            f"{MODULE}.mknew_wikidata.get_sitelinks_from_wikidata", return_value={"q": "Q12345"}
        ),
        find_page_categories_informations=mocker.patch(
            f"{MODULE}.mknew_sources.LangLinksClient.find_page_categories_informations",
            return_value={},
        ),
        collect_members=mocker.patch(f"{MODULE}.mknew_creator.CategoryMemberCollector.collect", return_value=[]),
        get_instance=mocker.patch(f"{MODULE}.mknew_creator.Settings.get_instance", return_value=settings),
        settings=settings,
    )


@dataclass
class MakeArProceedDeps(MakeArBaseDeps):
    """Dataclass extending MakeArBaseDeps with fixtures needed for creation proceed tests."""

    new_category: MagicMock
    add_members: MagicMock
    validate_categories_for_new_cat: MagicMock
    log_to_wikidata_qid: MagicMock
    log_to_wikidata: MagicMock


@pytest.fixture
def mock_make_ar_proceed_deps(mocker, mock_make_ar_base_deps, category_manager) -> MakeArProceedDeps:
    """Fixture adding page-creation mocks on top of mock_make_ar_base_deps."""
    mock_make_ar_base_deps.settings.category.min_members = 5
    mock_make_ar_base_deps.settings.range_limit = 5

    return MakeArProceedDeps(
        **mock_make_ar_base_deps.__dict__,
        new_category=mocker.patch(
            f"{MODULE}.mknew_creator.new_category",
            return_value=CategoryResult(True, "تصنيف:علوم", None),
        ),
        add_members=mocker.patch.object(category_manager.creator.members_adder, "add"),
        validate_categories_for_new_cat=mocker.patch(
            f"{MODULE}.mknew_creator.CategoryValidator.validate_categories_for_new_cat", return_value=False
        ),
        log_to_wikidata_qid=mocker.patch(f"{MODULE}.mknew_wikidata.log_to_wikidata_qid"),
        log_to_wikidata=mocker.patch(f"{MODULE}.mknew_wikidata.log_to_wikidata"),
    )


class TestMakeAr:
    """Tests for CategoryCreator.make_ar method."""

    def test_returns_empty_list_for_empty_ar_title(self, category_manager):
        """Test that make_ar returns empty list for empty Arabic title."""
        result = category_manager.creator.make_ar("Category:Science", "")

        assert result == []

    def test_returns_empty_list_for_whitespace_ar_title(self, category_manager):
        """Test that make_ar returns empty list for whitespace Arabic title."""
        result = category_manager.creator.make_ar("Category:Science", "    ")

        assert result == []

    def test_cleans_en_page_title(self, mocker, category_manager):
        """Test that make_ar cleans the English page title."""
        mocker.patch.object(category_manager.stats, "_scan_ar_title", return_value=False)

        result = category_manager.creator.make_ar("[[Category:Science]]", "علوم")

        assert result == []

    def test_returns_empty_when_ar_exists_in_wikidata(self, mocker, category_manager):
        """Test that make_ar returns empty list when Arabic link exists in Wikidata."""
        mocker.patch.object(category_manager.stats, "_scan_ar_title", return_value=True)
        mocker.patch.object(category_manager.creator.arabic_checker, "can_create", return_value=True)
        mocker.patch(
            f"{MODULE}.mknew_wikidata.get_sitelinks_from_wikidata",
            return_value={"sitelinks": {"arwiki": "علوم"}, "q": "Q12345"},
        )

        result = category_manager.creator.make_ar("Category:Science", "علوم")

        assert result == []

    def test_returns_empty_when_arabic_category_exists(self, mock_make_ar_base_deps, category_manager):
        """Test that make_ar returns empty list when the Arabic category already exists."""
        mock_make_ar_base_deps.can_create.return_value = False

        result = category_manager.creator.make_ar("Category:Science", "علوم")

        assert result == []
        mock_make_ar_base_deps.get_sitelinks_from_wikidata.assert_not_called()


class TestMakeArMinMembers:
    """Tests for minimum members check in CategoryCreator.make_ar method."""

    def test_returns_empty_when_below_min_members(self, mock_make_ar_base_deps: MakeArBaseDeps, category_manager):
        """Test that make_ar returns empty list when members count is below min_members."""
        mock_make_ar_base_deps.collect_members.return_value = ["Article1", "Article2", "Article3"]
        mock_make_ar_base_deps.settings.category.min_members = 5

        result = category_manager.creator.make_ar("Category:Science", "علوم")

        assert result == []

    @pytest.mark.skip(reason="takes too long, missing expected mocks")
    @pytest.mark.network
    def test_proceeds_when_at_min_members(self, mock_make_ar_proceed_deps: MakeArProceedDeps, category_manager):
        """Test that make_ar proceeds when members count equals min_members."""
        mock_make_ar_proceed_deps.collect_members.return_value = [
            "Article1",
            "Article2",
            "Article3",
            "Article4",
            "Article5",
        ]

        category_manager.creator.make_ar("Category:Science", "علوم")

        mock_make_ar_proceed_deps.new_category.assert_called_once()

    @pytest.mark.skip(reason="takes too long, missing expected mocks")
    def test_proceeds_when_above_min_members(self, mock_make_ar_proceed_deps: MakeArProceedDeps, category_manager):
        """Test that make_ar proceeds when members count is above min_members."""
        mock_make_ar_proceed_deps.collect_members.return_value = [
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

        category_manager.creator.make_ar("Category:Science", "علوم")

        mock_make_ar_proceed_deps.new_category.assert_called_once()

    def test_custom_min_members_value(self, mock_make_ar_base_deps: MakeArBaseDeps, category_manager):
        """Test that make_ar respects custom min_members value."""
        mock_make_ar_base_deps.collect_members.return_value = ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]
        mock_make_ar_base_deps.settings.category.min_members = 10
        mock_make_ar_base_deps.settings.range_limit = 5

        result = category_manager.creator.make_ar("Category:Science", "علوم")

        assert result == []

    @pytest.mark.skip(reason="takes too long, missing expected mocks")
    def test_min_members_zero_allows_any(self, mock_make_ar_proceed_deps: MakeArProceedDeps, category_manager):
        """Test that min_members of 0 allows any number of members."""
        mock_make_ar_proceed_deps.collect_members.return_value = ["Article1"]
        mock_make_ar_proceed_deps.settings.category.min_members = 0

        category_manager.creator.make_ar("Category:Science", "علوم")

        mock_make_ar_proceed_deps.new_category.assert_called_once()


class TestMakeArCreation:
    """Tests for the category creation step of CategoryCreator.make_ar."""

    MEMBERS = ["Article1", "Article2", "Article3", "Article4", "Article5"]

    def test_adds_label_and_stops_when_creation_fails(self, mocker, mock_make_ar_proceed_deps, category_manager):
        """Test that a failed category creation only adds the Arabic label to Wikidata."""
        mock_make_ar_proceed_deps.collect_members.return_value = self.MEMBERS
        mock_make_ar_proceed_deps.new_category.return_value = CategoryResult(False, "تصنيف:علوم", None)
        mock_add_label = mocker.patch.object(category_manager.creator.wikidata, "add_arabic_label")

        result = category_manager.creator.make_ar("Category:Science", "علوم")

        assert result == []
        mock_add_label.assert_called_once_with("Q12345", "علوم")
        mock_make_ar_proceed_deps.add_members.assert_not_called()

    def test_adds_members_and_logs_when_creation_succeeds(self, mock_make_ar_proceed_deps, category_manager):
        """Test that a created category gets its members added and is logged to Wikidata."""
        mock_make_ar_proceed_deps.collect_members.return_value = self.MEMBERS

        result = category_manager.creator.make_ar("Category:Science", "علوم")

        assert result == []
        mock_make_ar_proceed_deps.add_members.assert_called_once_with(self.MEMBERS, "علوم", callback=None)
        mock_make_ar_proceed_deps.log_to_wikidata_qid.assert_called_once_with("علوم", "Q12345")


class TestFinalizeCategoryCreation:
    """Tests for CategoryCreator._finalize_category_creation method."""

    def test_adds_members_and_logs_to_wikidata(self, mocker, category_manager):
        """Test that members are added and the creation is logged."""
        creator = category_manager.creator
        mock_add = mocker.patch.object(creator.members_adder, "add")
        mock_log = mocker.patch.object(creator.wikidata, "log_creation")
        mocker.patch(f"{MODULE}.mknew_creator.validate_categories_for_new_cat", return_value=False)

        result = creator._finalize_category_creation(
            "تصنيف:علوم", "Category:Science", "Q1", ["A"], ["Category:X"], None
        )

        mock_add.assert_called_once_with(["A"], "تصنيف:علوم", callback=None)
        mock_log.assert_called_once_with("تصنيف:علوم", "Category:Science", "Q1")
        assert result == ["Category:X"]

    def test_adds_resolved_members_when_validation_passes(self, mocker, category_manager):
        """Test that members found by the resolver are added in a second pass."""
        creator = category_manager.creator
        mock_add = mocker.patch.object(creator.members_adder, "add")
        mocker.patch.object(creator.wikidata, "log_creation")
        mocker.patch(f"{MODULE}.mknew_creator.validate_categories_for_new_cat", return_value=True)
        mocker.patch.object(creator.category_resolver, "resolve_members", return_value=["B"])

        creator._finalize_category_creation("تصنيف:علوم", "Category:Science", "Q1", ["A"], [], None)

        assert mock_add.call_count == 2
        assert mock_add.call_args_list[1][0][0] == ["B"]
