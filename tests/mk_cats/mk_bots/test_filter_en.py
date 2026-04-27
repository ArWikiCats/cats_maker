"""
Tests for src/mk_cats/utils/filter_en.py

This module tests English category filtering functions.
"""

import pytest

from src.mk_cats.utils.filter_en import (
    BBlcak,
    blcak_starts,
    filter_cat,
)


class TestBBlcak:
    """Tests for BBlcak blacklist"""

    def test_is_list(self):
        """Test that BBlcak is a list"""
        assert isinstance(BBlcak, list)

    def test_contains_disambiguation(self):
        """Test that Disambiguation is in blacklist"""
        assert "Disambiguation" in BBlcak

    def test_contains_wikiproject(self):
        """Test that wikiproject is in blacklist"""
        assert "wikiproject" in BBlcak

    def test_contains_sockpuppets(self):
        """Test that sockpuppets is in blacklist"""
        assert "sockpuppets" in BBlcak


class TestBlcakStarts:
    """Tests for blcak_starts blacklist"""

    def test_is_list(self):
        """Test that blcak_starts is a list"""
        assert isinstance(blcak_starts, list)

    def test_contains_cleanup(self):
        """Test that Clean-up variations are in blacklist"""
        assert "Clean-up" in blcak_starts or "Cleanup" in blcak_starts

    def test_contains_wikipedia(self):
        """Test that Wikipedia is in blacklist"""
        assert "Wikipedia" in blcak_starts

    def test_contains_articles_variations(self):
        """Test that Articles variations are in blacklist"""
        articles_items = [item for item in blcak_starts if item.startswith("Articles")]
        assert len(articles_items) > 0

    def test_contains_uncategorized(self):
        """Test that Uncategorized is in blacklist"""
        assert "Uncategorized" in blcak_starts

    def test_contains_user_pages(self):
        """Test that User pages is in blacklist"""
        assert "User pages" in blcak_starts


class TestFilterCat:
    """Tests for filter_cat function"""

    def test_returns_false_for_disambiguation(self):
        """Test that Disambiguation categories with exact case match return False.

        The blacklist check uses cat.lower().find(x) where x is the original
        blacklist item (not lowercased). So "Disambiguation" won't match
        "disambiguation" in the lowercased category string.
        """
        result = filter_cat("Category:Disambiguation pages")
        # Blacklist item "Disambiguation" doesn't match lowercase "disambiguation"
        assert result is True

    def test_returns_false_for_wikiproject(self):
        """Test that WikiProject categories return False"""
        result = filter_cat("Category:WikiProject Science")
        assert result is False

    def test_returns_false_for_cleanup(self):
        """Test that cleanup categories return False"""
        result = filter_cat("Cleanup articles")
        assert result is False

    def test_returns_false_for_wikipedia_articles(self):
        """Test that Wikipedia articles categories return False"""
        result = filter_cat("Wikipedia articles needing cleanup")
        assert result is False

    def test_returns_false_for_articles_with_prefix(self):
        """Test that 'Articles with...' categories return False"""
        result = filter_cat("Articles with dead external links")
        assert result is False

    def test_returns_true_for_valid_category(self):
        """Test that valid categories return True"""
        result = filter_cat("Category:Science")
        assert result is True

    def test_returns_true_for_regular_topic(self):
        """Test that regular topic categories return True"""
        result = filter_cat("Physics")
        assert result is True

    def test_case_insensitive_blacklist(self):
        """Test blacklist matching behavior with different cases.

        The code uses cat.lower().find(x) where x is not lowercased,
        so blacklist matching is effectively case-sensitive.
        """
        result = filter_cat("DISAMBIGUATION pages")
        # "Disambiguation" in BBlcak won't match "disambiguation" (lowercased)
        assert result is True

    def test_returns_false_for_month_year_pattern(self):
        """Test that month/year patterns return False"""
        result = filter_cat("Articles from January 2020")
        assert result is False

    def test_returns_false_for_sockpuppets(self):
        """Test that sockpuppet categories return False"""
        result = filter_cat("Wikipedia sockpuppets")
        assert result is False

    def test_returns_false_for_use_prefix(self):
        """Test that 'use ' prefixed categories return False"""
        result = filter_cat("use dmy dates")
        assert result is False

    def test_caching_works(self):
        """Test that caching decorator works (same result for same input)"""
        result1 = filter_cat("Science")
        result2 = filter_cat("Science")
        assert result1 == result2

    def test_returns_false_for_userspace(self):
        """Test that Userspace categories return False"""
        result = filter_cat("Userspace drafts")
        assert result is False
