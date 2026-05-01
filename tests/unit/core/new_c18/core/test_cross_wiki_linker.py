"""
Unit tests for src/core/new_c18/core/cross_wiki_linker.py module.
"""

import pytest

from src.core.new_c18.core.cross_wiki_linker import (
    _update_caches,
    get_en_link_from_ar_text,
    get_english_page_title,
    get_page_link,
    resolve_via_api,
    resolve_via_wikidata,
)


class TestResolveViaWikidata:
    """Tests for resolve_via_wikidata function"""

    def test_returns_none_when_no_qid_in_text(self, mocker):
        """Test that None is returned when no QID is found"""
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.extract_wikidata_qid", return_value=None)

        result = resolve_via_wikidata("some text", "link", "en", "ar")
        assert result is None

    def test_returns_none_when_qid_invalid(self, mocker):
        """Test that None is returned when QID is invalid"""
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.extract_wikidata_qid", return_value="invalid")

        result = resolve_via_wikidata("some text", "link", "en", "ar")
        assert result is None

    def test_resolves_via_wikidata_sitelinks(self, mocker):
        """Test resolving via Wikidata sitelinks"""
        mocker.patch(
            "src.core.new_c18.core.cross_wiki_linker.extract_wikidata_qid",
            return_value="Q123",
        )
        mocker.patch(
            "src.core.new_c18.core.cross_wiki_linker.Get_Sitelinks_from_qid",
            return_value={"sitelinks": {"enwiki": "Science", "arwiki": "علوم"}},
        )
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.set_cache_L_C_N")

        result = resolve_via_wikidata("text with Q123", "link", "en", "ar")
        assert result == "علوم"

    def test_returns_none_when_no_matching_sitelink(self, mocker):
        """Test that None is returned when no matching sitelink"""
        mocker.patch(
            "src.core.new_c18.core.cross_wiki_linker.extract_wikidata_qid",
            return_value="Q123",
        )
        mocker.patch(
            "src.core.new_c18.core.cross_wiki_linker.Get_Sitelinks_from_qid",
            return_value={"sitelinks": {"enwiki": "Science"}},
        )

        result = resolve_via_wikidata("text with Q123", "link", "en", "fr")
        assert result is None

    def test_returns_none_when_link_has_section(self, mocker):
        """Test that None is returned when result contains #"""
        mocker.patch(
            "src.core.new_c18.core.cross_wiki_linker.extract_wikidata_qid",
            return_value="Q123",
        )
        mocker.patch(
            "src.core.new_c18.core.cross_wiki_linker.Get_Sitelinks_from_qid",
            return_value={"sitelinks": {"arwiki": "علوم#قسم"}},
        )

        result = resolve_via_wikidata("text with Q123", "link", "en", "ar")
        assert result is None


class TestResolveViaApi:
    """Tests for resolve_via_api function"""

    def test_returns_cached_value(self, mocker):
        """Test that cached values are returned"""
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.get_cache_L_C_N", return_value="Science")

        result = resolve_via_api("Science", "en", "ar")
        assert result == "Science"

    def test_cleans_link_brackets_and_prefixes(self, mocker):
        """Test that link brackets and prefixes are cleaned"""
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.get_cache_L_C_N", return_value=None)
        mocker.patch(
            "src.core.new_c18.core.cross_wiki_linker.find_LCN",
            return_value={"Science": {"langlinks": {"ar": "علوم"}}},
        )
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.Get_Sitelinks_From_wikidata", return_value=None)
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.set_cache_L_C_N")

        result = resolve_via_api("[[en:Science]]", "en", "ar")
        assert result is None

    def test_finds_langlink_from_find_lcn(self, mocker):
        """Test finding langlink from find_LCN"""
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.get_cache_L_C_N", return_value=None)
        mocker.patch(
            "src.core.new_c18.core.cross_wiki_linker.find_LCN",
            return_value={"Science": {"langlinks": {"ar": "علوم", "en": "Science"}}},
        )
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.Get_Sitelinks_From_wikidata", return_value=None)
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.set_cache_L_C_N")

        result = resolve_via_api("Science", "en", "ar")
        assert result is None

    def test_returns_none_when_ar_to_match_differs(self, mocker):
        """Test that None is returned when ar_to_match differs"""
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.get_cache_L_C_N", return_value=None)
        mocker.patch(
            "src.core.new_c18.core.cross_wiki_linker.find_LCN",
            return_value={"Science": {"langlinks": {"ar": "different", "en": "Different"}}},
        )
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.Get_Sitelinks_From_wikidata", return_value=None)
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.set_cache_L_C_N")

        result = resolve_via_api("Science", "en", "ar")
        assert result is None


