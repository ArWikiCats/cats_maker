"""Test configuration for the test-suite."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add the ArWikiCats directory to the python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ===== Shared Test Data Fixtures =====


@pytest.fixture
def sample_category_data():
    """Sample category data for testing"""
    return {
        "en_title": "Science",
        "ar_title": "علوم",
        "namespace": "14",
        "members": ["Physics", "Chemistry", "Biology"],
    }


@pytest.fixture
def sample_page_info():
    """Sample page info from Wikipedia API"""
    return {
        "title": "Test Page",
        "pageid": 12345,
        "ns": 0,
        "exists": True,
    }


# ===== Mock Fixtures for External Services =====


@pytest.fixture
def mock_wikidata_api(mocker):
    """Mock Wikidata API calls"""
    return mocker.patch("src.core.wd_bots.wd_api_bot.Get_infos_wikidata")


@pytest.fixture
def mock_database(mocker):
    """Mock database connections"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mocker.patch("src.core.api_sql_new.db_pool.db_manager.execute_query", return_value=[])
    return mock_cursor


@pytest.fixture
def mock_logger(mocker):
    """Mock the project logger to suppress output during testing"""
    return mocker.patch("src.core.helps.log.logger")


# ===== API Response Fixtures =====


@pytest.fixture
def mock_api_response_with_langlinks():
    """Mock Wikipedia API response with langlinks"""
    return {
        "query": {
            "pages": {
                "123": {
                    "title": "Science",
                    "pageid": 123,
                    "ns": 14,
                    "langlinks": [{"lang": "ar", "*": "علوم"}, {"lang": "fr", "*": "Science"}],
                }
            }
        }
    }


@pytest.fixture
def mock_api_response_no_langlinks():
    """Mock Wikipedia API response without langlinks"""
    return {
        "query": {
            "pages": {
                "456": {
                    "title": "Test Category",
                    "pageid": 456,
                    "ns": 14,
                }
            }
        }
    }


@pytest.fixture
def mock_api_response_not_found():
    """Mock Wikipedia API response for non-existing page"""
    return {
        "query": {
            "pages": {
                "-1": {
                    "title": "Non-Existing Page",
                    "ns": 0,
                    "missing": "",
                }
            }
        }
    }


@pytest.fixture
def mock_wikidata_response():
    """Mock Wikidata API response"""
    return {
        "q": "Q12345",
        "sitelinks": {
            "arwiki": "علوم",
            "enwiki": "Science",
        },
        "labels": {
            "ar": "علوم",
            "en": "Science",
        },
    }


# ===== Database Mock Fixtures =====


@pytest.fixture
def mock_sql_result():
    """Mock SQL query result"""
    return [
        {"page_title": "Test_Article_1", "page_namespace": 0},
        {"page_title": "Test_Article_2", "page_namespace": 0},
        {"page_title": "Science", "page_namespace": 14},
    ]


# ===== File System Fixtures =====


@pytest.fixture
def temp_jsonl_file(tmp_path):
    """Create a temporary JSONL file for testing"""
    file_path = tmp_path / "test_data.jsonl"
    return file_path


# ===== Test Utility Functions =====


@pytest.fixture
def disable_network(mocker):
    """Disable all network requests during testing"""
    mocker.patch("requests.get", side_effect=Exception("Network disabled in tests"))
    mocker.patch("requests.post", side_effect=Exception("Network disabled in tests"))
    mocker.patch("urllib.request.urlopen", side_effect=Exception("Network disabled in tests"))
