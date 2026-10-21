"""
Unit tests for src/cats_maker/core_cat/c18/core/category_validator.py module.
"""

from src.cats_maker.core_cat.lists.category_validator import (
    CategoryValidator,
)


class FakeNewAPI:
    def __init__(self, page_info):
        self.page_info = page_info

    def get_page_info_from_wikipedia(self, title):
        return self.page_info.get(title)


class FakeSiteAPI:
    def __init__(self, page_info):
        self._newapi = FakeNewAPI(page_info)

    def newapi(self):
        return self._newapi


class FakeApiLoader:
    def __init__(self, page_info):
        self.page_info = page_info

    def load(self, site, wiki_type):
        return FakeSiteAPI(self.page_info)


class TestCategoryValidator:
    """Tests for CategoryValidator behavior."""

    def test_validate_categories_success(self):
        page_info = {
            "Category:Test": {
                "exists": True,
                "is_redirect_page": False,
                "langlinks": {"ar": "تصنيف:تجربة"},
                "templates": {},
            },
            "تصنيف:تجربة": {
                "exists": True,
                "is_redirect_page": False,
                "langlinks": {"en": "Category:Test"},
                "templates": {},
            },
        }
        validator = CategoryValidator(api_loader=FakeApiLoader(page_info))
        result = validator.validate_categories_for_new_cat("تجربة", "Test")
        assert result.valid is True

    def test_validate_categories_page_not_found(self):
        validator = CategoryValidator(api_loader=FakeApiLoader({}))
        result = validator.validate_categories_for_new_cat("تجربة", "Test")
        assert result.valid is False
        assert result.reason is not None
        assert "Page not found" in result.reason
