"""
Tests for src/utils/skip_cats.py

This module tests the category skip lists and template blacklists.
"""

import pytest

from src.core.utils.skip_cats import (
    NO_Templates_lower,
    global_False_entemps,
    skip_encats,
)


class TestSkipEnCats:
    """Tests for skip_encats list"""

    def test_skip_encats_is_list(self):
        """Test that skip_encats is a list"""
        assert isinstance(skip_encats, list)

    def test_skip_encats_contains_strings(self):
        """Test that skip_encats contains strings"""
        for item in skip_encats:
            assert isinstance(item, str)

    def test_skip_encats_items_start_with_category(self):
        """Test that skip_encats items are category format"""
        for item in skip_encats:
            assert item.startswith("Category:")


class TestGlobalFalseEntemps:
    """Tests for global_False_entemps (template blacklist)"""

    def test_is_list(self):
        """Test that global_False_entemps is a list"""
        assert isinstance(global_False_entemps, list)

    def test_contains_hidden_category(self):
        """Test that Hidden category is in the blacklist"""
        assert "Hidden category" in global_False_entemps

    def test_contains_maintenance_category(self):
        """Test that Maintenance category is in the blacklist"""
        assert "Maintenance category" in global_False_entemps

    def test_contains_wikipedia_category(self):
        """Test that Wikipedia category is in the blacklist"""
        assert "Wikipedia category" in global_False_entemps

    def test_contains_empty_category(self):
        """Test that Empty category is in the blacklist"""
        assert "Empty category" in global_False_entemps

    def test_contains_tracking_category(self):
        """Test that Tracking category is in the blacklist"""
        assert "Tracking category" in global_False_entemps

    def test_contains_category_redirect(self):
        """Test that Category redirect is in the blacklist"""
        assert "Category redirect" in global_False_entemps

    def test_all_items_are_strings(self):
        """Test that all items are strings"""
        for item in global_False_entemps:
            assert isinstance(item, str)

    def test_no_empty_strings(self):
        """Test that there are no empty strings"""
        for item in global_False_entemps:
            assert item.strip() != ""


class TestNOTemplatesLower:
    """Tests for NO_Templates_lower list (lowercase version)"""

    def test_is_list(self):
        """Test that NO_Templates_lower is a list"""
        assert isinstance(NO_Templates_lower, list)

    def test_length_matches_original(self):
        """Test that length matches global_False_entemps"""
        assert len(NO_Templates_lower) == len(global_False_entemps)

    def test_all_lowercase(self):
        """Test that all items are lowercase"""
        for item in NO_Templates_lower:
            assert item == item.lower()

    def test_contains_lowercase_hidden_category(self):
        """Test that hidden category (lowercase) is in the list"""
        assert "hidden category" in NO_Templates_lower

    def test_contains_lowercase_maintenance_category(self):
        """Test that maintenance category (lowercase) is in the list"""
        assert "maintenance category" in NO_Templates_lower

    def test_correspondence_with_original(self):
        """Test that each item corresponds to original list (lowercase)"""
        for original, lower in zip(global_False_entemps, NO_Templates_lower):
            assert original.lower() == lower


class TestBlacklistIntegrity:
    """Tests for blacklist integrity and consistency"""

    def test_no_duplicates_in_global_false_entemps(self):
        """Test that there are no duplicate entries"""
        assert len(global_False_entemps) == len(set(global_False_entemps))

    def test_no_duplicates_in_templates_lower(self):
        """Test that there are no duplicate entries in lowercase list"""
        assert len(NO_Templates_lower) == len(set(NO_Templates_lower))

    def test_blacklist_not_empty(self):
        """Test that blacklist is not empty"""
        assert len(global_False_entemps) > 0

    def test_minimum_blacklist_items(self):
        """Test that blacklist has a minimum number of items"""
        # Based on the source, there should be at least 10 items
        assert len(global_False_entemps) >= 10
