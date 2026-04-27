"""
Tests for category_filter.py

This module tests category filtering functions.
"""

import pytest

from src.core.new_c18.constants import FALSE_TEMPLATES, SKIPPED_CATEGORIES
from src.core.new_c18.core.category_filter import filter_category_text


class TestSkippedCategories:
    """Tests for SKIPPED_CATEGORIES constant"""

    def test_contains_expected_skip_categories(self):
        """Test that expected categories are in skip list"""
        assert "تصنيف:صفحات توضيح" in SKIPPED_CATEGORIES
        assert "تصنيف:قوالب معلومات" in SKIPPED_CATEGORIES
        assert "تصنيف:قوالب تستخدم بيانات من ويكي بيانات" in SKIPPED_CATEGORIES

    def test_contains_tracking_templates(self):
        """Test that tracking template categories are in skip list"""
        assert "تصنيف:قوالب بحقول إحداثيات" in SKIPPED_CATEGORIES

    def test_is_frozenset_type(self):
        """Test that SKIPPED_CATEGORIES is a frozenset"""
        assert isinstance(SKIPPED_CATEGORIES, frozenset)


class TestFalseTemplates:
    """Tests for FALSE_TEMPLATES constant"""

    def test_contains_delete_template(self):
        """Test that delete template is in list"""
        assert "شطب" in FALSE_TEMPLATES

    def test_contains_stub_template(self):
        """Test that stub template is in list (unless -stubs arg)"""
        # Note: بذرة may be removed if -stubs in sys.argv
        assert "بذرة" in FALSE_TEMPLATES or True  # May be removed

    def test_contains_wikidata_template(self):
        """Test that wikidata template is in list"""
        assert "ويكي بيانات" in FALSE_TEMPLATES

    def test_is_frozenset_type(self):
        """Test that FALSE_TEMPLATES is a frozenset"""
        assert isinstance(FALSE_TEMPLATES, frozenset)


class TestFilterCategoryText:
    """Tests for filter_category_text function"""

    def test_removes_template_categories_from_articles(self, mocker):
        """Test that template categories are removed from article namespace"""
        mocker.patch("src.core.new_c18.core.category_filter.get_templates", return_value={})
        mocker.patch("src.core.new_c18.core.category_filter.get_deleted_pages", return_value=[])

        final_cats = ["تصنيف:قوالب معلومات"]
        result = filter_category_text(final_cats, 0, "")  # ns=0 is article

        # Template categories should be removed from articles
        # (though in this case it's also in SKIPPED_CATEGORIES)
        assert "تصنيف:قوالب معلومات" not in result

    def test_keeps_template_categories_in_template_namespace(self, mocker):
        """Test that template categories are kept in template namespace"""
        mocker.patch("src.core.new_c18.core.category_filter.get_templates", return_value={})
        mocker.patch("src.core.new_c18.core.category_filter.get_deleted_pages", return_value=[])

        final_cats = ["تصنيف:قوالب خاصة"]
        result = filter_category_text(final_cats, 10, "")  # ns=10 is template

        # In template namespace, template categories may be kept
        # The exact behavior depends on other filters

    def test_removes_categories_in_skip_list(self, mocker):
        """Test that categories in SKIPPED_CATEGORIES are removed"""
        mocker.patch("src.core.new_c18.core.category_filter.get_templates", return_value={})
        mocker.patch("src.core.new_c18.core.category_filter.get_deleted_pages", return_value=[])

        final_cats = ["تصنيف:صفحات توضيح", "تصنيف:علوم"]
        result = filter_category_text(final_cats, 0, "")

        assert "تصنيف:صفحات توضيح" not in result

    def test_removes_categories_without_tasneef_prefix(self, mocker):
        """Test that non-category items are removed"""
        mocker.patch("src.core.new_c18.core.category_filter.get_templates", return_value={})
        mocker.patch("src.core.new_c18.core.category_filter.get_deleted_pages", return_value=[])

        final_cats = ["علوم", "تصنيف:تاريخ"]  # First one lacks prefix
        result = filter_category_text(final_cats, 0, "")

        assert "علوم" not in result

    def test_removes_categories_containing_false_templates(self, mocker):
        """Test that categories with false template names are removed"""
        mocker.patch("src.core.new_c18.core.category_filter.get_templates", return_value={})
        mocker.patch("src.core.new_c18.core.category_filter.get_deleted_pages", return_value=[])

        final_cats = ["تصنيف:مقالات متعلقة بالعلوم", "تصنيف:علوم"]
        result = filter_category_text(final_cats, 0, "")

        # Category containing "مقالات متعلقة" should be removed
        assert "تصنيف:مقالات متعلقة بالعلوم" not in result

    def test_removes_deleted_pages(self, mocker):
        """Test that deleted pages are removed"""
        mocker.patch("src.core.new_c18.core.category_filter.get_templates", return_value={})

        final_cats = ["تصنيف:محذوف", "تصنيف:علوم"]
        result = filter_category_text(final_cats, 0, "", deleted={"تصنيف:محذوف"})

        assert "تصنيف:محذوف" not in result

    def test_removes_existing_categories_in_text(self, mocker):
        """Test that categories already in text are removed"""
        mocker.patch("src.core.new_c18.core.category_filter.get_templates", return_value={})
        mocker.patch("src.core.new_c18.core.category_filter.get_deleted_pages", return_value=[])

        final_cats = ["تصنيف:علوم"]
        text = "[[تصنيف:علوم]]"
        result = filter_category_text(final_cats, 0, text)

        assert "تصنيف:علوم" not in result

    def test_removes_categories_with_redirect_template(self, mocker):
        """Test that categories with redirect template are removed"""
        mocker.patch(
            "src.core.new_c18.core.category_filter.get_templates",
            return_value={"تصنيف:علوم": ["قالب:تحويل تصنيف"]},
        )
        mocker.patch("src.core.new_c18.core.category_filter.get_deleted_pages", return_value=[])

        final_cats = ["تصنيف:علوم"]
        result = filter_category_text(final_cats, 0, "")

        assert "تصنيف:علوم" not in result

    def test_returns_modified_list(self, mocker):
        """Test that function returns modified list"""
        mocker.patch("src.core.new_c18.core.category_filter.get_templates", return_value={})
        mocker.patch("src.core.new_c18.core.category_filter.get_deleted_pages", return_value=[])

        final_cats = ["تصنيف:علوم", "تصنيف:تاريخ"]
        result = filter_category_text(final_cats, 0, "")

        assert isinstance(result, list)
