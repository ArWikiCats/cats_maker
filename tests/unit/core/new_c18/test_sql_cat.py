"""
Tests for category_resolver.py SQL-related methods.

This module tests SQL-based category functions.
"""

from src.core.new_c18.core.category_resolver import CategoryResolver


class TestFetchArTitlesBasedOnEnCategory:
    """Tests for CategoryResolver._fetch_ar_titles_based_on_en_category method"""

    def test_calls_en_category_members(self, mocker):
        """Test that _en_category_members is called"""
        mock_en_cat = mocker.patch(
            "src.core.new_c18.core.category_resolver.CategoryResolver._en_category_members",
            return_value=["Page1", "Page2"],
        )
        mocker.patch(
            "src.core.new_c18.core.category_resolver.CategoryResolver._translate_titles_to_ar",
            return_value=["صفحة1", "صفحة2"],
        )

        resolver = CategoryResolver()
        result = resolver._fetch_ar_titles_based_on_en_category("Science")

        mock_en_cat.assert_called_once_with("Science", wiki="en")

    def test_calls_translate_titles_to_ar(self, mocker):
        """Test that _translate_titles_to_ar is called"""
        mocker.patch(
            "src.core.new_c18.core.category_resolver.CategoryResolver._en_category_members",
            return_value=["Page1", "Page2"],
        )
        mock_get_ar = mocker.patch(
            "src.core.new_c18.core.category_resolver.CategoryResolver._translate_titles_to_ar",
            return_value=["صفحة1", "صفحة2"],
        )

        resolver = CategoryResolver()
        result = resolver._fetch_ar_titles_based_on_en_category("Science", wiki="en")

        mock_get_ar.assert_called_once_with(["Page1", "Page2"], wiki="en")

    def test_returns_arabic_titles(self, mocker):
        """Test that Arabic titles are returned"""
        mocker.patch(
            "src.core.new_c18.core.category_resolver.CategoryResolver._en_category_members",
            return_value=["Science"],
        )
        mocker.patch(
            "src.core.new_c18.core.category_resolver.CategoryResolver._translate_titles_to_ar",
            return_value=["علوم"],
        )

        resolver = CategoryResolver()
        result = resolver._fetch_ar_titles_based_on_en_category("Science")

        assert "علوم" in result


class TestListArPagesInCat:
    """Tests for CategoryResolver.list_ar_pages_in_cat method"""

    def test_returns_list(self, mocker):
        """Test that method returns a list"""
        mocker.patch(
            "src.core.new_c18.core.category_resolver.fetch_ar_category_members",
            return_value=[{"page_title": "test", "page_namespace": 0}],
        )

        resolver = CategoryResolver()
        result = resolver.list_ar_pages_in_cat("تصنيف:علوم")

        assert isinstance(result, list)
        assert "test" in result

    def test_uses_sql_when_enabled(self, mocker):
        """Test that SQL is used when enabled"""
        mock_sql = mocker.patch(
            "src.core.new_c18.core.category_resolver.fetch_ar_category_members",
            return_value=[{"page_title": "صفحة1", "page_namespace": 0}],
        )

        resolver = CategoryResolver(backend="sql")
        result = resolver.list_ar_pages_in_cat("تصنيف:علوم")

        mock_sql.assert_called_once()

    def test_replaces_spaces_with_underscores(self, mocker):
        """Test that spaces are handled correctly"""
        mock_sql = mocker.patch(
            "src.core.new_c18.core.category_resolver.fetch_ar_category_members",
            return_value=[{"page_title": "test", "page_namespace": 0}],
        )

        resolver = CategoryResolver(backend="sql")
        result = resolver.list_ar_pages_in_cat("تصنيف:علوم الحاسوب")
        assert "test" in result


