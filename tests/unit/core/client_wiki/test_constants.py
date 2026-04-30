"""
Unit tests for src/core/client_wiki/constants.py module.
"""

from src.core.client_wiki.constants import CATEGORY_PREFIXES, NS_LIST


class TestCategoryPrefixes:
    def test_arabic_prefix(self):
        assert CATEGORY_PREFIXES["ar"] == "تصنيف:"

    def test_english_prefix(self):
        assert CATEGORY_PREFIXES["en"] == "Category:"

    def test_www_prefix(self):
        assert CATEGORY_PREFIXES["www"] == "Category:"

    def test_has_expected_keys(self):
        assert set(CATEGORY_PREFIXES.keys()) == {"ar", "en", "www"}


class TestNsList:
    def test_ns_list_is_dict(self):
        assert isinstance(NS_LIST, dict)

    def test_ns_list_has_main_namespace(self):
        assert "0" in NS_LIST

    def test_ns_list_main_namespace_is_empty(self):
        assert NS_LIST["0"] == ""
