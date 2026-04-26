"""
Tests for src/api_sql/wiki_sql.py

This module tests namespace handling and SQL query functions for MediaWiki.
"""

import pytest

from src.core.api_sql.wiki_sql import (
    GET_SQL,
    add_nstext_to_title,
    make_labsdb_dbs_p,
    ns_text_tab_ar,
    ns_text_tab_en,
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
        assert result == "None:Test"

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
        assert "14" in ns_text_tab_ar
        assert ns_text_tab_ar["14"] == "تصنيف"

    def test_en_namespace_table_has_category(self):
        """Test English namespace table has category (14)"""
        assert "14" in ns_text_tab_en
        assert ns_text_tab_en["14"] == "Category"

    def test_ar_namespace_table_has_template(self):
        """Test Arabic namespace table has template (10)"""
        assert "10" in ns_text_tab_ar
        assert ns_text_tab_ar["10"] == "قالب"

    def test_en_namespace_table_has_template(self):
        """Test English namespace table has template (10)"""
        assert "10" in ns_text_tab_en
        assert ns_text_tab_en["10"] == "Template"

    def test_namespace_0_is_empty_string(self):
        """Test that namespace 0 maps to empty string"""
        assert ns_text_tab_ar["0"] == ""
        assert ns_text_tab_en["0"] == ""


class TestMakeLabsdbDbsP:
    """Tests for make_labsdb_dbs_p function"""

    def test_with_ar_wiki(self):
        """Test generating host and db for Arabic Wikipedia"""
        host, dbs_p = make_labsdb_dbs_p("ar")
        assert host == "arwiki.analytics.db.svc.wikimedia.cloud"
        assert dbs_p == "arwiki_p"

    def test_with_en_wiki(self):
        """Test generating host and db for English Wikipedia"""
        host, dbs_p = make_labsdb_dbs_p("en")
        assert host == "enwiki.analytics.db.svc.wikimedia.cloud"
        assert dbs_p == "enwiki_p"

    def test_with_wiki_suffix(self):
        """Test handling wiki suffix"""
        host, dbs_p = make_labsdb_dbs_p("arwiki")
        assert host == "arwiki.analytics.db.svc.wikimedia.cloud"
        assert dbs_p == "arwiki_p"

    def test_with_wikidata(self):
        """Test special handling for Wikidata"""
        host, dbs_p = make_labsdb_dbs_p("wikidata")
        assert host == "wikidatawiki.analytics.db.svc.wikimedia.cloud"
        assert dbs_p == "wikidatawiki_p"

    def test_with_be_tarask(self):
        """Test special handling for Belarusian (Taraškievica)"""
        host, dbs_p = make_labsdb_dbs_p("be-tarask")
        assert host == "be_x_oldwiki.analytics.db.svc.wikimedia.cloud"
        assert dbs_p == "be_x_oldwiki_p"

    def test_with_be_x_old(self):
        """Test special handling for be-x-old"""
        host, dbs_p = make_labsdb_dbs_p("be-x-old")
        assert host == "be_x_oldwiki.analytics.db.svc.wikimedia.cloud"
        assert dbs_p == "be_x_oldwiki_p"

    def test_with_hyphenated_wiki(self):
        """Test handling hyphenated wiki names"""
        host, dbs_p = make_labsdb_dbs_p("zh-yue")
        assert "_" in host  # hyphen should be converted to underscore
        assert "wiki" in dbs_p

    def test_with_wiktionary(self):
        """Test handling wiktionary"""
        host, dbs_p = make_labsdb_dbs_p("arwiktionary")
        assert host == "arwiktionary.analytics.db.svc.wikimedia.cloud"
        assert dbs_p == "arwiktionary_p"

    def test_with_commons(self):
        """Test handling commons wiki"""
        host, dbs_p = make_labsdb_dbs_p("commons")
        assert "commonswiki" in host
        assert "commonswiki_p" == dbs_p
