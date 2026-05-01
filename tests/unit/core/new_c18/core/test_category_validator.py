"""
Unit tests for src/core/new_c18/core/category_validator.py module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.new_c18.core.category_validator import (
    _check_page_status,
    _get_false_templates,
    _get_no_templates,
    validate_categories_for_new_cat,
)
from src.core.new_c18.models import ValidationResult


class TestGetNoTemplates:
    @patch("src.core.new_c18.core.category_validator.settings")
    @patch("src.core.new_c18.core.category_validator.NO_TEMPLATES_AR", frozenset(["stub"]))
    @patch("src.core.new_c18.core.category_validator.NO_TEMPLATES_AR_WITHOUT_STUBS", frozenset(["redirect"]))
    def test_returns_no_templates_ar(self, mock_settings):
        mock_settings.category.stubs = False
        result = _get_no_templates()
        assert "stub" in result

    @patch("src.core.new_c18.core.category_validator.settings")
    @patch("src.core.new_c18.core.category_validator.NO_TEMPLATES_AR", frozenset(["stub"]))
    @patch("src.core.new_c18.core.category_validator.NO_TEMPLATES_AR_WITHOUT_STUBS", frozenset(["redirect"]))
    def test_returns_no_templates_without_stubs(self, mock_settings):
        mock_settings.category.stubs = True
        result = _get_no_templates()
        assert "redirect" in result


class TestGetFalseTemplates:
    @patch("src.core.new_c18.core.category_validator.global_False_entemps", ["Nobots", "Dead"])
    def test_returns_lowercased(self):
        result = _get_false_templates()
        assert "nobots" in result
        assert "dead" in result


class TestCheckPageStatus:
    @patch("src.core.new_c18.core.category_validator.get_page_info_from_wikipedia")
    def test_page_not_found(self, mock_get_info):
        mock_get_info.return_value = None
        result = _check_page_status("en", "Category:Test", None, frozenset())
        assert result.valid is False
        assert "not found" in result.reason

    @patch("src.core.new_c18.core.category_validator.get_page_info_from_wikipedia")
    def test_page_does_not_exist(self, mock_get_info):
        mock_get_info.return_value = {"exists": False}
        result = _check_page_status("en", "Category:Test", None, frozenset())
        assert result.valid is False
        assert "not exist" in result.reason

    @patch("src.core.new_c18.core.category_validator.get_page_info_from_wikipedia")
    def test_page_is_redirect(self, mock_get_info):
        mock_get_info.return_value = {"exists": True, "isRedirectPage": True}
        result = _check_page_status("en", "Category:Test", None, frozenset())
        assert result.valid is False
        assert "redirect" in result.reason

    @patch("src.core.new_c18.core.category_validator.get_page_info_from_wikipedia")
    def test_valid_page(self, mock_get_info):
        mock_get_info.return_value = {"exists": True, "isRedirectPage": False, "templates": {}}
        result = _check_page_status("en", "Category:Test", None, frozenset())
        assert result.valid is True

    @patch("src.core.new_c18.core.category_validator.get_page_info_from_wikipedia")
    def test_blacklisted_template(self, mock_get_info):
        mock_get_info.return_value = {
            "exists": True,
            "isRedirectPage": False,
            "templates": {"Template:Nobots"},
        }
        with (
            patch("src.core.new_c18.core.category_validator.settings") as mock_settings,
            patch("src.core.new_c18.core.category_validator._get_false_templates", return_value=frozenset(["nobots"])),
        ):
            mock_settings.category.keep = False
            result = _check_page_status("en", "Category:Test", None, frozenset())
            assert result.valid is False
            assert "Blacklisted" in result.reason

    @patch("src.core.new_c18.core.category_validator.get_page_info_from_wikipedia")
    def test_langlink_mismatch(self, mock_get_info):
        mock_get_info.return_value = {
            "exists": True,
            "isRedirectPage": False,
            "templates": {},
            "langlinks": {"en": "Category:Other"},
        }
        # is_ar=True, so it looks for "ar" key; expected_langlink doesn't match
        result = _check_page_status("ar", "تصنيف:اختبار", "Category:Test", frozenset(), is_ar=True)
        # langlinks has "en" but not "ar", so langlink="" and condition is skipped
        # Need to provide the ar key
        mock_get_info.return_value["langlinks"]["ar"] = "تصنيف:أخرى"
        result = _check_page_status("ar", "تصنيف:اختبار", "Category:Test", frozenset(), is_ar=True)
        assert result.valid is False
        assert "mismatch" in result.reason


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
