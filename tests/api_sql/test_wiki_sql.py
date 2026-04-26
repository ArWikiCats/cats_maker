"""
Tests for src/core/api_sql/service.py

This module tests namespace handling and SQL query functions for MediaWiki.
"""

from src.core.api_sql.constants import NS_TEXT_AR, NS_TEXT_EN
from src.core.api_sql.service import (
    add_nstext_to_title,
    make_labsdb_dbs_p,
    sql_new,
    sql_new_title_ns,
)


class TestAddNsTextToTitle:
    """Tests for add_nstext_to_title function"""

    def test_with_namespace_0_returns_original_title(self):
        """Test that namespace 0 returns the original title unchanged"""
        result = add_nstext_to_title("محمد", "0", "ar")
        assert result == "محمد"

    def test_with_namespace_0_string(self):
        """Test namespace 0 as string"""
        result = add_nstext_to_title("Test Article", 0, "en")
        assert result == "Test Article"

    def test_with_category_namespace_ar(self):
        """Test adding category namespace prefix in Arabic"""
        result = add_nstext_to_title("علوم", "14", "ar")
        assert result == "تصنيف:علوم"

    def test_with_category_namespace_en(self):
        """Test adding category namespace prefix in English"""
        result = add_nstext_to_title("Science", "14", "en")
        assert result == "Category:Science"

    def test_with_template_namespace_ar(self):
        """Test adding template namespace prefix in Arabic"""
        result = add_nstext_to_title("صندوق", "10", "ar")
        assert result == "قالب:صندوق"

    def test_with_template_namespace_en(self):
        """Test adding template namespace prefix in English"""
        result = add_nstext_to_title("Infobox", "10", "en")
        assert result == "Template:Infobox"

    def test_with_user_namespace_ar(self):
        """Test adding user namespace prefix in Arabic"""
        result = add_nstext_to_title("أحمد", "2", "ar")
        assert result == "مستخدم:أحمد"

    def test_with_user_namespace_en(self):
        """Test adding user namespace prefix in English"""
        result = add_nstext_to_title("John", "2", "en")
        assert result == "User:John"

    def test_with_talk_namespace_ar(self):
        """Test adding talk namespace prefix in Arabic"""
        result = add_nstext_to_title("موضوع", "1", "ar")
        assert result == "نقاش:موضوع"

    def test_with_talk_namespace_en(self):
        """Test adding talk namespace prefix in English"""
        result = add_nstext_to_title("Topic", "1", "en")
        assert result == "Talk:Topic"

    def test_with_portal_namespace_ar(self):
        """Test adding portal namespace prefix in Arabic"""
        result = add_nstext_to_title("علوم", "100", "ar")
        assert result == "بوابة:علوم"

    def test_with_portal_namespace_en(self):
        """Test adding portal namespace prefix in English"""
        result = add_nstext_to_title("Science", "100", "en")
        assert result == "Portal:Science"

    def test_with_module_namespace_ar(self):
        """Test adding module namespace prefix in Arabic"""
        result = add_nstext_to_title("بيانات", "828", "ar")
        assert result == "وحدة:بيانات"

    def test_with_module_namespace_en(self):
        """Test adding module namespace prefix in English"""
        result = add_nstext_to_title("Data", "828", "en")
        assert result == "Module:Data"

    def test_with_invalid_namespace(self):
        """Test with an invalid namespace number"""
        result = add_nstext_to_title("Test", "999", "ar")
        # When namespace is not found, ns_text is None, so it returns "None:Test"
        assert result == "Test"

    def test_with_empty_title(self):
        """Test with empty title string"""
        result = add_nstext_to_title("", "14", "ar")
        assert result == ""

    def test_default_language_is_arabic(self):
        """Test that default language is Arabic"""
        result = add_nstext_to_title("علوم", "14")
        assert result == "تصنيف:علوم"


class TestNsTextTables:
    """Tests for namespace text tables"""

    def test_ar_namespace_table_has_category(self):
        """Test Arabic namespace table has category (14)"""
        assert "14" in NS_TEXT_AR
        assert NS_TEXT_AR["14"] == "تصنيف"

    def test_en_namespace_table_has_category(self):
        """Test English namespace table has category (14)"""
        assert "14" in NS_TEXT_EN
        assert NS_TEXT_EN["14"] == "Category"

    def test_ar_namespace_table_has_template(self):
        """Test Arabic namespace table has template (10)"""
        assert "10" in NS_TEXT_AR
        assert NS_TEXT_AR["10"] == "قالب"

    def test_en_namespace_table_has_template(self):
        """Test English namespace table has template (10)"""
        assert "10" in NS_TEXT_EN
        assert NS_TEXT_EN["10"] == "Template"

    def test_namespace_0_is_empty_string(self):
        """Test that namespace 0 maps to empty string"""
        assert NS_TEXT_AR["0"] == ""
        assert NS_TEXT_EN["0"] == ""


