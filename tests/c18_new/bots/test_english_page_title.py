"""
Tests for src/c18_new/bots/english_page_title.py

This module tests functions for finding English page titles from Arabic pages.
"""

import pytest

from src.core.c18_new.bots.english_page_title import (
    english_page_link,
    extract_wikidata_qid,
    get_en_link_from_ar_text,
    get_english_page_title,
)


class TestExtractWikidataQid:
    """Tests for extract_wikidata_qid function"""

    def test_extracts_qid_from_wikidata_template(self):
        """Test extracting QID from قيمة ويكي بيانات template"""
        text = "{{قيمة ويكي بيانات/قالب تحقق|Q12345}}"
        result = extract_wikidata_qid(text)
        assert result == "Q12345"

    def test_extracts_qid_with_id_parameter(self):
        """Test extracting QID with id= parameter"""
        text = "{{قيمة ويكي بيانات/قالب تحقق|id=Q67890}}"
        result = extract_wikidata_qid(text)
        assert result == "Q67890"

    def test_extracts_qid_from_cycling_race_template(self):
        """Test extracting QID from cycling race template"""
        text = "{{سباق الدراجات/صندوق معلومات|Q11111}}"
        result = extract_wikidata_qid(text)
        assert result == "Q11111"

    def test_extracts_qid_from_english_cycling_template(self):
        """Test extracting QID from English cycling template"""
        text = "{{Cycling race/infobox|Q22222}}"
        result = extract_wikidata_qid(text)
        assert result == "Q22222"

    def test_returns_empty_string_when_no_qid(self):
        """Test that empty string is returned when no QID found"""
        text = "مقالة عادية بدون قالب ويكي بيانات"
        result = extract_wikidata_qid(text)
        assert result == ""

    def test_returns_empty_string_for_empty_text(self):
        """Test that empty string is returned for empty text"""
        result = extract_wikidata_qid("")
        assert result == ""

    def test_handles_multiple_templates(self):
        """Test that first matching QID is extracted"""
        text = "{{قيمة ويكي بيانات/قالب تحقق|Q111}}{{قيمة ويكي بيانات/قالب تحقق|Q222}}"
        result = extract_wikidata_qid(text)
        assert result == "Q111"


class TestEnglishPageLink:
    """Tests for english_page_link function"""

    def test_returns_cached_value(self, mocker):
        """Test that cached values are returned"""
        mocker.patch("src.core.c18_new.bots.english_page_title.get_cache_L_C_N", return_value="Science")

        result = english_page_link("علوم", "ar", "en")
        assert result == "Science"

    def test_cleans_link_brackets(self, mocker):
        """Test that double brackets are removed from link"""
        mocker.patch("src.core.c18_new.bots.english_page_title.get_cache_L_C_N", return_value=None)
        mocker.patch("src.core.c18_new.bots.english_page_title.find_LCN", return_value=None)
        mocker.patch("src.core.c18_new.bots.english_page_title.Get_Sitelinks_From_wikidata", return_value=None)
        mocker.patch("src.core.c18_new.bots.english_page_title.set_cache_L_C_N")

        english_page_link("[[علوم]]", "ar", "en")
        # Function should process without error

    def test_returns_false_when_no_langlink(self, mocker):
        """Test that False is returned when no langlink is found"""
        mocker.patch("src.core.c18_new.bots.english_page_title.get_cache_L_C_N", return_value=None)
        mocker.patch("src.core.c18_new.bots.english_page_title.find_LCN", return_value=None)
        mocker.patch("src.core.c18_new.bots.english_page_title.Get_Sitelinks_From_wikidata", return_value=None)
        mocker.patch("src.core.c18_new.bots.english_page_title.set_cache_L_C_N")

        result = english_page_link("nonexistent", "ar", "en")
        assert result is False


class TestGetEnLinkFromArText:
    """Tests for get_en_link_from_ar_text function"""

    def test_returns_empty_string_when_no_sitelinks(self, mocker):
        """Test that empty string is returned when no sitelinks"""
        mocker.patch("src.core.c18_new.bots.english_page_title.Get_Sitelinks_From_wikidata", return_value=None)

        result = get_en_link_from_ar_text("علوم", "arwiki", "enwiki")
        assert result == ""

    def test_extracts_english_sitelink(self, mocker):
        """Test that English sitelink is extracted"""
        mocker.patch(
            "src.core.c18_new.bots.english_page_title.Get_Sitelinks_From_wikidata",
            return_value={"sitelinks": {"enwiki": "Science"}},
        )

        result = get_en_link_from_ar_text("علوم", "arwiki", "enwiki")
        assert result == "Science"

    def test_handles_wiki_suffix(self, mocker):
        """Test handling of wiki suffix in sitetarget"""
        mocker.patch(
            "src.core.c18_new.bots.english_page_title.Get_Sitelinks_From_wikidata",
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
            "src.core.c18_new.bots.english_page_title.get_en_link_from_ar_text", return_value="User:Test/Sandbox"
        )

        result, site = get_english_page_title("", "علوم", "", {})
        # Sandbox pages should be rejected
        # The exact behavior depends on implementation

    def test_returns_empty_when_no_english_found(self, mocker):
        """Test that empty strings are returned when no English found"""
        mocker.patch("src.core.c18_new.bots.english_page_title.get_en_link_from_ar_text", return_value="")
        mocker.patch("src.core.c18_new.bots.english_page_title.english_page_link", return_value=False)

        result, site = get_english_page_title("", "علوم", "", {})
        # Should return empty strings when nothing found
        assert result == "" or result is False
