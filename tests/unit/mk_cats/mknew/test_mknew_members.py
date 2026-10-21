"""Tests for CategoryMembersAdder (mknew_members.py)."""

from unittest.mock import MagicMock

from src.cats_maker.mk_cats.mknew.mknew_members import CategoryMembersAdder


def make_adder(save_result=True):
    """Build an adder whose add_to_page function is a mock returning `save_result`."""
    add_to_page = MagicMock(return_value=save_result)
    return CategoryMembersAdder(add_to_page_func=add_to_page), add_to_page


class TestAdd:
    """Tests for CategoryMembersAdder.add method."""

    def test_handles_empty_list(self):
        """Test that empty list is handled gracefully."""
        adder, add_to_page = make_adder()

        adder.add([], "تصنيف:علوم")

        add_to_page.assert_not_called()

    def test_handles_none_list(self):
        """Test that None list is handled gracefully."""
        adder, add_to_page = make_adder()

        adder.add(None, "تصنيف:علوم")

        add_to_page.assert_not_called()

    def test_adds_tasneef_prefix_if_missing(self):
        """Test that تصنيف: prefix is added if missing."""
        adder, add_to_page = make_adder()

        adder.add(["صفحة1"], "علوم")

        add_to_page.assert_called_once_with("صفحة1", "تصنيف:علوم")

    def test_replaces_underscores_in_title(self):
        """Test that underscores are replaced with spaces in title."""
        adder, add_to_page = make_adder()

        adder.add(["صفحة1"], "تصنيف:علوم_الحاسوب")

        add_to_page.assert_called_once_with("صفحة1", "تصنيف:علوم الحاسوب")

    def test_calls_add_to_page_for_each_item(self):
        """Test that add_to_page is called for each item in list."""
        adder, add_to_page = make_adder()

        adder.add(["صفحة1", "صفحة2", "صفحة3"], "تصنيف:علوم")

        assert add_to_page.call_count == 3

    def test_calls_callback_on_success(self):
        """Test that callback is called on successful save."""
        adder, _ = make_adder(save_result=True)
        mock_callback = MagicMock()

        adder.add(["صفحة1"], "تصنيف:علوم", callback=mock_callback)

        mock_callback.assert_called_once_with("تصنيف:علوم")

    def test_skips_callback_when_save_fails(self):
        """Test that callback is not called when the page was not saved."""
        adder, _ = make_adder(save_result=False)
        mock_callback = MagicMock()

        adder.add(["صفحة1"], "تصنيف:علوم", callback=mock_callback)

        mock_callback.assert_not_called()

    def test_handles_callback_exception(self):
        """Test that callback exceptions are handled without propagating."""
        adder, _ = make_adder(save_result=True)
        mock_callback = MagicMock(side_effect=Exception("Test error"))

        adder.add(["صفحة1"], "تصنيف:علوم", callback=mock_callback)

        mock_callback.assert_called_once()