class TestMakeLabsdbDbsP:
    """Tests for make_labsdb_dbs_p function"""

    def test_with_ar_wiki(self):
        """Test generating host and db for Arabic Wikipedia"""
        host, db_p = make_labsdb_dbs_p("ar")
        assert host == "arwiki.analytics.db.svc.wikimedia.cloud"
        assert db_p == "arwiki_p"

    def test_with_en_wiki(self):
        """Test generating host and db for English Wikipedia"""
        host, db_p = make_labsdb_dbs_p("en")
        assert host == "enwiki.analytics.db.svc.wikimedia.cloud"
        assert db_p == "enwiki_p"

    def test_with_wiki_suffix(self):
        """Test handling wiki suffix"""
        host, db_p = make_labsdb_dbs_p("arwiki")
        assert host == "arwiki.analytics.db.svc.wikimedia.cloud"
        assert db_p == "arwiki_p"

    def test_with_wikidata(self):
        """Test special handling for Wikidata"""
        host, db_p = make_labsdb_dbs_p("wikidata")
        assert host == "wikidatawiki.analytics.db.svc.wikimedia.cloud"
        assert db_p == "wikidatawiki_p"

    def test_with_be_tarask(self):
        """Test special handling for Belarusian (Taraškievica)"""
        host, db_p = make_labsdb_dbs_p("be-tarask")
        assert host == "be_x_oldwiki.analytics.db.svc.wikimedia.cloud"
        assert db_p == "be_x_oldwiki_p"

    def test_with_be_x_old(self):
        """Test special handling for be-x-old"""
        host, db_p = make_labsdb_dbs_p("be-x-old")
        assert host == "be_x_oldwiki.analytics.db.svc.wikimedia.cloud"
        assert db_p == "be_x_oldwiki_p"

    def test_with_hyphenated_wiki(self):
        """Test handling hyphenated wiki names"""
        host, db_p = make_labsdb_dbs_p("zh-yue")
        assert "_" in host  # hyphen should be converted to underscore
        assert "wiki" in db_p

    def test_with_wiktionary(self):
        """Test handling wiktionary"""
        host, db_p = make_labsdb_dbs_p("arwiktionary")
        assert host == "arwiktionary.analytics.db.svc.wikimedia.cloud"
        assert db_p == "arwiktionary_p"

    def test_with_commons(self):
        """Test handling commons wiki"""
        host, db_p = make_labsdb_dbs_p("commons")
        assert "commonswiki" in host
        assert "commonswiki_p" == db_p


class TestSqlNew:
    """Tests for sql_new function."""

    def test_returns_empty_list_when_sql_disabled(self, mocker):
        """Test that sql_new returns [] when GET_SQL is False."""
        mocker.patch("src.core.api_sql.service.GET_SQL", return_value=False)
        result = sql_new("SELECT 1", wiki="ar")
        assert result == []

    def test_routes_to_make_sql_connect_silent(self, mocker):
        """Test that sql_new routes through make_sql_connect_silent."""
        mocker.patch("src.core.api_sql.service.GET_SQL", return_value=True)
        mock_connect = mocker.patch(
            "src.core.api_sql.service.make_sql_connect_silent",
            return_value=[{"col": "val"}],
        )

        result = sql_new("SELECT * FROM page", wiki="en", values=("title",))

        assert result == [{"col": "val"}]
        mock_connect.assert_called_once_with(
            "SELECT * FROM page",
            host="enwiki.analytics.db.svc.wikimedia.cloud",
            db="enwiki_p",
            values=("title",),
        )


class TestSqlNewTitleNs:
    """Tests for sql_new_title_ns function."""

    def test_maps_rows_to_namespace_titles(self, mocker):
        """Test mapping rows to 'Namespace:Title' strings."""
        mocker.patch("src.core.api_sql.service.GET_SQL", return_value=True)
        mocker.patch(
            "src.core.api_sql.service.make_sql_connect_silent",
            return_value=[
                {"page_title": "Science", "page_namespace": 14},
                {"page_title": "Test", "page_namespace": 0},
            ],
        )

        result = sql_new_title_ns("SELECT 1", wiki="en")

        assert result == ["Category:Science", "Test"]

    def test_skips_incomplete_rows(self, mocker):
        """Test that rows missing title or namespace are skipped."""
        mocker.patch("src.core.api_sql.service.GET_SQL", return_value=True)
        mocker.patch(
            "src.core.api_sql.service.make_sql_connect_silent",
            return_value=[
                {"page_title": "Valid", "page_namespace": 0},
                {"page_title": "Missing NS"},
                {"page_namespace": 0},
            ],
        )

        result = sql_new_title_ns("SELECT 1", wiki="ar")

        assert result == ["Valid"]
