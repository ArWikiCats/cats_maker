"""
Unit tests for src/core/new_c18/core/category_validator.py module.
"""

from unittest.mock import patch

from src.core.new_c18.core.category_validator import (
    _get_false_templates,
    _get_no_templates,
    validate_categories_for_new_cat,
)
from src.core.new_c18.models import ValidationResult


class TestGetNoTemplates:
    @patch("src.core.new_c18.core.category_validator.main_settings")
    @patch("src.core.new_c18.core.category_validator.NO_TEMPLATES_AR", frozenset(["stub"]))
    @patch("src.core.new_c18.core.category_validator.NO_TEMPLATES_AR_WITHOUT_STUBS", frozenset(["redirect"]))
    def test_returns_no_templates_ar(self, mock_settings):
        mock_settings.category.stubs = False
        result = _get_no_templates()
        assert "stub" in result

    @patch("src.core.new_c18.core.category_validator.main_settings")
    @patch("src.core.new_c18.core.category_validator.NO_TEMPLATES_AR", frozenset(["stub"]))
    @patch("src.core.new_c18.core.category_validator.NO_TEMPLATES_AR_WITHOUT_STUBS", frozenset(["redirect"]))
    def test_returns_no_templates_without_stubs(self, mock_settings):
        mock_settings.category.stubs = True
        result = _get_no_templates()
        assert "redirect" in result


class TestGetFalseTemplates:
    @patch("src.core.new_c18.core.category_validator.global_false_entemps", ["Nobots", "Dead"])
    def test_returns_lowercased(self):
        result = _get_false_templates()
        assert "nobots" in result
        assert "dead" in result


class TestValidateCategoriesForNewCat:
    @patch("src.core.new_c18.core.category_validator._check_page_status")
    def test_valid_pair(self, mock_check):
        mock_check.return_value = ValidationResult(valid=True)
        result = validate_categories_for_new_cat("اختبار", "Test")
        assert result.valid is True

    @patch("src.core.new_c18.core.category_validator._check_page_status")
    def test_en_page_invalid(self, mock_check):
        mock_check.return_value = ValidationResult(valid=False, reason="not found")
        result = validate_categories_for_new_cat("اختبار", "Test")
        assert result.valid is False

    @patch("src.core.new_c18.core.category_validator._check_page_status")
    def test_ar_page_invalid(self, mock_check):
        # First call (EN) passes, second call (AR) fails
        mock_check.side_effect = [
            ValidationResult(valid=True),
            ValidationResult(valid=False, reason="redirect"),
        ]
        result = validate_categories_for_new_cat("اختبار", "Test")
        assert result.valid is False
