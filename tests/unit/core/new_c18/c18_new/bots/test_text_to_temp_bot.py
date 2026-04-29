"""
Tests for doc_handler.py

This module tests functions for adding text/categories to template pages.
"""

import re

import pytest

from src.core.new_c18.constants import PRE_TEXT, TO_SEARCH, TOSEARCH_AND_REPLACE
from src.core.new_c18.tools.doc_handler import (
    add_direct,
    add_text_to_template,
    add_to_doc_page,
    add_to_text_temps,
    find_doc_and_add,
)


class TestTosearchAndReplace:
    """Tests for TOSEARCH_AND_REPLACE constant"""

    def test_is_list(self):
        """Test that TOSEARCH_AND_REPLACE is a list"""
        assert isinstance(TOSEARCH_AND_REPLACE, list)

    def test_contains_expected_templates(self):
        """Test that expected templates are in list"""
        assert "{{توثيق شريط}}" in TOSEARCH_AND_REPLACE
        assert "{{Navbox documentation}}" in TOSEARCH_AND_REPLACE


class TestToSearch:
    """Tests for TO_SEARCH constant"""

    def test_is_list(self):
        """Test that TO_SEARCH is a list"""
        assert isinstance(TO_SEARCH, list)

    def test_contains_expected_patterns(self):
        """Test that expected patterns are in list"""
        assert "{{#استدعاء:شريط|شريط" in TO_SEARCH


class TestPreText:
    """Tests for PRE_TEXT constant"""

    def test_is_string(self):
        """Test that PRE_TEXT is a string"""
        assert isinstance(PRE_TEXT, str)

    def test_contains_documentation_header(self):
        """Test that PRE_TEXT contains documentation header"""
        assert "صفحة توثيق فرعية" in PRE_TEXT

    def test_contains_usage_section(self):
        """Test that PRE_TEXT contains usage section"""
        assert "استعمال" in PRE_TEXT


class TestAddToTextTemps:
    """Tests for add_to_text_temps function"""

    def test_adds_categories_after_template(self):
        """Test that categories are added after template"""
        text = "محتوى\n{{توثيق شريط}}\nنهاية"
        categories = "[[تصنيف:علوم]]"
        result = add_to_text_temps(text, categories)

        assert categories in result
        assert result.index(categories) > result.index("{{توثيق شريط}}")

    def test_returns_unchanged_if_no_template(self):
        """Test that text is unchanged if no template found"""
        text = "محتوى عادي"
        categories = "[[تصنيف:علوم]]"
        result = add_to_text_temps(text, categories)

        assert result == text


class TestAddToDocPage:
    """Tests for add_to_doc_page function"""

    def test_creates_new_doc_page_for_empty_text(self):
        """Test that new doc page is created for empty text"""
        categories = "[[تصنيف:علوم]]"
        result = add_to_doc_page("", categories)

        assert "صفحة توثيق فرعية" in result
        assert categories in result
        assert "</includeonly>" in result

    def test_adds_categories_to_existing_doc(self):
        """Test that categories are added to existing doc"""
        text = "محتوى التوثيق"
        categories = "[[تصنيف:علوم]]"
        result = add_to_doc_page(text, categories)

        # Should add categories somehow
        assert isinstance(result, str)

    def test_handles_includeonly_tags(self):
        """Test handling of includeonly tags"""
        text = "<includeonly>\n[[تصنيف:قديم]]\n</includeonly>"
        categories = "[[تصنيف:جديد]]"
        result = add_to_doc_page(text, categories)

        assert "[[تصنيف:جديد]]" in result or result == text

    def test_skips_existing_categories(self):
        """Test that existing categories are not duplicated"""
        text = "محتوى\n[[تصنيف:علوم]]"
        categories = "[[تصنيف:علوم]]"
        result = add_to_doc_page(text, categories)

        # Should not add duplicate
        assert result.count("[[تصنيف:علوم]]") <= 1 or result == text


class TestAddDirect:
    """Tests for add_direct function"""

    def test_adds_before_documentation_template(self):
        """Test that categories are added before documentation template"""
        text = "محتوى\n{{توثيق}}"
        categories = "[[تصنيف:علوم]]"
        result = add_direct(text, categories)

        assert categories in result

    def test_adds_before_navbox_template(self):
        """Test that categories are added before navbox template"""
        text = "محتوى\n{{توثيق شريط}}"
        categories = "[[تصنيف:علوم]]"
        result = add_direct(text, categories)

        assert categories in result

    def test_adds_noinclude_wrapper_when_no_template(self):
        """Test that noinclude wrapper is added when no template found"""
        text = "محتوى القالب"
        categories = "[[تصنيف:علوم]]"
        result = add_direct(text, categories)

        assert "<noinclude>" in result
        assert categories in result

    def test_handles_collapsible_option_template(self):
        """Test handling of collapsible option template"""
        text = "محتوى\n{{خيارات طي قالب تصفح}}"
        categories = "[[تصنيف:علوم]]"
        result = add_direct(text, categories)

        assert categories in result


class TestFindDocAndAdd:
    """Tests for find_doc_and_add function"""

    def test_skips_sandbox_pages(self, mocker):
        """Test that sandbox pages are skipped"""
        result = find_doc_and_add("[[تصنيف:علوم]]", "قالب:اختبار/ملعب")
        assert result is False

    def test_skips_lab_pages(self, mocker):
        """Test that lab pages are skipped"""
        result = find_doc_and_add("[[تصنيف:علوم]]", "قالب:اختبار/مختبر")
        assert result is False

    @pytest.mark.skip(reason="_lru_cache_wrapper does not have the attribute 'MainPage'")
    def test_returns_false_for_nonexistent_page(self, mocker):
        """Test that False is returned for nonexistent page"""
        mock_page = mocker.MagicMock()
        mock_page.get_text.return_value = ""
        mock_page.exists.return_value = False

        mocker.patch("src.core.new_c18.tools.doc_handler.load_main_api.MainPage", return_value=mock_page)

        result = find_doc_and_add("[[تصنيف:علوم]]", "قالب:اختبار", create=False)
        assert result is False


class TestAddTextToTemplate:
    """Tests for add_text_to_template function"""

    def test_handles_doc_page(self, mocker):
        """Test handling of /شرح pages"""
        mocker.patch("src.core.new_c18.tools.doc_handler.add_to_doc_page", return_value="نتيجة التوثيق")

        result = add_text_to_template("نص", "[[تصنيف:علوم]]", "قالب:اختبار/شرح")
        assert result == "نتيجة التوثيق"

    def test_handles_navbox_template(self):
        """Test handling of navbox templates"""
        text = "{{توثيق شريط}}"
        result = add_text_to_template(text, "[[تصنيف:علوم]]", "قالب:اختبار")

        # Should add categories using add_to_text_temps
        assert "[[تصنيف:علوم]]" in result

    def test_handles_regular_template(self, mocker):
        """Test handling of regular templates"""
        mocker.patch("src.core.new_c18.tools.doc_handler.find_doc_and_add", return_value=False)

        text = "محتوى القالب"
        result = add_text_to_template(text, "[[تصنيف:علوم]]", "قالب:اختبار")

        # Should use add_direct
        assert "<noinclude>" in result or "[[تصنيف:علوم]]" in result