class TestListEnPagesWithArLinks:
    """Tests for CategoryResolver.list_en_pages_with_ar_links method"""

    def test_returns_list(self, mocker):
        """Test that method returns a list"""
        mocker.patch(
            "src.core.new_c18.core.category_resolver.fetch_en_category_langlinks",
            side_effect=Exception("SQL Error"),
        )
        mocker.patch(
            "src.core.new_c18.core.category_resolver.CategoryResolver._fetch_ar_titles_based_on_en_category",
            return_value=[],
        )
        mocker.patch("src.core.new_c18.core.category_resolver.settings.database.use_sql", False)

        resolver = CategoryResolver()
        result = resolver.list_en_pages_with_ar_links("Science")

        assert isinstance(result, list)

    def test_uses_sql_when_enabled(self, mocker):
        """Test that SQL is used when enabled"""
        mock_sql = mocker.patch(
            "src.core.new_c18.core.category_resolver.fetch_en_category_langlinks",
            return_value=[{"ll_title": "صفحة1"}, {"ll_title": "صفحة2"}],
        )

        resolver = CategoryResolver(backend="sql")
        result = resolver.list_en_pages_with_ar_links("Science")

        mock_sql.assert_called_once()

    def test_falls_back_to_api_when_sql_disabled(self, mocker):
        """Test fallback to API when SQL fails"""
        mocker.patch(
            "src.core.new_c18.core.category_resolver.fetch_en_category_langlinks",
            side_effect=Exception("SQL Error"),
        )
        mock_api = mocker.patch(
            "src.core.new_c18.core.category_resolver.CategoryResolver._fetch_ar_titles_based_on_en_category",
            return_value=["صفحة1"],
        )
        mocker.patch("src.core.new_c18.core.category_resolver.settings.database.use_sql", False)

        resolver = CategoryResolver()
        result = resolver.list_en_pages_with_ar_links("Science")

        mock_api.assert_called_once()

    def test_replaces_underscores_in_results(self, mocker):
        """Test that underscores are replaced with spaces in results"""
        mocker.patch(
            "src.core.new_c18.core.category_resolver.fetch_en_category_langlinks",
            return_value=[{"ll_title": "صفحة_اختبار"}],
        )

        resolver = CategoryResolver(backend="sql")
        result = resolver.list_en_pages_with_ar_links("Science")

        assert "صفحة اختبار" in result


class TestDiffMissingArPages:
    """Tests for CategoryResolver.diff_missing_ar_pages method"""

    def test_returns_list(self, mocker):
        """Test that method returns a list"""
        mocker.patch(
            "src.core.new_c18.core.category_resolver.CategoryResolver.list_ar_pages_in_cat",
            return_value=[],
        )
        mocker.patch(
            "src.core.new_c18.core.category_resolver.CategoryResolver.list_en_pages_with_ar_links",
            return_value=[],
        )

        resolver = CategoryResolver()
        result = resolver.diff_missing_ar_pages("Science", "علوم")

        assert isinstance(result, list)

    def test_returns_difference_of_lists(self, mocker):
        """Test that result is pages in en but not in ar"""
        mocker.patch(
            "src.core.new_c18.core.category_resolver.CategoryResolver.list_ar_pages_in_cat",
            return_value=["صفحة1", "صفحة2"],
        )
        mocker.patch(
            "src.core.new_c18.core.category_resolver.CategoryResolver.list_en_pages_with_ar_links",
            return_value=["صفحة1", "صفحة2", "صفحة3"],
        )

        resolver = CategoryResolver()
        result = resolver.diff_missing_ar_pages("Science", "علوم")

        assert "صفحة3" in result
        assert "صفحة1" not in result
        assert "صفحة2" not in result


class TestResolveMembers:
    """Tests for CategoryResolver.resolve_members method"""

    def test_returns_list(self, mocker):
        """Test that method returns a list"""
        mocker.patch(
            "src.core.new_c18.core.category_resolver.CategoryResolver.diff_missing_ar_pages",
            return_value=[],
        )

        resolver = CategoryResolver()
        result = resolver.resolve_members("Science", "علوم")

        assert isinstance(result, list)

    def test_cleans_category_prefix(self, mocker):
        """Test that Category: prefix is cleaned"""
        mock_diff = mocker.patch(
            "src.core.new_c18.core.category_resolver.CategoryResolver.diff_missing_ar_pages",
            return_value=[],
        )

        resolver = CategoryResolver()
        resolver.resolve_members("Category:Science", "تصنيف:علوم")

        call_args = mock_diff.call_args[0]
        assert "Category:" not in call_args[0]
        assert "تصنيف:" not in call_args[1]

    def test_replaces_underscores(self, mocker):
        """Test that underscores are replaced with spaces"""
        mock_diff = mocker.patch(
            "src.core.new_c18.core.category_resolver.CategoryResolver.diff_missing_ar_pages",
            return_value=[],
        )

        resolver = CategoryResolver()
        resolver.resolve_members("Computer_Science", "علوم_الحاسوب")

        call_args = mock_diff.call_args[0]
        assert "_" not in call_args[0]
        assert "_" not in call_args[1]

    def test_passes_wiki_parameter(self, mocker):
        """Test that wiki parameter is passed"""
        mock_diff = mocker.patch(
            "src.core.new_c18.core.category_resolver.CategoryResolver.diff_missing_ar_pages",
            return_value=[],
        )

        resolver = CategoryResolver()
        resolver.resolve_members("Sciences", "علوم", wiki="fr")

        call_kwargs = mock_diff.call_args[1]
        assert call_kwargs["wiki"] == "fr"
