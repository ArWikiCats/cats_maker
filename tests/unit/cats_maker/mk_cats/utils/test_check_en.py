"""
Tests for check_en.py

This module tests:
- check_en_temps() - Check English templates for blacklisted items
"""

from unittest.mock import MagicMock

import pytest

from src.cats_maker.mk_cats.utils.check_en import check_en_temps


@pytest.fixture(autouse=True)
def patch_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set default patches for SKIP_ENCATS and EN_FALSE_TEMPLATES_LOWERS."""
    monkeypatch.setattr("src.cats_maker.mk_cats.utils.check_en.SKIP_ENCATS", [])
    monkeypatch.setattr("src.cats_maker.mk_cats.utils.check_en.EN_FALSE_TEMPLATES_LOWERS", ["badtemplate"])


@pytest.fixture
def mock_find_page_data(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Fixture to mock find_page_data function."""
    _mock = MagicMock(return_value=None)
    monkeypatch.setattr("src.cats_maker.mk_cats.utils.check_en.LangLinksClient.find_page_data", _mock)
    return _mock


class TestCheckEnTemps:
    """Tests for check_en_temps function."""

    def test_returns_false_for_skipped_category(
        self, monkeypatch: pytest.MonkeyPatch, mock_find_page_data: MagicMock
    ) -> None:
        """Test that check_en_temps returns False for categories in SKIP_ENCATS."""
        monkeypatch.setattr("src.cats_maker.mk_cats.utils.check_en.SKIP_ENCATS", ["Category:Skip"])

        result = check_en_temps("Category:Skip")

        assert result is False

    def test_returns_true_when_no_category_data(self, mock_find_page_data: MagicMock) -> None:
        """Test that check_en_temps returns True when no category data found."""
        mock_find_page_data.return_value = None

        result = check_en_temps("Category:Test")

        assert result is True

    def test_returns_true_when_no_templates(self, mock_find_page_data: MagicMock) -> None:
        """Test that check_en_temps returns True when category has no templates."""
        mock_find_page_data.return_value = {"Category:Test": {}}

        result = check_en_temps("Category:Test")

        assert result is True

    def test_returns_true_for_allowed_templates(self, mock_find_page_data: MagicMock) -> None:
        """Test that check_en_temps returns True for allowed templates."""
        mock_find_page_data.return_value = {"Category:Test": {"templates": ["Template:GoodTemplate"]}}

        result = check_en_temps("Category:Test")

        assert result is True

    def test_returns_false_for_blacklisted_template(self, mock_find_page_data: MagicMock) -> None:
        """Test that check_en_temps returns False for blacklisted templates."""
        mock_find_page_data.return_value = {"Category:Test": {"templates": ["Template:BadTemplate"]}}

        result = check_en_temps("Category:Test")

        assert result is False

    def test_template_check_is_case_insensitive(self, mock_find_page_data: MagicMock) -> None:
        """Test that template check is case insensitive."""
        mock_find_page_data.return_value = {"Category:Test": {"templates": ["Template:BADTEMPLATE"]}}

        result = check_en_temps("Category:Test")

        assert result is False

    def test_removes_template_prefix(self, mock_find_page_data: MagicMock) -> None:
        """Test that check_en_temps removes 'template:' prefix."""
        mock_find_page_data.return_value = {"Category:Test": {"templates": ["template:badtemplate"]}}

        result = check_en_temps("Category:Test")

        assert result is False

    def test_calls_find_lcn_with_correct_params(self, mock_find_page_data: MagicMock) -> None:
        """Test that check_en_temps calls find_page_data with correct parameters."""
        check_en_temps("Category:Test")

        mock_find_page_data.assert_called_once_with("Category:Test", prop="templates|categories", site_code="en")

    def test_handles_empty_templates_list(self, mock_find_page_data: MagicMock) -> None:
        """Test that check_en_temps handles empty templates list."""
        mock_find_page_data.return_value = {"Category:Test": {"templates": []}}

        result = check_en_temps("Category:Test")

        assert result is True

    def test_multiple_templates_with_one_blacklisted(self, mock_find_page_data: MagicMock) -> None:
        """Test that check_en_temps returns False if any template is blacklisted."""
        mock_find_page_data.return_value = {
            "Category:Test": {"templates": ["Template:GoodTemplate1", "Template:BadTemplate", "Template:GoodTemplate2"]}
        }

        result = check_en_temps("Category:Test")

        assert result is False
