"""Tests for EnglishCategorySource and ArabicCategoryChecker (mknew_sources.py)."""

from unittest.mock import MagicMock

from src.cats_maker.mk_cats.mknew.mknew_sources import ArabicCategoryChecker, EnglishCategorySource

SITE_AR = {"family": "wikipedia", "code": "ar"}
SITE_EN = {"family": "wikipedia", "code": "en"}


def make_apis_cls(page_exists: bool):
    """Build a fake AllAPIS class whose pages all report `page_exists`."""
    page = MagicMock()
    page.exists.return_value = page_exists
    api = MagicMock()
    api.mainpage.return_value = page
    apis_cls = MagicMock()
    apis_cls.load.return_value = api
    return apis_cls, api


class TestArabicCategoryChecker:
    """Tests for ArabicCategoryChecker.can_create method."""

    def test_returns_true_when_page_does_not_exist(self):
        """Test that can_create returns True when the Arabic category is missing."""
        apis_cls, _ = make_apis_cls(page_exists=False)

        assert ArabicCategoryChecker(SITE_AR, apis_cls=apis_cls).can_create("علوم") is True

    def test_returns_false_when_page_exists(self):
        """Test that can_create returns False when the Arabic category already exists."""
        apis_cls, _ = make_apis_cls(page_exists=True)

        assert ArabicCategoryChecker(SITE_AR, apis_cls=apis_cls).can_create("علوم") is False

    def test_adds_category_prefix_when_missing(self):
        """Test that the category namespace prefix is added before the lookup."""
        apis_cls, api = make_apis_cls(page_exists=False)

        ArabicCategoryChecker(SITE_AR, apis_cls=apis_cls).can_create("علوم")

        api.mainpage.assert_called_once_with("تصنيف:علوم")

    def test_keeps_existing_category_prefix(self):
        """Test that an existing prefix is not duplicated."""
        apis_cls, api = make_apis_cls(page_exists=False)

        ArabicCategoryChecker(SITE_AR, apis_cls=apis_cls).can_create("تصنيف:علوم")

        api.mainpage.assert_called_once_with("تصنيف:علوم")

    def test_loads_api_for_arabic_site_code(self):
        """Test that the API is loaded for the configured Arabic site code."""
        apis_cls, _ = make_apis_cls(page_exists=False)

        ArabicCategoryChecker(SITE_AR, apis_cls=apis_cls).can_create("علوم")

        apis_cls.load.assert_called_once_with("ar")


class TestNormalizeTitle:
    """Tests for EnglishCategorySource.normalize_title method."""

    def test_removes_wiki_brackets(self):
        """Test that [[ and ]] are removed from the title."""
        assert EnglishCategorySource.normalize_title("[[Category:Science]]") == "Category:Science"

    def test_replaces_underscores_with_spaces(self):
        """Test that underscores become spaces."""
        assert EnglishCategorySource.normalize_title("Category:Computer_science") == "Category:Computer science"

    def test_strips_surrounding_whitespace(self):
        """Test that leading and trailing whitespace is stripped."""
        assert EnglishCategorySource.normalize_title("  Category:Science  ") == "Category:Science"


class TestFindParentCategories:
    """Tests for EnglishCategorySource.find_parent_categories method."""

    def make_client_cls(self, result):
        client_cls = MagicMock()
        client_cls.return_value.find_page_categories_informations.return_value = result
        return client_cls

    def test_returns_empty_lists_when_no_categories(self):
        """Test that empty client results give two empty lists."""
        source = EnglishCategorySource(SITE_EN, langlinks_client_cls=self.make_client_cls({}))

        assert source.find_parent_categories("Category:Science") == ([], [])

    def test_splits_parents_by_arabic_link(self):
        """Test that parents with an Arabic link and without one are separated."""
        client_cls = self.make_client_cls({"Category:One": {"ar": "تصنيف:واحد"}, "Category:Two": {}})
        source = EnglishCategorySource(SITE_EN, langlinks_client_cls=client_cls)

        en_cats, ar_cats = source.find_parent_categories("Category:Science")

        assert en_cats == ["Category:Two"]
        assert ar_cats == ["تصنيف:واحد"]

    def test_queries_client_with_english_site(self):
        """Test that the client is created and queried with the English site settings."""
        client_cls = self.make_client_cls({})
        source = EnglishCategorySource(SITE_EN, langlinks_client_cls=client_cls)

        source.find_parent_categories("Category:Science")

        client_cls.assert_called_once_with(family="wikipedia")
        client_cls.return_value.find_page_categories_informations.assert_called_once_with(
            "Category:Science", prop="langlinks", site_code="en"
        )
