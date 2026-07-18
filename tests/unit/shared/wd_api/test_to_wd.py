"""
Unit tests for src/core/wd_api/to_wd.py module.
"""

from unittest.mock import MagicMock, patch

from src.shared.wd_api.to_wd import (
    log_to_wikidata_qid,
    makejson,
    post_wd_params,
)


class TestMakejson:
    def test_creates_valid_structure(self):
        result = makejson("P31", "4167836")
        assert result["mainsnak"]["property"] == "P31"
        assert result["mainsnak"]["datavalue"]["value"]["id"] == "Q4167836"
        assert result["type"] == "statement"

    def test_strips_q_prefix(self):
        result = makejson("P31", "Q123")
        assert result["mainsnak"]["datavalue"]["value"]["numeric-id"] == "123"
        assert result["mainsnak"]["datavalue"]["value"]["id"] == "Q123"


class TestPostWdParams:
    @patch("src.shared.wd_api.to_wd.get_session_post")
    def test_success_returns_true(self, mock_get_session):
        mock_api = MagicMock()
        mock_api.post_to_newapi.return_value = {"success": 1}
        mock_get_session.return_value = mock_api
        assert post_wd_params({"action": "test"}) is True

    @patch("src.shared.wd_api.to_wd.get_session_post")
    def test_failure_returns_false(self, mock_get_session):
        mock_api = MagicMock()
        mock_api.post_to_newapi.return_value = {"error": {}}
        mock_get_session.return_value = mock_api
        assert post_wd_params({"action": "test"}) is False


class TestAddLabels:
    def test_returns_false_when_no_qid(self):
        from src.shared.wd_api.to_wd import add_labels

        assert add_labels("", "label", "ar") is False

    def test_returns_false_when_empty_label(self):
        from src.shared.wd_api.to_wd import add_labels

        assert add_labels("Q123", "", "ar") is False


class TestLogToWikidataQid:
    @patch("src.shared.wd_api.to_wd.add_sitelinks_to_wikidata")
    @patch("src.shared.wd_api.to_wd.add_labels")
    def test_calls_both_functions(self, mock_labels, mock_sitelinks):
        log_to_wikidata_qid("title", "Q123")
        mock_sitelinks.assert_called_once_with("Q123", "title", "arwiki")
        mock_labels.assert_called_once_with("Q123", "title", "ar")
