"""Tests for ar_make_lab (labels_creator.py)."""

from unittest.mock import MagicMock

from src.cats_maker.mk_cats.mknew import ar_make_lab


class TestArMakeLab:
    """Tests for ar_make_lab function."""

    def test_returns_empty_when_filter_fails(self, mocker):
        """Test that ar_make_lab returns empty string when filter_category fails."""
        mocker.patch("src.cats_maker.mk_cats.mknew.labels_creator.filter_category", return_value=False)

        result = ar_make_lab("Category:Test")

        assert result == ""

    def test_returns_empty_when_no_resolver(self, mocker):
        """Test that ar_make_lab returns empty string when resolve_arabic_category_label is None."""
        mocker.patch("src.cats_maker.mk_cats.mknew.labels_creator.filter_category", return_value=True)
        mocker.patch("src.cats_maker.mk_cats.mknew.labels_creator.resolve_arabic_category_label", None)

        result = ar_make_lab("Category:Science")

        assert result == ""

    def test_returns_label_when_resolver_exists(self, mocker):
        """Test that ar_make_lab returns label when resolver exists."""
        mocker.patch("src.cats_maker.mk_cats.mknew.labels_creator.filter_category", return_value=True)
        mock_resolver = MagicMock(return_value="علوم")
        mocker.patch("src.cats_maker.mk_cats.mknew.labels_creator.resolve_arabic_category_label", mock_resolver)

        result = ar_make_lab("Category:Science")

        assert result == "علوم"
