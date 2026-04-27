"""
Tests for check_redirects.py

This module tests Wikipedia API helper functions.
"""

import pytest

from src.core.wiki_api.check_redirects import (
    remove_redirect_pages,
)


@pytest.mark.network
class TestRemoveRedirectPagesReal:
    """Tests for remove_redirect_pages function"""

    def test_removes_redirects_english(self):
        """Test that redirect pages are removed from the list"""
        page_titles = ["Python (programming language)", "USA", "Nonexistent Page 12345"]
        non_redirects = remove_redirect_pages("en", page_titles)
        assert "Python (programming language)" in non_redirects
        assert "USA" not in non_redirects
        assert "Nonexistent Page 12345" not in non_redirects

    def test_removes_redirects_arabic(self):
        """Test that redirect pages are removed from the list"""
        page_titles = ["يمن", "اليمن"]
        non_redirects = remove_redirect_pages("ar", page_titles)
        assert "يمن" not in non_redirects
        assert "اليمن" in non_redirects

    def test_real_mixed_pages(self):
        """Test with real mix of valid pages and redirects"""
        page_titles = ["Wikipedia", "Main Page", "WP:NPOV"]  # WP:NPOV is redirect
        non_redirects = remove_redirect_pages("en", page_titles)
        assert "Wikipedia" in non_redirects
        assert "Main Page" in non_redirects

    def test_real_all_valid(self):
        """Test with real pages that are all valid (non-redirects)"""
        page_titles = ["Wikipedia", "Main Page"]
        non_redirects = remove_redirect_pages("en", page_titles)
        assert len(non_redirects) == 2

    def test_real_empty_list(self):
        """Test with empty list on real API"""
        result = remove_redirect_pages("en", [])
        assert result == []
