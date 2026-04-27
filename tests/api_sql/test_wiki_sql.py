"""
Tests for src/core/api_sql/service.py

This module tests namespace handling and SQL query functions for MediaWiki.
"""

import pytest

from src.core.api_sql.config import ConfigLoader
from src.core.api_sql.constants import NS_TEXT_AR, NS_TEXT_EN
from src.core.api_sql.db_pool import db_manager
from src.core.api_sql.exceptions import DatabaseConnectionError
from src.core.api_sql.utils import add_namespace_prefix


class TestAddNamespacePrefix:
    """Tests for add_namespace_prefix function"""

    def test_with_namespace_0_returns_original_title(self):
        """Test that namespace 0 returns the original title unchanged"""
        result = add_namespace_prefix("محمد", "0", "ar")
        assert result == "محمد"

    def test_with_namespace_0_string(self):
        """Test namespace 0 as string"""
        result = add_namespace_prefix("Test Article", 0, "en")
        assert result == "Test Article"

    def test_with_category_namespace_ar(self):
        """Test adding category namespace prefix in Arabic"""
        result = add_namespace_prefix("علوم", "14", "ar")
        assert result == "تصنيف:علوم"

    def test_with_category_namespace_en(self):
        """Test adding category namespace prefix in English"""
        result = add_namespace_prefix("Science", "14", "en")
        assert result == "Category:Science"

    def test_with_template_namespace_ar(self):
        """Test adding template namespace prefix in Arabic"""
        result = add_namespace_prefix("صندوق", "10", "ar")
        assert result == "قالب:صندوق"

    def test_with_template_namespace_en(self):
        """Test adding template namespace prefix in English"""
        result = add_namespace_prefix("Infobox", "10", "en")
        assert result == "Template:Infobox"

    def test_with_user_namespace_ar(self):
        """Test adding user namespace prefix in Arabic"""
        result = add_namespace_prefix("أحمد", "2", "ar")
        assert result == "مستخدم:أحمد"

    def test_with_user_namespace_en(self):
        """Test adding user namespace prefix in English"""
        result = add_namespace_prefix("John", "2", "en")
        assert result == "User:John"

    def test_with_talk_namespace_ar(self):
        """Test adding talk namespace prefix in Arabic"""
        result = add_namespace_prefix("موضوع", "1", "ar")
        assert result == "نقاش:موضوع"

    def test_with_talk_namespace_en(self):
        """Test adding talk namespace prefix in English"""
        result = add_namespace_prefix("Topic", "1", "en")
        assert result == "Talk:Topic"

    def test_with_portal_namespace_ar(self):
        """Test adding portal namespace prefix in Arabic"""
        result = add_namespace_prefix("علوم", "100", "ar")
        assert result == "بوابة:علوم"

    def test_with_portal_namespace_en(self):
        """Test adding portal namespace prefix in English"""
        result = add_namespace_prefix("Science", "100", "en")
        assert result == "Portal:Science"

    def test_with_module_namespace_ar(self):
        """Test adding module namespace prefix in Arabic"""
        result = add_namespace_prefix("بيانات", "828", "ar")
        assert result == "وحدة:بيانات"

    def test_with_module_namespace_en(self):
        """Test adding module namespace prefix in English"""
        result = add_namespace_prefix("Data", "828", "en")
        assert result == "Module:Data"

    def test_with_invalid_namespace(self):
        """Test with an invalid namespace number"""
        result = add_namespace_prefix("Test", "999", "ar")
        # When namespace is not found, it returns title
        assert result == "Test"

    def test_with_empty_title(self):
        """Test with empty title string"""
        result = add_namespace_prefix("", "14", "ar")
        assert result == ""

    def test_default_language_is_arabic(self):
        """Test that default language is Arabic"""
        result = add_namespace_prefix("علوم", "14")
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


class TestConfigLoader:
    """Tests for ConfigLoader class"""

    def test_get_db_config_ar(self, mocker):
        """Test resolving DB config for Arabic Wikipedia"""
        mocker.patch("pathlib.Path.exists", return_value=True)
        config = ConfigLoader.get_db_config("ar")
        assert config.host == "arwiki.analytics.db.svc.wikimedia.cloud"
        assert config.database == "arwiki_p"

    def test_get_db_config_enwiki(self, mocker):
        """Test resolving DB config for English Wikipedia"""
        mocker.patch("pathlib.Path.exists", return_value=True)
        config = ConfigLoader.get_db_config("enwiki")
        assert config.host == "enwiki.analytics.db.svc.wikimedia.cloud"
        assert config.database == "enwiki_p"

    def test_get_db_config_wikidata(self, mocker):
        """Test resolving DB config for Wikidata"""
        mocker.patch("pathlib.Path.exists", return_value=True)
        config = ConfigLoader.get_db_config("wikidata")
        assert config.host == "wikidatawiki.analytics.db.svc.wikimedia.cloud"
        assert config.database == "wikidatawiki_p"


class TestDatabaseManager:
    """Tests for DatabaseManager class."""

    def test_execute_query_raises_when_not_prod(self, mocker):
        """Test that DatabaseManager raises DatabaseConnectionError when not in production."""
        mocker.patch("src.core.api_sql.config.ConfigLoader.is_production", return_value=False)

        with pytest.raises(DatabaseConnectionError):
            db_manager.execute_query(wiki="ar", query="SELECT 1")

    def test_execute_query_rejects_non_select(self):
        """Test that only SELECT queries are allowed."""

        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            db_manager.execute_query(wiki="ar", query="DELETE FROM page")
