"""
Tests for categorytext.py

This module tests category text generation functions.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.mk_cats.categorytext import (
    LocalLanguageLinks,
    category_mapping,
    fetch_commons_category,
    generate_category_text,
    generate_portal_content,
    get_page_link_data,
)

# ===== Tests for get_page_link_data =====


class TestGetPageLinkData:
    """Tests for get_page_link_data function"""

    def test_returns_empty_when_page_links_is_none(self, mocker):
        """Test that get_page_link_data returns empty list when page_links returns None"""
        mock_api = MagicMock()
        mock_page = MagicMock()
        mock_page.page_links.return_value = None
        mock_api.MainPage.return_value = mock_page
        mocker.patch("src.mk_cats.categorytext.load_main_api", return_value=mock_api)

        result = get_page_link_data("TestPage", "en", 100)

        assert result == []
        mock_api.MainPage.assert_called_once_with("TestPage")

    def test_returns_empty_when_page_links_is_empty(self, mocker):
        """Test that get_page_link_data returns empty list for empty page links"""
        mock_api = MagicMock()
        mock_page = MagicMock()
        mock_page.page_links.return_value = []
        mock_api.MainPage.return_value = mock_page
        mocker.patch("src.mk_cats.categorytext.load_main_api", return_value=mock_api)

        result = get_page_link_data("TestPage", "en", 100)

        assert result == []

    def test_filters_by_namespace(self, mocker):
        """Test that get_page_link_data filters results by namespace"""
        mock_api = MagicMock()
        mock_page = MagicMock()
        mock_page.page_links.return_value = [
            {"ns": 100, "title": "Portal:Science", "exists": True},
            {"ns": 14, "title": "تصنيف:علوم", "exists": True},
            {"ns": 100, "title": "Portal:History", "exists": True},
        ]
        mock_api.MainPage.return_value = mock_page
        mocker.patch("src.mk_cats.categorytext.load_main_api", return_value=mock_api)

        result = get_page_link_data("TestPage", "en", 100)

        assert result == ["Portal:Science", "Portal:History"]

    def test_excludes_non_existing_pages(self, mocker):
        """Test that get_page_link_data excludes pages where exists is False"""
        mock_api = MagicMock()
        mock_page = MagicMock()
        mock_page.page_links.return_value = [
            {"ns": 100, "title": "Portal:Science", "exists": True},
            {"ns": 100, "title": "Portal:History", "exists": False},
        ]
        mock_api.MainPage.return_value = mock_page
        mocker.patch("src.mk_cats.categorytext.load_main_api", return_value=mock_api)

        result = get_page_link_data("TestPage", "en", 100)

        assert result == ["Portal:Science"]

    def test_excludes_pages_without_title(self, mocker):
        """Test that get_page_link_data excludes pages with no title"""
        mock_api = MagicMock()
        mock_page = MagicMock()
        mock_page.page_links.return_value = [
            {"ns": 100, "title": "Portal:Science", "exists": True},
            {"ns": 100, "title": "", "exists": True},
            {"ns": 100, "exists": True},
        ]
        mock_api.MainPage.return_value = mock_page
        mocker.patch("src.mk_cats.categorytext.load_main_api", return_value=mock_api)

        result = get_page_link_data("TestPage", "en", 100)

        assert result == ["Portal:Science"]

    def test_filters_with_namespace_10(self, mocker):
        """Test that get_page_link_data filters with namespace 10"""
        mock_api = MagicMock()
        mock_page = MagicMock()
        mock_page.page_links.return_value = [
            {"ns": 10, "title": "Template:Stub", "exists": True},
            {"ns": 100, "title": "Portal:Science", "exists": True},
        ]
        mock_api.MainPage.return_value = mock_page
        mocker.patch("src.mk_cats.categorytext.load_main_api", return_value=mock_api)

        result = get_page_link_data("TestPage", "en", 10)

        assert result == ["Template:Stub"]

    def test_calls_load_main_api_with_correct_sitecode(self, mocker):
        """Test that load_main_api is called with the correct sitecode"""
        mock_api = MagicMock()
        mock_page = MagicMock()
        mock_page.page_links.return_value = []
        mock_api.MainPage.return_value = mock_page
        mock_load = mocker.patch("src.mk_cats.categorytext.load_main_api", return_value=mock_api)

        get_page_link_data("TestPage", "ar", 100)

        mock_load.assert_called_once_with("ar")


# ===== Tests for fetch_commons_category =====


class TestFetchCommonsCategory:
    """Tests for fetch_commons_category function"""

    def test_returns_template_when_p373_exists(self, mocker):
        """Test that fetch_commons_category returns a template when P373 value exists"""
        mocker.patch("src.mk_cats.categorytext.Get_P373_API", return_value="Yemen")

        result = fetch_commons_category("Category:Yemen", "Q805")

        assert result == "{{تصنيف كومنز|Yemen}}"

    def test_returns_empty_when_p373_is_empty(self, mocker):
        """Test that fetch_commons_category returns empty string when P373 is empty"""
        mocker.patch("src.mk_cats.categorytext.Get_P373_API", return_value="")

        result = fetch_commons_category("Category:Science", "Q123")

        assert result == ""

    def test_returns_empty_when_p373_is_none(self, mocker):
        """Test that fetch_commons_category returns empty string when P373 is None"""
        mocker.patch("src.mk_cats.categorytext.Get_P373_API", return_value=None)

        result = fetch_commons_category("Category:Science", "Q123")

        assert result == ""

    def test_calls_get_p373_api_with_correct_args(self, mocker):
        """Test that Get_P373_API is called with correct arguments"""
        mock_p373 = mocker.patch("src.mk_cats.categorytext.Get_P373_API", return_value="Test")

        fetch_commons_category("Category:Test", "Q999")

        mock_p373.assert_called_once_with(q="Q999", titles="Category:Test", sites="enwiki")


# ===== Tests for generate_portal_content =====


class TestGeneratePortalContent:
    """Tests for generate_portal_content function"""

    def test_returns_empty_string_when_no_portals(self, mocker):
        """Test that generate_portal_content returns empty string when no portals found"""
        mocker.patch("src.mk_cats.categorytext.get_page_link_data", return_value=[])

        result = generate_portal_content("تصنيف:تصنيف_بدون_بوابات", "Category:NoPortals")

        assert result == ""

    def test_returns_string_and_empty_list_with_return_list(self, mocker):
        """Test that generate_portal_content returns tuple when return_list=True"""
        mocker.patch("src.mk_cats.categorytext.get_page_link_data", return_value=[])

        result = generate_portal_content("تصنيف:اختبار", "Category:Test", return_list=True)

        assert result == ("", [])

    def test_translates_english_portals_to_arabic(self, mocker):
        """Test that English portal names are translated to Arabic"""
        mocker.patch("src.mk_cats.categorytext.get_page_link_data", return_value=["Portal:Olympics"])

        result = generate_portal_content("تصنيف:ألعاب أولمبية", "Category:Olympics")

        assert "ألعاب أولمبية" in result
        assert "{{بوابة|" in result

    def test_translates_multiple_portals(self, mocker):
        """Test that multiple portals are translated and joined"""
        mocker.patch("src.mk_cats.categorytext.get_page_link_data", return_value=["Portal:Olympics", "Portal:Iceland"])

        result = generate_portal_content("تصنيف:ألعاب أولمبية", "Category:Olympics")

        assert "ألعاب أولمبية" in result
        assert "آيسلندا" in result

    def test_adds_portal_from_category_mapping(self, mocker):
        """Test that portals from category_mapping are added based on title content"""
        mocker.patch("src.mk_cats.categorytext.get_page_link_data", return_value=[])

        # Title contains "أفلام" which maps to "سينما"
        result = generate_portal_content("تصنيف:أفلام مصرية", "Category:Egyptian films")

        assert "سينما" in result

    def test_adds_portal_from_local_language_links(self, mocker):
        """Test that portals from LocalLanguageLinks are added based on title content"""
        mocker.patch("src.mk_cats.categorytext.get_page_link_data", return_value=[])

        # Title contains "فلسطين" which is in LocalLanguageLinks
        result = generate_portal_content("تصنيف:تاريخ فلسطين", "Category:History of Palestine")

        assert "فلسطين" in result

    def test_adds_portal_from_title_start(self, mocker):
        """Test that portals are matched at the start of the title"""
        mocker.patch("src.mk_cats.categorytext.get_page_link_data", return_value=[])

        # Title starts with "تصنيف:اليمن "
        result = generate_portal_content("تصنيف:اليمن في القرن العشرين", "Category:Yemen in 20th century")

        assert "اليمن" in result

    def test_adds_portal_from_title_end(self, mocker):
        """Test that portals are matched at the end of the title"""
        mocker.patch("src.mk_cats.categorytext.get_page_link_data", return_value=[])

        result = generate_portal_content("تصنيف:تاريخ اليمن", "Category:History of Yemen")

        assert "اليمن" in result

    def test_no_duplicate_portals(self, mocker):
        """Test that portals are not duplicated"""
        mocker.patch("src.mk_cats.categorytext.get_page_link_data", return_value=["Portal:Iceland"])

        # Title contains "آيسلندا" and also portal link has Iceland
        result = generate_portal_content("تصنيف:تاريخ آيسلندا", "Category:History of Iceland", return_list=True)

        litp, lilo = result
        assert lilo.count("آيسلندا") == 1

    def test_returns_list_when_return_list_true(self, mocker):
        """Test that generate_portal_content returns list when return_list=True"""
        mocker.patch("src.mk_cats.categorytext.get_page_link_data", return_value=["Portal:Iceland"])

        litp, lilo = generate_portal_content("تصنيف:اختبار", "Category:Test", return_list=True)

        assert isinstance(lilo, list)
        assert "آيسلندا" in lilo

    def test_format_with_multiple_portals(self, mocker):
        """Test portal format with multiple portals uses pipe separator"""
        mocker.patch("src.mk_cats.categorytext.get_page_link_data", return_value=["Portal:Iceland", "Portal:Olympics"])

        result = generate_portal_content("تصنيف:اختبار", "Category:Test")

        assert "{{بوابة|" in result
        assert "|" in result.split("{{بوابة|")[1].split("}}")[0]

    def test_ignores_unknown_portal_names(self, mocker):
        """Test that unknown portal names are ignored"""
        mocker.patch("src.mk_cats.categorytext.get_page_link_data", return_value=["Portal:UnknownPortalXYZ"])

        result = generate_portal_content("تصنيف:اختبار", "Category:Test")

        assert result == ""

    def test_category_mapping_in_category_not_duplicated(self, mocker):
        """Test that category_mapping portals are not duplicated if already in list"""
        mocker.patch("src.mk_cats.categorytext.get_page_link_data", return_value=["Portal:Olympics"])

        # Title contains "الألعاب الأولمبية" which maps to "ألعاب أولمبية"
        # The portal link also gives "ألعاب أولمبية"
        result = generate_portal_content("تصنيف:الألعاب الأولمبية", "Category:Olympics", return_list=True)

        litp, lilo = result
        assert lilo.count("ألعاب أول㎥ية") == 1 or lilo.count("ألعاب أولمبية") == 1


# ===== Tests for generate_category_text =====


class TestGenerateCategoryText:
    """Tests for generate_category_text function"""

    def test_generates_text_with_all_components(self, mocker):
        """Test that generate_category_text includes all components"""
        mocker.patch("src.mk_cats.categorytext.main_make_temp_no_title", return_value="")
        mocker.patch("src.mk_cats.categorytext.generate_portal_content", return_value="{{بوابة|علوم}}\n")
        mocker.patch("src.mk_cats.categorytext.fetch_commons_category", return_value="{{تصنيف كومنز|Science}}")

        result = generate_category_text("Category:Science", "تصنيف:علوم", "Q123")

        assert "{{بوابة|علوم}}" in result
        assert "{{نسخ:#لوموجود" in result
        assert "{{تصنيف كومنز|Science}}" in result

    def test_includes_template_when_present(self, mocker):
        """Test that template is included when main_make_temp_no_title returns content"""
        mocker.patch("src.mk_cats.categorytext.main_make_temp_no_title", return_value="{{قالب تصفح}}")
        mocker.patch("src.mk_cats.categorytext.generate_portal_content", return_value="")
        mocker.patch("src.mk_cats.categorytext.fetch_commons_category", return_value="")

        result = generate_category_text("Category:Science", "تصنيف:علوم", "Q123")

        assert "{{قالب تصفح}}" in result

    def test_no_template_when_absent(self, mocker):
        """Test that no template is added when main_make_temp_no_title returns empty"""
        mocker.patch("src.mk_cats.categorytext.main_make_temp_no_title", return_value="")
        mocker.patch("src.mk_cats.categorytext.generate_portal_content", return_value="")
        mocker.patch("src.mk_cats.categorytext.fetch_commons_category", return_value="")

        result = generate_category_text("Category:Science", "تصنيف:علوم", "Q123")

        assert "\nNone" not in result

    def test_no_template_when_none(self, mocker):
        """Test that no template is added when main_make_temp_no_title returns None"""
        mocker.patch("src.mk_cats.categorytext.main_make_temp_no_title", return_value=None)
        mocker.patch("src.mk_cats.categorytext.generate_portal_content", return_value="")
        mocker.patch("src.mk_cats.categorytext.fetch_commons_category", return_value="")

        result = generate_category_text("Category:Science", "تصنيف:علوم", "Q123")

        assert "\nNone" not in result

    def test_calls_main_make_temp_no_title_with_correct_args(self, mocker):
        """Test that main_make_temp_no_title is called with correct arguments"""
        mock_temp = mocker.patch("src.mk_cats.categorytext.main_make_temp_no_title", return_value="")
        mocker.patch("src.mk_cats.categorytext.generate_portal_content", return_value="")
        mocker.patch("src.mk_cats.categorytext.fetch_commons_category", return_value="")

        generate_category_text("Category:Science", "تصنيف:علوم", "Q123")

        mock_temp.assert_called_once_with("Category:Science", "تصنيف:علوم")

    def test_always_includes_lomawjod_template(self, mocker):
        """Test that the lomawjod template is always present"""
        mocker.patch("src.mk_cats.categorytext.main_make_temp_no_title", return_value="")
        mocker.patch("src.mk_cats.categorytext.generate_portal_content", return_value="")
        mocker.patch("src.mk_cats.categorytext.fetch_commons_category", return_value="")

        result = generate_category_text("Category:Test", "تصنيف:اختبار", "Q1")

        assert "{{نسخ:#لوموجود:{{نسخ:اسم_الصفحة}}|{{مقالة تصنيف}}|}}" in result


# ===== Original data integrity tests =====


class TestCategoryMapping:
    """Tests for category_mapping dictionary"""

    def test_is_dict(self):
        """Test that category_mapping is a dictionary"""
        assert isinstance(category_mapping, dict)

    def test_contains_known_mappings(self):
        """Test that category_mapping contains known mappings"""
        assert "الألعاب الأولمبية" in category_mapping
        assert category_mapping["الألعاب الأولمبية"] == "ألعاب أولمبية"

    def test_values_are_strings(self):
        """Test that all values are strings"""
        for key, value in category_mapping.items():
            assert isinstance(key, str)
            assert isinstance(value, str)


class TestLocalLanguageLinksSet:
    """Tests for LocalLanguageLinks set"""

    def test_is_set(self):
        """Test that LocalLanguageLinks is a set"""
        assert isinstance(LocalLanguageLinks, set)

    def test_contains_known_items(self):
        """Test that LocalLanguageLinks contains known items"""
        known_items = ["فلسطين", "المغرب", "اليمن", "سينما", "كرة القدم"]
        for item in known_items:
            assert item in LocalLanguageLinks

    def test_all_items_are_strings(self):
        """Test that all items are strings"""
        for item in LocalLanguageLinks:
            assert isinstance(item, str)

    def test_no_empty_strings(self):
        """Test that there are no empty strings"""
        for item in LocalLanguageLinks:
            assert item.strip() != ""


class PortalListIntegrityTests:
    """Tests for portal list integrity"""

    def test_find_list_values_relate_to_portals(self):
        """Test that category_mapping values are valid portal names"""
        for key, value in category_mapping.items():
            # Values should be non-empty strings
            assert value.strip() != ""
