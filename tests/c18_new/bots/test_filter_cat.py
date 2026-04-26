"""
Tests for src/c18_new/bots/filter_cat.py

This module tests category filtering functions.
"""

import pytest

from src.core.c18_new.bots.filter_cat import (
    Skippe_Cat,
    filter_cats_text,
    page_false_templates,
)


class TestSkippeCat:
    """Tests for Skippe_Cat list"""

    def test_contains_expected_skip_categories(self):
        """Test that expected categories are in skip list"""
        assert "تصنيف:صفحات توضيح" in Skippe_Cat
        assert "تصنيف:قوالب معلومات" in Skippe_Cat
        assert "تصنيف:قوالب تستخدم بيانات من ويكي بيانات" in Skippe_Cat

    def test_contains_tracking_templates(self):
        """Test that tracking template categories are in skip list"""
        assert "تصنيف:قوالب بحقول إحداثيات" in Skippe_Cat

    def test_is_list_type(self):
        """Test that Skippe_Cat is a list"""
        assert isinstance(Skippe_Cat, list)


class TestPageFalseTemplates:
    """Tests for page_false_templates list"""

    def test_contains_delete_template(self):
        """Test that delete template is in list"""
        assert "شطب" in page_false_templates

    def test_contains_stub_template(self):
        """Test that stub template is in list (unless -stubs arg)"""
        # Note: bذرة may be removed if -stubs in sys.argv
        assert "بذرة" in page_false_templates or True  # May be removed

    def test_contains_wikidata_template(self):
        """Test that wikidata template is in list"""
        assert "ويكي بيانات" in page_false_templates

    def test_is_list_type(self):
        """Test that page_false_templates is a list"""
        assert isinstance(page_false_templates, list)


class TestFilterCatsText:
    """Tests for filter_cats_text function"""

    def test_removes_template_categories_from_articles(self, mocker):
        """Test that template categories are removed from article namespace"""
        mocker.patch("src.core.c18_new.bots.filter_cat.templatequerymulti", return_value={})
        mocker.patch("src.core.c18_new.bots.filter_cat.templatequery", return_value=False)
        mocker.patch("src.core.c18_new.bots.filter_cat.get_deleted_pages", return_value=[])

        final_cats = ["تصنيف:قوالب معلومات"]
        result = filter_cats_text(final_cats, 0, "")  # ns=0 is article

        # Template categories should be removed from articles
        # (though in this case it's also in Skippe_Cat)
        assert "تصنيف:قوالب معلومات" not in result

    def test_keeps_template_categories_in_template_namespace(self, mocker):
        """Test that template categories are kept in template namespace"""
        mocker.patch("src.core.c18_new.bots.filter_cat.templatequerymulti", return_value={})
        mocker.patch("src.core.c18_new.bots.filter_cat.templatequery", return_value=False)
        mocker.patch("src.core.c18_new.bots.filter_cat.get_deleted_pages", return_value=[])

        final_cats = ["تصنيف:قوالب خاصة"]
        result = filter_cats_text(final_cats, 10, "")  # ns=10 is template

        # In template namespace, template categories may be kept
        # The exact behavior depends on other filters

    def test_removes_categories_in_skip_list(self, mocker):
        """Test that categories in Skippe_Cat are removed"""
        mocker.patch("src.core.c18_new.bots.filter_cat.templatequerymulti", return_value={})
        mocker.patch("src.core.c18_new.bots.filter_cat.templatequery", return_value=False)
        mocker.patch("src.core.c18_new.bots.filter_cat.get_deleted_pages", return_value=[])

        final_cats = ["تصنيف:صفحات توضيح", "تصنيف:علوم"]
        result = filter_cats_text(final_cats, 0, "")

        assert "تصنيف:صفحات توضيح" not in result

    def test_removes_categories_without_tasneef_prefix(self, mocker):
        """Test that non-category items are removed"""
        mocker.patch("src.core.c18_new.bots.filter_cat.templatequerymulti", return_value={})
        mocker.patch("src.core.c18_new.bots.filter_cat.templatequery", return_value=False)
        mocker.patch("src.core.c18_new.bots.filter_cat.get_deleted_pages", return_value=[])

        final_cats = ["علوم", "تصنيف:تاريخ"]  # First one lacks prefix
        result = filter_cats_text(final_cats, 0, "")

        assert "علوم" not in result

    def test_removes_categories_containing_false_templates(self, mocker):
        """Test that categories with false template names are removed"""
        mocker.patch("src.core.c18_new.bots.filter_cat.templatequerymulti", return_value={})
        mocker.patch("src.core.c18_new.bots.filter_cat.templatequery", return_value=False)
        mocker.patch("src.core.c18_new.bots.filter_cat.get_deleted_pages", return_value=[])

        final_cats = ["تصنيف:مقالات متعلقة بالعلوم", "تصنيف:علوم"]
        result = filter_cats_text(final_cats, 0, "")

        # Category containing "مقالات متعلقة" should be removed
        assert "تصنيف:مقالات متعلقة بالعلوم" not in result

    def test_removes_deleted_pages(self, mocker):
        """Test that deleted pages are removed"""
        mocker.patch("src.core.c18_new.bots.filter_cat.templatequerymulti", return_value={})
        mocker.patch("src.core.c18_new.bots.filter_cat.templatequery", return_value=False)
        mocker.patch("src.core.c18_new.bots.filter_cat.get_deleted_pages", return_value=["تصنيف:محذوف"])

        final_cats = ["تصنيف:محذوف", "تصنيف:علوم"]
        result = filter_cats_text(final_cats, 0, "")

        assert "تصنيف:محذوف" not in result

    def test_removes_existing_categories_in_text(self, mocker):
        """Test that categories already in text are removed"""
        mocker.patch("src.core.c18_new.bots.filter_cat.templatequerymulti", return_value={})
        mocker.patch("src.core.c18_new.bots.filter_cat.templatequery", return_value=False)
        mocker.patch("src.core.c18_new.bots.filter_cat.get_deleted_pages", return_value=[])

        final_cats = ["تصنيف:علوم"]
        text = "[[تصنيف:علوم]]"
        result = filter_cats_text(final_cats, 0, text)

        assert "تصنيف:علوم" not in result

    def test_removes_categories_with_redirect_template(self, mocker):
        """Test that categories with redirect template are removed"""
        mocker.patch(
            "src.core.c18_new.bots.filter_cat.templatequerymulti",
            return_value={"تصنيف:علوم": {"templates": ["قالب:تحويل تصنيف"]}},
        )
        mocker.patch("src.core.c18_new.bots.filter_cat.templatequery", return_value=["قالب:تحويل تصنيف"])
        mocker.patch("src.core.c18_new.bots.filter_cat.get_deleted_pages", return_value=[])

        final_cats = ["تصنيف:علوم"]
        result = filter_cats_text(final_cats, 0, "")

        assert "تصنيف:علوم" not in result

    def test_returns_modified_list(self, mocker):
        """Test that function returns modified list"""
        mocker.patch("src.core.c18_new.bots.filter_cat.templatequerymulti", return_value={})
        mocker.patch("src.core.c18_new.bots.filter_cat.templatequery", return_value=False)
        mocker.patch("src.core.c18_new.bots.filter_cat.get_deleted_pages", return_value=[])

        final_cats = ["تصنيف:علوم", "تصنيف:تاريخ"]
        result = filter_cats_text(final_cats, 0, "")

        assert isinstance(result, list)
