"""
Tests for src/helps/printe_helper.py

This module tests the color formatting functionality for console output.
"""

import pytest

from src.core.helps.printe_helper import get_color_table, make_str


class TestGetColorTable:
    """Tests for get_color_table function"""

    def test_returns_dict(self):
        """Test that get_color_table returns a dictionary"""
        result = get_color_table()
        assert isinstance(result, dict)

    def test_contains_basic_colors(self):
        """Test that color table contains basic colors"""
        table = get_color_table()
        basic_colors = ["red", "green", "yellow", "blue", "purple", "cyan", "white"]
        for color in basic_colors:
            assert color in table

    def test_contains_light_color_variants(self):
        """Test that color table contains light color variants"""
        table = get_color_table()
        light_colors = ["lightred", "lightgreen", "lightyellow", "lightblue", "lightpurple"]
        for color in light_colors:
            assert color in table

    def test_contains_formatting_options(self):
        """Test that color table contains formatting options"""
        table = get_color_table()
        formats = ["bold", "underline", "invert", "blink"]
        for fmt in formats:
            assert fmt in table

    def test_color_values_are_ansi_templates(self):
        """Test that color values are ANSI escape sequence templates"""
        table = get_color_table()
        # Check that red contains ANSI escape code format
        assert "\033[" in table.get("red", "")
        assert "%s" in table.get("red", "")  # Format placeholder

    def test_caching_returns_same_object(self):
        """Test that function is cached and returns same dict"""
        table1 = get_color_table()
        table2 = get_color_table()
        assert table1 is table2  # Same object due to lru_cache


class TestMakeStr:
    """Tests for make_str function"""

    def test_plain_text_unchanged(self):
        """Test that plain text without color tags is returned unchanged"""
        result = make_str("Hello World")
        assert result == "Hello World"

    def test_non_string_returned_as_is(self):
        """Test that non-string values are returned as-is"""
        result = make_str(12345)
        assert result == 12345

    def test_none_returned_as_is(self):
        """Test that None is returned as-is"""
        result = make_str(None)
        assert result is None

    def test_list_returned_as_is(self):
        """Test that lists are returned as-is"""
        test_list = [1, 2, 3]
        result = make_str(test_list)
        assert result == test_list

    def test_color_tag_removed_from_output(self):
        """Test that color tags are processed and removed"""
        result = make_str("<<red>>Hello<<default>>")
        # The color code should be applied but tag removed
        assert "<<red>>" not in result
        assert "<<default>>" not in result
        assert "Hello" in result

    def test_multiple_color_tags(self):
        """Test handling multiple color tags"""
        result = make_str("<<red>>Red<<default>> and <<blue>>Blue<<default>>")
        assert "<<red>>" not in result
        assert "<<blue>>" not in result
        assert "Red" in result
        assert "Blue" in result

    def test_nested_color_tags(self):
        """Test handling nested color tags with previous"""
        result = make_str("<<red>>Red <<green>>Green<<previous>> Back<<default>>")
        assert "<<red>>" not in result
        assert "<<green>>" not in result
        assert "<<previous>>" not in result

    def test_03_color_format(self):
        """Test that \03{color} format is also processed"""
        # This format is used by pywikibot
        result = make_str("\03{red}Hello\03{default}")
        assert "\03{red}" not in result
        assert "\03{default}" not in result
        assert "Hello" in result

    def test_empty_string(self):
        """Test empty string is returned unchanged"""
        result = make_str("")
        assert result == ""

    def test_string_without_color_markers_unchanged(self):
        """Test string without << or \\03 is returned as-is"""
        text = "Just a normal string with no color codes"
        result = make_str(text)
        assert result == text

    def test_lightred_color(self):
        """Test lightred color tag"""
        result = make_str("<<lightred>>Error<<default>>")
        assert "Error" in result
        assert "<<lightred>>" not in result

    def test_lightgreen_color(self):
        """Test lightgreen color tag"""
        result = make_str("<<lightgreen>>Success<<default>>")
        assert "Success" in result
        assert "<<lightgreen>>" not in result

    def test_lightblue_color(self):
        """Test lightblue color tag"""
        result = make_str("<<lightblue>>Info<<default>>")
        assert "Info" in result
        assert "<<lightblue>>" not in result

    def test_bold_formatting(self):
        """Test bold formatting tag"""
        result = make_str("<<bold>>Important<<default>>")
        assert "Important" in result
        assert "<<bold>>" not in result

    def test_underline_formatting(self):
        """Test underline formatting tag"""
        result = make_str("<<underline>>Underlined<<default>>")
        assert "Underlined" in result
        assert "<<underline>>" not in result

    def test_aqua_alias_for_cyan(self):
        """Test that aqua is an alias for cyan"""
        result = make_str("<<aqua>>Aqua text<<default>>")
        assert "Aqua text" in result
        assert "<<aqua>>" not in result

    def test_grey_alias_for_gray(self):
        """Test that grey is an alias for gray"""
        result = make_str("<<grey>>Grey text<<default>>")
        assert "Grey text" in result
        assert "<<grey>>" not in result
