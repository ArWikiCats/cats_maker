"""Unit tests for src/core/api_sql/constants.py module."""

from src.shared.api_sql.constants import (
    NS_TEXT_AR,
    NS_TEXT_EN,
    SUFFIXED_WIKIS,
    WIKI_ALIASES,
)


class TestWikiAliases:
    """Tests for WIKI_ALIASES mapping."""

    def test_wikidata_alias(self):
        assert WIKI_ALIASES["wikidata"] == "wikidatawiki"

    def test_be_x_old_dash(self):
        assert WIKI_ALIASES["be-x-old"] == "be_x_old"

    def test_be_tarask_underscore(self):
        assert WIKI_ALIASES["be_tarask"] == "be_x_old"

    def test_be_tarask_dash(self):
        assert WIKI_ALIASES["be-tarask"] == "be_x_old"

    def test_all_values_are_strings(self):
        for v in WIKI_ALIASES.values():
            assert isinstance(v, str)


class TestSuffixedWikis:
    """Tests for SUFFIXED_WIKIS frozenset."""

    def test_is_frozenset(self):
        assert isinstance(SUFFIXED_WIKIS, frozenset)

    def test_contains_wiktionary(self):
        assert "wiktionary" in SUFFIXED_WIKIS

    def test_does_not_contain_wiki(self):
        assert "wiki" not in SUFFIXED_WIKIS


class TestNsTextAr:
    """Tests for Arabic namespace table."""

    def test_category(self):
        assert NS_TEXT_AR["14"] == "تصنيف"

    def test_template(self):
        assert NS_TEXT_AR["10"] == "قالب"

    def test_namespace_zero_is_empty(self):
        assert NS_TEXT_AR["0"] == ""

    def test_user(self):
        assert NS_TEXT_AR["2"] == "مستخدم"

    def test_portal(self):
        assert NS_TEXT_AR["100"] == "بوابة"

    def test_module(self):
        assert NS_TEXT_AR["828"] == "وحدة"


class TestNsTextEn:
    """Tests for English namespace table."""

    def test_category(self):
        assert NS_TEXT_EN["14"] == "Category"

    def test_template(self):
        assert NS_TEXT_EN["10"] == "Template"

    def test_namespace_zero_is_empty(self):
        assert NS_TEXT_EN["0"] == ""

    def test_user(self):
        assert NS_TEXT_EN["2"] == "User"

    def test_portal(self):
        assert NS_TEXT_EN["100"] == "Portal"

    def test_module(self):
        assert NS_TEXT_EN["828"] == "Module"
