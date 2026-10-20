"""
Unit tests for src/cats_maker/core_cat/c18/core/category_validator.py module.
"""

from unittest.mock import patch

from src.cats_maker.core_cat.lists.category_validator import (
    validate_categories_for_new_cat,
)
from src.cats_maker.core_cat.c18.models import ValidationResult


class TestValidateCategoriesForNewCat:
    @patch("src.cats_maker.core_cat.lists.category_validator._check_page_status")
    def test_valid_pair(self, mock_check):
        mock_check.return_value = ValidationResult(valid=True)
        result = validate_categories_for_new_cat("اختبار", "Test")
        assert result.valid is True

    @patch("src.cats_maker.core_cat.lists.category_validator._check_page_status")
    def test_en_page_invalid(self, mock_check):
        mock_check.return_value = ValidationResult(valid=False, reason="not found")
        result = validate_categories_for_new_cat("اختبار", "Test")
        assert result.valid is False

    @patch("src.cats_maker.core_cat.lists.category_validator._check_page_status")
    def test_ar_page_invalid(self, mock_check):
        # First call (EN) passes, second call (AR) fails
        mock_check.side_effect = [
            ValidationResult(valid=True),
            ValidationResult(valid=False, reason="redirect"),
        ]
        result = validate_categories_for_new_cat("اختبار", "Test")
        assert result.valid is False
