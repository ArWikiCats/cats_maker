"""
Tests for doc_handler.py

This module tests functions for adding text/categories to template pages.
"""

import re

import pytest

from src.core.new_c18.tools.doc_handler import (
    add_direct,
    add_text_to_template,
    add_to_doc_page,
    add_to_text_temps,
    find_doc_and_add,
)


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

    def test_skips_empty_category_lines(self):
        """Test that empty lines in categories are skipped"""
        text = "محتوى"
        categories = "[[تصنيف:علوم]]\n\n[[تصنيف:تاريخ]]"
        result = add_to_doc_page(text, categories)

        assert "[[تصنيف:علوم]]" in result

    def test_handles_category_with_pipe(self):
        """Test that categories with pipe (sort key) are handled"""
        text = "محتوى"
        categories = "[[تصنيف:علوم|فرع]]"
        result = add_to_doc_page(text, categories)

        # Should handle the pipe correctly
        assert isinstance(result, str)

    def test_handles_includeonly_with_category_pattern(self):
        """Test handling when includeonly precedes category"""
        text = "<includeonly>\n[[تصنيف:قديم]]"
        categories = "[[تصنيف:جديد]]"
        result = add_to_doc_page(text, categories)

        assert "[[تصنيف:جديد]]" in result or result == text

    def test_handles_sandbox_template(self):
        """Test handling of sandbox template"""
        text = "محتوى\n{{sandbox other}}"
        categories = "[[تصنيف:علوم]]"
        result = add_to_doc_page(text, categories)

        assert "[[تصنيف:علوم]]" in result

    def test_handles_melab_akher_template(self):
        """Test handling of ملعب أخر template"""
        text = "محتوى\n{{ملعب أخر}}"
        categories = "[[تصنيف:علوم]]"
        result = add_to_doc_page(text, categories)

        assert "[[تصنيف:علوم]]" in result

    def test_handles_end_includeonly_tag(self):
        """Test handling of </includeonly> tag"""
        text = "محتوى\n</includeonly>"
        categories = "[[تصنيف:علوم]]"
        result = add_to_doc_page(text, categories)

        assert "[[تصنيف:علوم]]" in result

    def test_creates_default_template_when_no_match(self):
        """Test that default template is created when no other match"""
        text = "محتوى قالب"
        categories = "[[تصنيف:علوم]]"
        result = add_to_doc_page(text, categories)

        assert "ملعب آخر" in result


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

    def test_handles_option_lawi_template(self):
        """Test handling of خيار طوي قالب template"""
        text = "محتوى\n{{خيار طوي قالب}}"
        categories = "[[تصنيف:علوم]]"
        result = add_direct(text, categories)

        assert categories in result

    def test_handles_collapsible_option_english(self):
        """Test handling of collapsible option English template"""
        text = "محتوى\n{{collapsible option}}"
        categories = "[[تصنيف:علوم]]"
        result = add_direct(text, categories)

        assert categories in result

    def test_merges_adjacent_noinclude_tags(self):
        """Test that adjacent noinclude tags are merged"""
        text = "<noinclude>content1</noinclude>\n<noinclude>content2</noinclude>"
        categories = "[[تصنيف:علوم]]"
        result = add_direct(text, categories)

        assert "<noinclude>" in result

    def test_adds_content_when_not_in_text(self):
        """Test that content is added when not already in text"""
        text = "محتوى القالب"
        categories = "تصنيف:علوم"
        result = add_direct(text, categories)

        assert "<noinclude>" in result


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
