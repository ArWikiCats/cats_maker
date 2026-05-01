"""
Unit tests for src/core/wd_bots/to_wd.py module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.wd_bots.to_wd import (
    after_success,
    create_new_item,
    log_to_wikidata,
    log_to_wikidata_qid,
    makejson,
    outbot_json,
    outbot_json_bot,
    post_wd_params,
)


class TestOutbotJsonBot:
    def test_origin_not_empty(self):
        err = {"code": "origin-not-empty", "info": "test", "extradata": [""], "messages": [{}]}
        assert outbot_json_bot(err) == "origin-not-empty"

    def test_missingparam(self):
        err = {"code": "missingparam", "info": "test", "extradata": [""], "messages": [{}]}
        assert outbot_json_bot(err) == "warn"

    def test_modification_failed_wikibase_api_failed_modify(self):
        err = {
            "code": "modification-failed",
            "info": "test",
            "extradata": [""],
            "messages": [{"name": "wikibase-api-failed-modify", "html": {}}],
        }
        assert outbot_json_bot(err) == "wikibase-api-failed-modify"

    def test_modification_failed_label_equals_description(self):
        err = {
            "code": "modification-failed",
            "info": "test",
            "extradata": [""],
            "messages": [{"name": "wikibase-validator-label-equals-description", "html": {}}],
        }
        assert outbot_json_bot(err) == "wikibase-validator-label-equals-description"

    def test_modification_failed_same_description(self):
        err = {
            "code": "modification-failed",
            "info": "test",
            "extradata": [""],
            "messages": [{"name": "wikibase-validator-label-with-description-conflict", "parameters": ["a", "b", "c"]}],
        }
        assert outbot_json_bot(err) == "same description"

    def test_modification_failed_generic(self):
        err = {
            "code": "modification-failed",
            "info": "test",
            "extradata": [""],
            "messages": [{}],
        }
        assert outbot_json_bot(err) == "warn"

    def test_unresolved_redirect(self):
        err = {"code": "unresolved-redirect", "info": "", "extradata": [""], "messages": [{}]}
        assert outbot_json_bot(err) == "unresolved-redirect"

    def test_failed_save_returns_false(self):
        err = {"code": "failed-save", "info": "", "extradata": [""], "messages": [{}]}
        assert outbot_json_bot(err) is False

    def test_no_external_page(self):
        err = {"code": "no-external-page", "info": "", "extradata": [""], "messages": [{}]}
        assert outbot_json_bot(err) is False

    def test_unknown_code(self):
        err = {"code": "unknown-error", "info": "", "extradata": [""], "messages": [{}]}
        assert outbot_json_bot(err) == "unknown-error"


class TestOutbotJson:
    def test_no_error_returns_warn(self):
        js_text = {"success": 1}
        assert outbot_json(js_text) == "warn"

    def test_with_error_delegates(self):
        js_text = {"error": {"code": "missingparam", "info": "", "extradata": [""], "messages": [{}]}}
        assert outbot_json(js_text) == "warn"

    def test_with_fi_and_line(self):
        js_text = {"error": {"code": "test", "info": "", "extradata": [""], "messages": [{}]}}
        result = outbot_json(js_text, fi="file", line="line")
        assert result == "test"


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

    def test_none_numeric_returns_none(self):
        assert makejson("P31", None) is None


class TestPostWdParams:
    @patch("src.core.wd_bots.to_wd.get_session_post")
    @patch("src.core.wd_bots.to_wd.after_success")
    def test_success_returns_true(self, mock_after, mock_get_session):
        mock_api = MagicMock()
        mock_api.post_to_newapi.return_value = {"success": 1}
        mock_get_session.return_value = mock_api
        assert post_wd_params({"action": "test"}) is True

    @patch("src.core.wd_bots.to_wd.get_session_post")
    @patch("src.core.wd_bots.to_wd.outbot_json")
    def test_failure_returns_false(self, mock_outbot, mock_get_session):
        mock_api = MagicMock()
        mock_api.post_to_newapi.return_value = {"error": {}}
        mock_get_session.return_value = mock_api
        assert post_wd_params({"action": "test"}) is False


class TestAddLabels:
    @patch("src.core.wd_bots.to_wd.is_wd_lag_high", return_value=True)
    def test_returns_empty_when_lag_high(self, _):
        from src.core.wd_bots.to_wd import add_labels

        assert add_labels("Q123", "label", "ar") == ""

    @patch("src.core.wd_bots.to_wd.is_wd_lag_high", return_value=False)
    def test_returns_false_when_no_qid(self, _):
        from src.core.wd_bots.to_wd import add_labels

        assert add_labels("", "label", "ar") is False

    @patch("src.core.wd_bots.to_wd.is_wd_lag_high", return_value=False)
    def test_returns_false_when_empty_label(self, _):
        from src.core.wd_bots.to_wd import add_labels

        assert add_labels("Q123", "", "ar") is False


class TestLogToWikidataQid:
    @patch("src.core.wd_bots.to_wd.add_sitelinks_to_wikidata")
    @patch("src.core.wd_bots.to_wd.add_labels")
    def test_calls_both_functions(self, mock_labels, mock_sitelinks):
        log_to_wikidata_qid("title", "Q123")
        mock_sitelinks.assert_called_once_with("Q123", "title", "arwiki")
        mock_labels.assert_called_once_with("Q123", "title", "ar")
