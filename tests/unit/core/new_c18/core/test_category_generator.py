"""
Unit tests for src/core/new_c18/core/category_generator.py module.
"""

from unittest.mock import MagicMock, patch

from src.core.new_c18.core.category_generator import (
    _get_namespace_ids,
    fetch_category_members,
    translate_titles_to_ar,
)


class TestGetNamespaceIds:
    @patch("src.core.new_c18.core.category_generator.settings")
    @patch("src.core.new_c18.core.category_generator.DEFAULT_MEMBER_NAMESPACES", [0, 10, 14])
    @patch("src.core.new_c18.core.category_generator.STUB_MEMBER_NAMESPACES", [0, 14])
    def test_default_namespaces(self, mock_settings):
        mock_settings.category.stubs = False
        result = _get_namespace_ids()
        assert result == [0, 10, 14]

    @patch("src.core.new_c18.core.category_generator.settings")
    @patch("src.core.new_c18.core.category_generator.DEFAULT_MEMBER_NAMESPACES", [0, 10, 14])
    @patch("src.core.new_c18.core.category_generator.STUB_MEMBER_NAMESPACES", [0, 14])
    def test_stub_namespaces(self, mock_settings):
        mock_settings.category.stubs = True
        result = _get_namespace_ids()
        assert result == [0, 14]


class TestFetchCategoryMembers:
    @patch("src.core.new_c18.core.category_generator.load_main_api")
    def test_returns_titles(self, mock_load_api):
        mock_api = MagicMock()
        mock_api.CatDepth.return_value = {
            "Page1": {"ns": 0},
            "Page2": {"ns": 0},
        }
        mock_load_api.return_value = mock_api
        result = fetch_category_members("Category:Test", wiki="en", namespaces=[0])
        assert "Page1" in result
        assert "Page2" in result

    @patch("src.core.new_c18.core.category_generator.load_main_api")
    def test_filters_by_namespace(self, mock_load_api):
        mock_api = MagicMock()
        mock_api.CatDepth.return_value = {
            "Page1": {"ns": 0},
            "Cat1": {"ns": 14},
        }
        mock_load_api.return_value = mock_api
        result = fetch_category_members("Category:Test", wiki="en", namespaces=[0])
        assert "Page1" in result
        assert "Cat1" not in result


class TestTranslateTitlesToAr:
    @patch("src.core.new_c18.core.category_generator.find_LCN")
    @patch("src.core.new_c18.core.category_generator.settings")
    def test_returns_translated_titles(self, mock_settings, mock_find_lcn):
        mock_settings.EEn_site.code = "en"
        mock_find_lcn.return_value = {
            "Science": {"langlinks": {"ar": "علوم"}},
            "Math": {"langlinks": {"ar": "رياضيات"}},
        }
        result = translate_titles_to_ar(["Science", "Math"])
        assert "علوم" in result
        assert "رياضيات" in result

    @patch("src.core.new_c18.core.category_generator.find_LCN")
    @patch("src.core.new_c18.core.category_generator.settings")
    def test_skips_missing_translations(self, mock_settings, mock_find_lcn):
        mock_settings.EEn_site.code = "en"
        mock_find_lcn.return_value = {
            "Science": {"langlinks": {"en": "Science"}},
        }
        result = translate_titles_to_ar(["Science"])
        assert result == []

    @patch("src.core.new_c18.core.category_generator.find_LCN")
    @patch("src.core.new_c18.core.category_generator.settings")
    def test_empty_result(self, mock_settings, mock_find_lcn):
        mock_settings.EEn_site.code = "en"
        mock_find_lcn.return_value = None
        result = translate_titles_to_ar(["Unknown"])
        assert result == []
