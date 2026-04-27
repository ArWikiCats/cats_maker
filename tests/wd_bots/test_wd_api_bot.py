"""
Tests for wd_api_bot.py

This module tests Wikidata API functions.
"""

import pytest

from src.core.wd_bots.wd_api_bot import (
    Get_infos_wikidata,
    Get_P373_API,
    Get_Sitelinks_from_qid,
    Get_Sitelinks_From_wikidata,
    format_labels_descriptions,
    format_sitelinks,
)


class TestFormatSitelinks:
    """Tests for format_sitelinks function"""

    def test_formats_sitelinks_correctly(self):
        """Test that sitelinks are formatted correctly"""
        sitelinks = {
            "enwiki": {"site": "enwiki", "title": "Science"},
            "arwiki": {"site": "arwiki", "title": "علوم"},
        }
        result = format_sitelinks(sitelinks)
        assert result["enwiki"] == "Science"
        assert result["arwiki"] == "علوم"

    def test_returns_empty_dict_for_empty_input(self):
        """Test that empty input returns empty dict"""
        result = format_sitelinks({})
        assert result == {}

    def test_handles_various_sites(self):
        """Test handling of various wiki sites"""
        sitelinks = {
            "dewiki": {"site": "dewiki", "title": "Wissenschaft"},
            "frwiki": {"site": "frwiki", "title": "Science"},
            "commonswiki": {"site": "commonswiki", "title": "Category:Science"},
        }
        result = format_sitelinks(sitelinks)
        assert len(result) == 3


class TestFormatLabelsDescriptions:
    """Tests for format_labels_descriptions function"""

    def test_formats_labels_correctly(self):
        """Test that labels are formatted correctly"""
        labels = {
            "en": {"language": "en", "value": "Science"},
            "ar": {"language": "ar", "value": "علوم"},
        }
        result = format_labels_descriptions(labels)
        assert result["en"] == "Science"
        assert result["ar"] == "علوم"

    def test_returns_empty_dict_for_empty_input(self):
        """Test that empty input returns empty dict"""
        result = format_labels_descriptions({})
        assert result == {}


class TestGetInfosWikidata:
    """Tests for Get_infos_wikidata function"""

    def test_returns_default_table_on_no_response(self, mocker):
        """Test that function returns default table when API returns None"""
        mocker.patch("src.core.wd_bots.wd_api_bot.submitAPI", return_value=None)

        params = {"action": "wbgetentities", "ids": "Q12345", "props": "sitelinks|labels"}
        result = Get_infos_wikidata(params)

        assert result == {"labels": {}, "sitelinks": {}, "q": ""}

    def test_returns_default_table_on_failed_success(self, mocker):
        """Test that function returns default table when success is not 1"""
        mocker.patch("src.core.wd_bots.wd_api_bot.submitAPI", return_value={"success": 0})

        params = {"action": "wbgetentities", "ids": "Q12345", "props": "sitelinks"}
        result = Get_infos_wikidata(params)

        assert result == {"labels": {}, "sitelinks": {}, "q": ""}

    def test_returns_default_table_for_missing_entity(self, mocker):
        """Test that function returns default table for -1 entity"""
        mocker.patch("src.core.wd_bots.wd_api_bot.submitAPI", return_value={"success": 1, "entities": {"-1": {}}})

        params = {"action": "wbgetentities", "ids": "Q999999999", "props": "sitelinks"}
        result = Get_infos_wikidata(params)

        assert result == {"labels": {}, "sitelinks": {}, "q": ""}

    def test_extracts_data_correctly(self, mocker):
        """Test that function extracts data from valid response"""
        mock_response = {
            "success": 1,
            "entities": {
                "Q12345": {
                    "labels": {"en": {"language": "en", "value": "Test"}},
                    "sitelinks": {"enwiki": {"site": "enwiki", "title": "Test Page"}},
                }
            },
        }
        mocker.patch("src.core.wd_bots.wd_api_bot.submitAPI", return_value=mock_response)

        params = {"action": "wbgetentities", "ids": "Q12345", "props": "sitelinks|labels"}
        result = Get_infos_wikidata(params)

        assert result["q"] == "Q12345"
        assert result["labels"]["en"] == "Test"
        assert result["sitelinks"]["enwiki"] == "Test Page"


class TestGetSitelinksFromWikidata:
    """Tests for Get_Sitelinks_From_wikidata function"""

    def test_adds_wiki_suffix_if_missing(self, mocker):
        """Test that 'wiki' suffix is added to site code"""
        mock_info = mocker.patch(
            "src.core.wd_bots.wd_api_bot.Get_infos_wikidata", return_value={"sitelinks": {}, "q": ""}
        )
        Get_Sitelinks_From_wikidata.cache_clear()

        Get_Sitelinks_From_wikidata("en", "Test")

        call_args = mock_info.call_args[0][0]
        assert call_args["sites"] == "enwiki"

    def test_returns_specific_sitelink_when_ssite_provided(self, mocker):
        """Test that specific sitelink is returned when ssite is provided"""
        mocker.patch(
            "src.core.wd_bots.wd_api_bot.Get_infos_wikidata",
            return_value={"sitelinks": {"arwiki": "علوم"}, "q": "Q123"},
        )
        Get_Sitelinks_From_wikidata.cache_clear()

        result = Get_Sitelinks_From_wikidata("en", "Science")

        assert result["sitelinks"]["arwiki"] == "علوم"

    def test_returns_table_when_no_ssite(self, mocker):
        """Test that full table is returned when ssite is not provided"""
        mock_table = {"sitelinks": {"enwiki": "Science"}, "q": "Q123"}
        mocker.patch("src.core.wd_bots.wd_api_bot.Get_infos_wikidata", return_value=mock_table)
        Get_Sitelinks_From_wikidata.cache_clear()

        result = Get_Sitelinks_From_wikidata("en", "Science")

        assert "sitelinks" in result
        assert "q" in result


class TestGetP373API:
    """Tests for Get_P373_API function"""

    def test_returns_empty_string_on_no_response(self, mocker):
        """Test that function returns empty string when API returns None"""
        mocker.patch("src.core.wd_bots.wd_api_bot.submitAPI", return_value=None)

        result = Get_P373_API("Q12345")

        assert result == ""

    def test_extracts_commons_category(self, mocker):
        """Test that function extracts Commons category from sitelinks"""
        mock_response = {
            "entities": {"Q123": {"sitelinks": {"commonswiki": {"title": "Category:Science"}}, "claims": {}}}
        }
        mocker.patch("src.core.wd_bots.wd_api_bot.submitAPI", return_value=mock_response)

        result = Get_P373_API("Q123")

        assert result == "Science"

    def test_extracts_p373_from_claims(self, mocker):
        """Test that function extracts P373 value from claims"""
        mock_response = {
            "entities": {
                "Q123": {
                    "sitelinks": {},
                    "claims": {"P373": [{"mainsnak": {"datavalue": {"type": "string", "value": "Test Category"}}}]},
                }
            }
        }
        mocker.patch("src.core.wd_bots.wd_api_bot.submitAPI", return_value=mock_response)

        result = Get_P373_API("Q123")

        assert result == "Test Category"
