"""Tests for the CategoryManager facade and the legacy functions (category_manager.py)."""

from unittest.mock import MagicMock

from src.cats_maker.mk_cats.mknew import CategoryManager
from src.cats_maker.mk_cats.mknew import category_manager as mknew
from src.cats_maker.mk_cats.mknew.mknew_processor import CategoryBatchProcessor


class TestCategoryManagerWiring:
    """Tests for how CategoryManager builds and shares its components."""

    def test_components_share_the_same_stats(self, category_manager):
        """Test that manager, creator and processor use one stats instance."""
        assert category_manager.creator.stats is category_manager.stats
        assert category_manager.processor.stats is category_manager.stats

    def test_processor_uses_the_manager_creator(self, category_manager):
        """Test that the processor drives the same creator the manager exposes."""
        assert category_manager.processor.creator is category_manager.creator

    def test_components_share_the_same_resolver(self, category_manager):
        """Test that creator and processor use the manager resolver."""
        assert category_manager.creator.category_resolver is category_manager.category_resolver
        assert category_manager.processor.category_resolver is category_manager.category_resolver

    def test_uses_default_sites(self, category_manager):
        """Test that default wiki sites are used when none are given."""
        assert category_manager.wiki_site_ar == mknew.WIKI_SITE_AR
        assert category_manager.wiki_site_en == mknew.WIKI_SITE_EN

    def test_accepts_injected_components(self):
        """Test that a creator and a processor can be injected."""
        creator = MagicMock()
        processor = MagicMock()

        manager = CategoryManager(creator=creator, processor=processor)

        assert manager.creator is creator
        assert manager.processor is processor


class TestCategoryManagerDelegation:
    """Tests that CategoryManager public methods delegate to the right component."""

    def test_make_ar_delegates_to_creator(self, mocker, category_manager):
        """Test that make_ar is handled by the creator."""
        callback = MagicMock()
        mock_make_ar = mocker.patch.object(category_manager.creator, "make_ar", return_value=["Category:X"])

        result = category_manager.make_ar("Category:Science", "علوم", callback=callback)

        assert result == ["Category:X"]
        mock_make_ar.assert_called_once_with("Category:Science", "علوم", callback=callback)

    def test_one_cat_delegates_to_processor(self, mocker, category_manager):
        """Test that one_cat is handled by the processor."""
        callback = MagicMock()
        mock_one_cat = mocker.patch.object(category_manager.processor, "one_cat", return_value=False)

        result = category_manager.one_cat("Category:Science", 1, 2, sugust="علوم", callback=callback)

        assert result is False
        mock_one_cat.assert_called_once_with("Category:Science", 1, 2, sugust="علوم", callback=callback)

    def test_process_categories_delegates_to_processor(self, mocker, category_manager):
        """Test that process_categories is handled by the processor."""
        mock_process = mocker.patch.object(category_manager.processor, "process_categories")

        category_manager.process_categories("Category:Science", "علوم", 1, 2)

        mock_process.assert_called_once_with("Category:Science", "علوم", 1, 2, callback=None)

    def test_create_categories_from_list_delegates_to_processor(self, mocker, category_manager):
        """Test that create_categories_from_list is handled by the processor."""
        mock_create = mocker.patch.object(category_manager.processor, "create_categories_from_list")

        category_manager.create_categories_from_list(["Cat1"])

        mock_create.assert_called_once_with(["Cat1"], callback=None)


class TestLegacyFunctions:
    """Tests for the module level legacy compatibility functions."""

    def test_process_categories_wrapper(self, mocker):
        """Test that the legacy process_categories function reaches the processor."""
        mock_process = mocker.patch.object(CategoryBatchProcessor, "process_categories")
        callback = MagicMock()

        mknew.process_categories("Category:Science", "علوم", 1, 2, callback=callback)

        mock_process.assert_called_once_with("Category:Science", "علوم", 1, 2, callback=callback)

    def test_create_categories_from_list_wrapper(self, mocker):
        """Test that the legacy create_categories_from_list function reaches the processor."""
        mock_create = mocker.patch.object(CategoryBatchProcessor, "create_categories_from_list")

        mknew.create_categories_from_list(["Cat1", "Cat2"])

        mock_create.assert_called_once_with(["Cat1", "Cat2"], callback=None)
