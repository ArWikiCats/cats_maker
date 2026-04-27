"""
Tests for check_redirects.py

This module tests Wikipedia API helper functions.
"""

from src.core.wiki_api.check_redirects import remove_redirect_pages


class TestRemoveRedirectPages:
    """Tests for remove_redirect_pages function"""

    def test_returns_non_redirect_pages(self, mocker):
        """Test that remove_redirect_pages returns only non-redirect pages"""
        mocker.patch(
            "src.core.wiki_api.check_redirects.load_non_redirects",
            return_value={
                "Science": True,
                "Mathematics": True,
                "redirect": False,
            },
        )

        result = remove_redirect_pages("en", ["Science", "Mathematics", "Physics"])

        assert result == ["Science", "Mathematics"]

    def test_logs_zero_removals(self, mocker):
        """Test that remove_redirect_pages logs correctly when no redirects are removed"""
        mocker.patch(
            "src.core.wiki_api.check_redirects.load_non_redirects",
            return_value={
                "Page1": True,
                "Page2": True,
            },
        )
        result = remove_redirect_pages("en", ["Page1", "Page2"])
        assert result == ["Page1", "Page2"]

    def test_handles_empty_input(self, mocker):
        """Test that remove_redirect_pages handles empty input list"""
        result = remove_redirect_pages("en", [])

        assert result == []

    def test_handles_all_redirects(self, mocker):
        """Test that remove_redirect_pages handles case where all pages are redirects"""
        mocker.patch(
            "src.core.wiki_api.check_redirects.load_non_redirects",
            return_value={
                "Page1": False,
                "Page2": False,
                "Page3": False,
                "redirect": True,
            },
        )
        result = remove_redirect_pages("en", ["Page1", "Page2", "Page3"])

        assert result == ["redirect"]

    def test_preserves_order(self, mocker):
        """Test that remove_redirect_pages preserves the order of non-redirect pages"""
        mocker.patch(
            "src.core.wiki_api.check_redirects.load_non_redirects",
            return_value={
                "Page1": True,
                "Page2": False,
                "Page3": True,
                "Page4": True,
                "redirect": False,
            },
        )

        result = remove_redirect_pages("en", ["Page1", "Page2", "Page3", "Page4"])

        assert result == ["Page1", "Page3", "Page4"]

    def test_works_with_different_languages(self, mocker):
        """Test that remove_redirect_pages works with different language codes"""
        mocker.patch(
            "src.core.wiki_api.check_redirects.load_non_redirects",
            return_value={
                "صفحة": True,
            },
        )
        result = remove_redirect_pages("ar", ["صفحة"])

        assert result == ["صفحة"]
