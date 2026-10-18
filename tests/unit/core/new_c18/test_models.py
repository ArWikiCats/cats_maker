"""
Unit tests for src/app/core/new_c18/models.py module.
"""

import pytest

from src.app.core.new_c18.models import Category, CategoryRef, PageRef, ValidationResult, WikiPage


class TestCategoryRef:
    def test_creation(self):
        ref = CategoryRef(title="Science", lang="en")
        assert ref.title == "Science"
        assert ref.lang == "en"

    def test_frozen(self):
        ref = CategoryRef(title="Science", lang="en")
        with pytest.raises(AttributeError):
            ref.title = "Math"


class TestPageRef:
    def test_creation(self):
        ref = PageRef(title="Test", namespace=0, langlinks={"en": "Test"})
        assert ref.title == "Test"
        assert ref.namespace == 0
        assert ref.langlinks == {"en": "Test"}


class TestWikiPage:
    def test_defaults(self):
        page = WikiPage(title="Test", namespace=0)
        assert page.langlinks == {}

    def test_with_langlinks(self):
        page = WikiPage(title="Test", namespace=0, langlinks={"ar": "اختبار"})
        assert page.langlinks == {"ar": "اختبار"}


class TestCategory:
    def test_defaults(self):
        cat = Category(title="Test")
        assert cat.templates == []

    def test_with_templates(self):
        cat = Category(title="Test", templates=["قالب:A"])
        assert cat.templates == ["قالب:A"]


class TestValidationResult:
    def test_valid(self):
        result = ValidationResult(valid=True)
        assert result.valid is True
        assert result.reason is None

    def test_invalid_with_reason(self):
        result = ValidationResult(valid=False, reason="not found")
        assert result.valid is False
        assert result.reason == "not found"
