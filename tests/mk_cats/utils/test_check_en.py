"""
Tests for src/mk_cats/utils/check_en.py

اختبارات لملف check_en.py - فحص القوالب الإنجليزية

This module tests:
- check_en_temps() - Check English templates for blacklisted items
"""

from unittest.mock import MagicMock, patch

import pytest


class TestCheckEnTemps:
    """Tests for check_en_temps function."""

    def test_returns_false_for_skipped_category(self, mocker):
        """Test that check_en_temps returns False for categories in skip_encats."""
        mocker.patch("src.mk_cats.utils.check_en.skip_encats", ["Category:Skip"])

        from src.mk_cats.utils.check_en import check_en_temps

        result = check_en_temps("Category:Skip")

        assert result is False

    def test_returns_true_when_no_category_data(self, mocker):
        """Test that check_en_temps returns True when no category data found."""
        mocker.patch("src.mk_cats.utils.check_en.skip_encats", [])
        mocker.patch("src.mk_cats.utils.check_en.find_LCN", return_value=None)

        from src.mk_cats.utils.check_en import check_en_temps

        result = check_en_temps("Category:Test")

        assert result is True

    def test_returns_true_when_no_templates(self, mocker):
        """Test that check_en_temps returns True when category has no templates."""
        mocker.patch("src.mk_cats.utils.check_en.skip_encats", [])
        mocker.patch("src.mk_cats.utils.check_en.find_LCN", return_value={"Category:Test": {}})

        from src.mk_cats.utils.check_en import check_en_temps

        result = check_en_temps("Category:Test")

        assert result is True

    def test_returns_true_for_allowed_templates(self, mocker):
        """Test that check_en_temps returns True for allowed templates."""
        mocker.patch("src.mk_cats.utils.check_en.skip_encats", [])
        mocker.patch("src.mk_cats.utils.check_en.NO_Templates_lower", ["badtemplate"])
        mocker.patch(
            "src.mk_cats.utils.check_en.find_LCN",
            return_value={"Category:Test": {"templates": ["Template:GoodTemplate"]}},
        )

        from src.mk_cats.utils.check_en import check_en_temps

        result = check_en_temps("Category:Test")

        assert result is True

    def test_returns_false_for_blacklisted_template(self, mocker):
        """Test that check_en_temps returns False for blacklisted templates."""
        mocker.patch("src.mk_cats.utils.check_en.skip_encats", [])
        mocker.patch("src.mk_cats.utils.check_en.NO_Templates_lower", ["badtemplate"])
        mocker.patch(
            "src.mk_cats.utils.check_en.find_LCN",
            return_value={"Category:Test": {"templates": ["Template:BadTemplate"]}},
        )

        from src.mk_cats.utils.check_en import check_en_temps

        result = check_en_temps("Category:Test")

        assert result is False

    def test_template_check_is_case_insensitive(self, mocker):
        """Test that template check is case insensitive."""
        mocker.patch("src.mk_cats.utils.check_en.skip_encats", [])
        mocker.patch("src.mk_cats.utils.check_en.NO_Templates_lower", ["badtemplate"])
        mocker.patch(
            "src.mk_cats.utils.check_en.find_LCN",
            return_value={"Category:Test": {"templates": ["Template:BADTEMPLATE"]}},
        )

        from src.mk_cats.utils.check_en import check_en_temps

        result = check_en_temps("Category:Test")

        assert result is False

    def test_removes_template_prefix(self, mocker):
        """Test that check_en_temps removes 'template:' prefix."""
        mocker.patch("src.mk_cats.utils.check_en.skip_encats", [])
        mocker.patch("src.mk_cats.utils.check_en.NO_Templates_lower", ["badtemplate"])
        mocker.patch(
            "src.mk_cats.utils.check_en.find_LCN",
            return_value={"Category:Test": {"templates": ["template:badtemplate"]}},
        )

        from src.mk_cats.utils.check_en import check_en_temps

        result = check_en_temps("Category:Test")

        assert result is False

    def test_calls_find_lcn_with_correct_params(self, mocker):
        """Test that check_en_temps calls find_LCN with correct parameters."""
        mocker.patch("src.mk_cats.utils.check_en.skip_encats", [])
        mock_find_lcn = mocker.patch("src.mk_cats.utils.check_en.find_LCN", return_value=None)

        from src.mk_cats.utils.check_en import check_en_temps

        check_en_temps("Category:Test")

        mock_find_lcn.assert_called_once_with("Category:Test", prop="templates|categories", first_site_code="en")

    def test_handles_empty_templates_list(self, mocker):
        """Test that check_en_temps handles empty templates list."""
        mocker.patch("src.mk_cats.utils.check_en.skip_encats", [])
        mocker.patch("src.mk_cats.utils.check_en.find_LCN", return_value={"Category:Test": {"templates": []}})

        from src.mk_cats.utils.check_en import check_en_temps

        result = check_en_temps("Category:Test")

        assert result is True

    def test_multiple_templates_with_one_blacklisted(self, mocker):
        """Test that check_en_temps returns False if any template is blacklisted."""
        mocker.patch("src.mk_cats.utils.check_en.skip_encats", [])
        mocker.patch("src.mk_cats.utils.check_en.NO_Templates_lower", ["badtemplate"])
        mocker.patch(
            "src.mk_cats.utils.check_en.find_LCN",
            return_value={
                "Category:Test": {
                    "templates": ["Template:GoodTemplate1", "Template:BadTemplate", "Template:GoodTemplate2"]
                }
            },
        )

        from src.mk_cats.utils.check_en import check_en_temps

        result = check_en_temps("Category:Test")

        assert result is False
