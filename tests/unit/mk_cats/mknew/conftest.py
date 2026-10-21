"""Shared fixtures for the category manager tests."""

import pytest

from src.cats_maker.mk_cats.mknew import CategoryManager


@pytest.fixture
def category_manager():
    """Fixture to provide a fresh CategoryManager instance."""
    category_manager = CategoryManager()
    category_manager.stats.clear_processing_state()
    return category_manager
