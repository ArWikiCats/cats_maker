"""Tests for CategoryManagerStats (mknew_state.py)."""

from src.cats_maker.mk_cats.mknew.mknew_state import CategoryManagerStats


class TestScanArTitle:
    """Tests for CategoryManagerStats._scan_ar_title method."""

    def test_returns_false_for_already_created(self):
        """Test that _scan_ar_title returns False for already created titles."""
        stats = CategoryManagerStats()
        stats._already_created.append("تصنيف:علوم")

        result = stats._scan_ar_title("تصنيف:علوم")

        assert result is False

    def test_returns_true_for_new_title(self):
        """Test that _scan_ar_title returns True for new titles."""
        stats = CategoryManagerStats()

        result = stats._scan_ar_title("تصنيف:جديد")

        assert result is True

    def test_tracks_title_in_newcat_done(self):
        """Test that _scan_ar_title tracks title in _new_cat_done."""
        stats = CategoryManagerStats()

        stats._scan_ar_title("تصنيف:اختبار")

        assert "تصنيف:اختبار" in stats._new_cat_done

    def test_returns_false_on_second_scan(self):
        """Test that scanning the same title twice returns False the second time."""
        stats = CategoryManagerStats()
        stats._scan_ar_title("تصنيف:اختبار")

        result = stats._scan_ar_title("تصنيف:اختبار")

        assert result is False
        assert stats._new_cat_done["تصنيف:اختبار"] == 2
