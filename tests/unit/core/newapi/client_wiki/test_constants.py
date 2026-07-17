"""
Unit tests for src/core/client_wiki/constants.py module.
"""

from src.core.newapi.client_wiki.constants import CATEGORY_PREFIXES


class TestCategoryPrefixes:
    def test_arabic_prefix(self):
        assert CATEGORY_PREFIXES["ar"] == "تصنيف:"

    def test_english_prefix(self):
        assert CATEGORY_PREFIXES["en"] == "Category:"

    def test_www_prefix(self):
        assert CATEGORY_PREFIXES["www"] == "Category:"

    def test_has_expected_keys(self):
        assert set(CATEGORY_PREFIXES.keys()) == {"ar", "en", "www"}
