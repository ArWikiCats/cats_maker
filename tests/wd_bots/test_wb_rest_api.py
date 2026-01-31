"""
Tests for src/wd_bots/wb_rest_api.py

This module tests Wikidata REST API functions.
"""

import pytest

from src.wd_bots.wb_rest_api import (
    Get_one_qid_info,
    Get_P373,
    get_rest_result,
    get_wd_api_bot,
    wd_cach,
)


class TestWdCach:
    """Tests for wd_cach cache"""

    def test_is_dict(self):
        """Test that wd_cach is a dictionary"""
        assert isinstance(wd_cach, dict)


class TestGetWdApiBot:
    """Tests for get_wd_api_bot function"""

    def test_returns_api_bot(self, mocker):
        """Test that API bot is returned"""
        mock_bot = mocker.MagicMock()
        mocker.patch("src.wd_bots.wb_rest_api.NewHimoAPIBot", return_value=mock_bot)

        get_wd_api_bot.cache_clear()

        result = get_wd_api_bot()

        assert result is not None

    def test_caches_result(self, mocker):
        """Test that result is cached"""
        mock_bot = mocker.MagicMock()
        mock_class = mocker.patch("src.wd_bots.wb_rest_api.NewHimoAPIBot", return_value=mock_bot)

        get_wd_api_bot.cache_clear()

        get_wd_api_bot()
        get_wd_api_bot()

        assert mock_class.call_count == 1


class TestGetRestResult:
    """Tests for get_rest_result function"""

    def test_delegates_to_api_bot(self, mocker):
        """Test that function delegates to API bot"""
        mock_bot = mocker.MagicMock()
        mock_bot.get_rest_result.return_value = {"test": "data"}
        mocker.patch("src.wd_bots.wb_rest_api.get_wd_api_bot", return_value=mock_bot)

        result = get_rest_result("https://example.com")

        mock_bot.get_rest_result.assert_called_with("https://example.com")
        assert result == {"test": "data"}


class TestGetOneQidInfo:
    """Tests for Get_one_qid_info function"""

    def test_returns_cached_value(self, mocker):
        """Test that cached values are returned"""
        # Add to cache
        wd_cach[("Q123", None)] = {"cached": "data"}

        result = Get_one_qid_info("Q123")

        assert result == {"cached": "data"}

        # Clean up
        del wd_cach[("Q123", None)]

    def test_returns_default_structure(self, mocker):
        """Test that default structure is returned"""
        mocker.patch("src.wd_bots.wb_rest_api.get_rest_result", return_value={})

        result = Get_one_qid_info("Q999999")

        assert "labels" in result
        assert "descriptions" in result
        assert "aliases" in result
        assert "sitelinks" in result
        assert "statements" in result
        assert "qid" in result

    def test_extracts_labels(self, mocker):
        """Test that labels are extracted"""
        mocker.patch("src.wd_bots.wb_rest_api.get_rest_result", return_value={"labels": {"en": "Test", "ar": "اختبار"}})

        result = Get_one_qid_info("Q12345_test")

        assert result["labels"]["en"] == "Test"
        assert result["labels"]["ar"] == "اختبار"

    def test_extracts_sitelinks(self, mocker):
        """Test that sitelinks are extracted"""
        mocker.patch(
            "src.wd_bots.wb_rest_api.get_rest_result",
            return_value={"sitelinks": {"enwiki": {"title": "Test Page"}, "arwiki": {"title": "صفحة اختبار"}}},
        )

        result = Get_one_qid_info("Q12346_test")

        assert result["sitelinks"]["enwiki"] == "Test Page"
        assert result["sitelinks"]["arwiki"] == "صفحة اختبار"

    def test_handles_only_parameter(self, mocker):
        """Test handling of 'only' parameter"""
        mock_get = mocker.patch("src.wd_bots.wb_rest_api.get_rest_result", return_value={"en": "Test"})

        Get_one_qid_info("Q12347_test", only="labels")

        call_args = mock_get.call_args[0][0]
        assert "/labels" in call_args


class TestGetP373:
    """Tests for Get_P373 function"""

    def test_extracts_p373_from_statements(self, mocker):
        """Test that P373 is extracted from statements"""
        mocker.patch(
            "src.wd_bots.wb_rest_api.Get_one_qid_info",
            return_value={"statements": {"P373": [{"value": {"content": "Science"}}]}, "sitelinks": {}},
        )

        result = Get_P373("Q123")

        assert result == "Science"

    def test_falls_back_to_commonswiki_sitelink(self, mocker):
        """Test fallback to commonswiki sitelink"""
        mocker.patch(
            "src.wd_bots.wb_rest_api.Get_one_qid_info",
            return_value={"statements": {}, "sitelinks": {"commonswiki": "Category:Science"}},
        )

        result = Get_P373("Q456")

        assert result == "Science"

    def test_removes_category_prefix_from_sitelink(self, mocker):
        """Test that Category: prefix is removed from sitelink"""
        mocker.patch(
            "src.wd_bots.wb_rest_api.Get_one_qid_info",
            return_value={"statements": {}, "sitelinks": {"commonswiki": "Category:Test Category"}},
        )

        result = Get_P373("Q789")

        assert result == "Test Category"

    def test_returns_empty_string_when_not_found(self, mocker):
        """Test that empty string is returned when not found"""
        mocker.patch("src.wd_bots.wb_rest_api.Get_one_qid_info", return_value={"statements": {}, "sitelinks": {}})

        result = Get_P373("Q000")

        assert result == ""
