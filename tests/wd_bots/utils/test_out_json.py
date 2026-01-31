"""
Tests for src/wd_bots/utils/out_json.py

This module tests JSON output handling functions.
"""

from src.wd_bots.utils.out_json import (
    outbot_json,
)


class TestOutbotJson:
    """Tests for outbot_json function"""

    def test_returns_true_on_success(self):
        """Test that True is returned on success"""
        js_text = {"success": 1}

        result = outbot_json(js_text)

        assert result is True

    def test_returns_warn_on_no_error(self):
        """Test that 'warn' is returned when no error"""
        js_text = {"success": 0}

        result = outbot_json(js_text)

        assert result == "warn"

    def test_delegates_to_outbot_json_bot(self):
        """Test that error handling is delegated"""
        js_text = {"success": 0, "error": {"code": "origin-not-empty", "info": "Test error"}}

        result = outbot_json(js_text)

        assert result == "origin-not-empty"

    def test_handles_entity_response(self):
        """Test handling of entity response"""
        js_text = {"success": 1, "entity": {"id": "Q123", "sitelinks": {}}}

        result = outbot_json(js_text)

        assert result is True
