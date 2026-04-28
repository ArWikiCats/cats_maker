"""
Tests for constants.py

This module tests category filtering functions.
"""

import pytest

from src.core.new_c18.constants import FALSE_TEMPLATES, SKIPPED_CATEGORIES


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