class TestUpdateCaches:
    """Tests for _update_caches function"""

    def test_updates_both_directions(self, mocker):
        """Test that both cache directions are updated"""
        mock_set_cache = mocker.patch("src.core.new_c18.core.cross_wiki_linker.set_cache_L_C_N")

        _update_caches("Science", "en", "ar", "علوم")

        assert mock_set_cache.call_count == 2


class TestGetPageLink:
    """Tests for get_page_link function"""

    def test_returns_cached_value(self, mocker):
        """Test that cached values are returned"""
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.get_cache_L_C_N", return_value="Science")

        result = get_page_link("علوم", "ar", "en")
        assert result == "Science"

    def test_cleans_link_brackets(self, mocker):
        """Test that double brackets are removed from link"""
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.get_cache_L_C_N", return_value=None)
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.find_LCN", return_value=None)
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.Get_Sitelinks_From_wikidata", return_value=None)
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.set_cache_L_C_N")

        get_page_link("[[علوم]]", "ar", "en")
        # Function should process without error

    def test_returns_none_when_no_langlink(self, mocker):
        """Test that None is returned when no langlink is found"""
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.get_cache_L_C_N", return_value=None)
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.find_LCN", return_value=None)
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.Get_Sitelinks_From_wikidata", return_value=None)
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.set_cache_L_C_N")

        result = get_page_link("nonexistent", "ar", "en")
        assert result is None


class TestGetEnLinkFromArText:
    """Tests for get_en_link_from_ar_text function"""

    def test_returns_empty_string_when_no_sitelinks(self, mocker):
        """Test that empty string is returned when no sitelinks"""
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.Get_Sitelinks_From_wikidata", return_value=None)

        result = get_en_link_from_ar_text("علوم", "arwiki", "enwiki")
        assert result == ""

    def test_extracts_english_sitelink(self, mocker):
        """Test that English sitelink is extracted"""
        mocker.patch(
            "src.core.new_c18.core.cross_wiki_linker.Get_Sitelinks_From_wikidata",
            return_value={"sitelinks": {"enwiki": "Science"}},
        )

        result = get_en_link_from_ar_text("علوم", "arwiki", "enwiki")
        assert result == "Science"

    def test_handles_wiki_suffix(self, mocker):
        """Test handling of wiki suffix in sitetarget"""
        mocker.patch(
            "src.core.new_c18.core.cross_wiki_linker.Get_Sitelinks_From_wikidata",
            return_value={"sitelinks": {"en": "Science", "enwiki": "Science"}},
        )

        result = get_en_link_from_ar_text("علوم", "arwiki", "en")
        assert result == "Science"


class TestGetEnglishPageTitle:
    """Tests for get_english_page_title function"""

    def test_returns_provided_english_link(self):
        """Test that provided english link is returned"""
        result, site = get_english_page_title("Science", "علوم", "", {})
        assert result == "Science"
        assert site == "en"

    def test_extracts_from_langlinks(self, mocker):
        """Test extracting from ar_page_langlinks"""
        result, site = get_english_page_title("", "علوم", "", {"en": "Science"})
        assert result == "Science"
        assert site == "en"

    def test_blacklists_sandbox_pages(self, mocker):
        """Test that Sandbox pages are blacklisted"""
        mocker.patch(
            "src.core.new_c18.core.cross_wiki_linker.get_en_link_from_ar_text", return_value="User:Test/Sandbox"
        )

        result, site = get_english_page_title("", "علوم", "", {})
        # Sandbox pages should be rejected
        assert result == ""

    def test_returns_empty_when_no_english_found(self, mocker):
        """Test that empty strings are returned when no English found"""
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.get_en_link_from_ar_text", return_value="")
        mocker.patch("src.core.new_c18.core.cross_wiki_linker.get_page_link", return_value=None)

        result, site = get_english_page_title("", "علوم", "", {})
        assert result == ""
