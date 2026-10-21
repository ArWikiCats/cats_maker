"""Tests for CategoryWikidataService (mknew_wikidata.py)."""

from src.cats_maker.mk_cats.mknew.mknew_wikidata import CategoryWikidataService

MODULE = "src.cats_maker.mk_cats.mknew.mknew_wikidata"
SITE_AR = {"family": "wikipedia", "code": "ar"}
SITE_EN = {"family": "wikipedia", "code": "en"}


class TestCheckSitelink:
    """Tests for CategoryWikidataService.check_sitelink method."""

    def test_returns_true_when_arabic_sitelink_exists(self, mocker):
        """Test that an existing arwiki sitelink is reported with the item info."""
        info = {"q": "Q12345", "sitelinks": {"arwiki": "علوم"}}
        mocker.patch(f"{MODULE}.get_sitelinks_from_wikidata", return_value=info)

        found, result = CategoryWikidataService(SITE_AR, SITE_EN).check_sitelink("Category:Science")

        assert found is True
        assert result == info

    def test_returns_false_without_arabic_sitelink(self, mocker):
        """Test that other-language sitelinks do not count as an Arabic link."""
        info = {"q": "Q12345", "sitelinks": {"frwiki": "Sciences"}}
        mocker.patch(f"{MODULE}.get_sitelinks_from_wikidata", return_value=info)

        found, result = CategoryWikidataService(SITE_AR, SITE_EN).check_sitelink("Category:Science")

        assert found is False
        assert result == info

    def test_returns_empty_info_when_wikidata_returns_none(self, mocker):
        """Test that a None answer from Wikidata becomes an empty dict."""
        mocker.patch(f"{MODULE}.get_sitelinks_from_wikidata", return_value=None)

        found, result = CategoryWikidataService(SITE_AR, SITE_EN).check_sitelink("Category:Science")

        assert found is False
        assert result == {}

    def test_looks_up_english_site_code(self, mocker):
        """Test that the lookup uses the English site code and the page title."""
        mock_get = mocker.patch(f"{MODULE}.get_sitelinks_from_wikidata", return_value={})

        CategoryWikidataService(SITE_AR, SITE_EN).check_sitelink("Category:Science")

        mock_get.assert_called_once_with("en", "Category:Science")

    def test_uses_family_suffix_for_non_wikipedia_sites(self, mocker):
        """Test that non-wikipedia families use the site-id style (e.g. enwikisource)."""
        site_ar = {"family": "wikisource", "code": "ar"}
        site_en = {"family": "wikisource", "code": "en"}
        mock_get = mocker.patch(
            f"{MODULE}.get_sitelinks_from_wikidata", return_value={"sitelinks": {"arwikisource": "علوم"}}
        )

        found, _ = CategoryWikidataService(site_ar, site_en).check_sitelink("Category:Science")

        mock_get.assert_called_once_with("enwikisource", "Category:Science")
        assert found is True


class TestLogCreation:
    """Tests for CategoryWikidataService.log_creation method."""

    def test_logs_by_qid_when_known(self, mocker):
        """Test that a known QID is logged with log_to_wikidata_qid."""
        by_qid = mocker.patch(f"{MODULE}.log_to_wikidata_qid")
        by_title = mocker.patch(f"{MODULE}.log_to_wikidata")

        CategoryWikidataService(SITE_AR, SITE_EN).log_creation("تصنيف:علوم", "Category:Science", "Q12345")

        by_qid.assert_called_once_with("تصنيف:علوم", "Q12345")
        by_title.assert_not_called()

    def test_logs_by_titles_without_qid(self, mocker):
        """Test that a missing QID falls back to logging by titles."""
        by_qid = mocker.patch(f"{MODULE}.log_to_wikidata_qid")
        by_title = mocker.patch(f"{MODULE}.log_to_wikidata")

        CategoryWikidataService(SITE_AR, SITE_EN).log_creation("تصنيف:علوم", "Category:Science", "")

        by_title.assert_called_once_with("تصنيف:علوم", "Category:Science")
        by_qid.assert_not_called()


class TestAddArabicLabel:
    """Tests for CategoryWikidataService.add_arabic_label method."""

    def test_adds_arabic_label_to_item(self, mocker):
        """Test that add_labels is called with the Arabic language code."""
        mock_add = mocker.patch(f"{MODULE}.add_labels")

        CategoryWikidataService(SITE_AR, SITE_EN).add_arabic_label("Q12345", "تصنيف:علوم")

        mock_add.assert_called_once_with("Q12345", "تصنيف:علوم", "ar")
