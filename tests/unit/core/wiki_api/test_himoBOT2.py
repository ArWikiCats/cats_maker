"""
Tests for himoBOT2.py

This module tests Wikipedia API helper functions.
"""

import pytest

from src.core.wiki_api.himoBOT2 import (
    get_page_info_from_wikipedia,
)


class TestGetPageInfoFromWikipediaNew:
    """Tests for get_page_info_from_wikipedia function"""

    def test_returns_dict_for_valid_page(self, mocker):
        """Test that function returns dict for valid page"""
        mock_response = {
            "query": {
                "pages": {
                    "123": {
                        "pageid": 123,
                        "ns": 0,
                        "title": "Test Page",
                        "langlinks": [{"lang": "en", "*": "Test Page"}],
                    }
                }
            }
        }
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        result = get_page_info_from_wikipedia("ar", "Test Page")
        assert isinstance(result, dict)

    def test_returns_empty_dict_on_no_response(self, mocker):
        """Test that function returns empty dict when API fails"""
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=None)
        get_page_info_from_wikipedia.cache_clear()

        result = get_page_info_from_wikipedia("ar", "Nonexistent")
        assert result == {}

    def test_handles_missing_page(self, mocker):
        """Test that function handles missing pages correctly"""
        mock_response = {
            "query": {
                "pages": {
                    "-1": {
                        "ns": 0,
                        "title": "Missing Page",
                        "missing": "",
                    }
                }
            }
        }
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        result = get_page_info_from_wikipedia("ar", "Missing Page")
        assert isinstance(result, dict)
        if result:
            assert result.get("exists") is False

    def test_strips_wiki_suffix_from_sitecode(self, mocker):
        """Test that function strips 'wiki' suffix from sitecode"""
        mock_response = {"query": {"pages": {"123": {"pageid": 123, "ns": 0, "title": "Test"}}}}
        mock_submit = mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        get_page_info_from_wikipedia("arwiki", "Test")
        # The function should call submitAPI with 'ar' not 'arwiki'
        call_args = mock_submit.call_args
        assert call_args[0][1] == "ar"  # sitecode should be 'ar'

    def test_findtemp_adds_tltemplates(self, mocker):
        """Test that findtemp parameter adds tltemplates to params."""
        mock_response = {"query": {"pages": {"123": {"pageid": 123, "ns": 0, "title": "Test"}}}}
        mock_submit = mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        get_page_info_from_wikipedia("ar", "Test", findtemp="Template:Stub")
        call_args = mock_submit.call_args
        params = call_args[0][0]
        assert params["tltemplates"] == "Template:Stub"

    def test_empty_query_returns_empty(self, mocker):
        """Test that empty query returns empty dict."""
        mock_response = {"query": {}}
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        result = get_page_info_from_wikipedia("ar", "Test")
        assert result == {}

    def test_normalized_titles(self, mocker):
        """Test handling of normalized titles."""
        mock_response = {
            "query": {
                "normalized": [{"from": "test page", "to": "Test Page"}],
                "pages": {
                    "123": {
                        "pageid": 123,
                        "ns": 0,
                        "title": "Test Page",
                        "langlinks": [],
                    }
                },
            }
        }
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        result = get_page_info_from_wikipedia("ar", "test page")
        assert result["title"] == "Test Page"

    def test_redirect_handling(self, mocker):
        """Test redirect handling builds redirect table entries."""
        mock_response = {
            "query": {
                "redirects": [{"from": "Old Title", "to": "New Title"}],
                "pages": {
                    "123": {
                        "pageid": 123,
                        "ns": 0,
                        "title": "New Title",
                        "langlinks": [],
                    }
                },
            }
        }
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        result = get_page_info_from_wikipedia("ar", "Old Title")
        # The redirect entry for "Old Title" is found first via title lookup
        assert result["isRedirectPage"] is True
        assert result["from"] == "Old Title"
        assert result["to"] == "New Title"

    def test_missing_key_sets_exists_false(self, mocker):
        """Test that 'missing' key in page data sets exists=False."""
        mock_response = {
            "query": {
                "pages": {
                    "456": {
                        "pageid": 456,
                        "ns": 0,
                        "title": "Gone Page",
                        "missing": "",
                        "langlinks": [],
                    }
                }
            }
        }
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        result = get_page_info_from_wikipedia("ar", "Gone Page")
        assert result["exists"] is False

    def test_title2_fallback_lookup(self, mocker):
        """Test result lookup using title2 when title not in table."""
        mock_response = {
            "query": {
                "normalized": [{"from": "input", "to": "Normalized"}],
                "pages": {
                    "123": {
                        "pageid": 123,
                        "ns": 0,
                        "title": "Normalized",
                        "langlinks": [],
                    }
                },
            }
        }
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        # "input" won't be in the table (pages use "Normalized"), so title2 fallback
        result = get_page_info_from_wikipedia("ar", "input")
        assert result["title"] == "Normalized"

    def test_langlinks_extraction(self, mocker):
        """Test langlinks extraction from page data."""
        mock_response = {
            "query": {
                "pages": {
                    "123": {
                        "pageid": 123,
                        "ns": 0,
                        "title": "Test",
                        "langlinks": [{"lang": "en", "*": "Test"}, {"lang": "fr", "*": "Test"}],
                    }
                }
            }
        }
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        result = get_page_info_from_wikipedia("ar", "Test")
        assert result["langlinks"] == {"en": "Test", "fr": "Test"}

    def test_pageprops_wikibase_item(self, mocker):
        """Test wikibase_item extraction from pageprops."""
        mock_response = {
            "query": {
                "pages": {
                    "123": {
                        "pageid": 123,
                        "ns": 0,
                        "title": "Test",
                        "langlinks": [],
                        "pageprops": {"wikibase_item": "Q12345"},
                    }
                }
            }
        }
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        result = get_page_info_from_wikipedia("ar", "Test")
        assert result["wikibase_item"] == "Q12345"
        assert result["q"] == "Q12345"

    def test_templates_extraction(self, mocker):
        """Test templates extraction from page data."""
        mock_response = {
            "query": {
                "pages": {
                    "123": {
                        "pageid": 123,
                        "ns": 0,
                        "title": "Test",
                        "langlinks": [],
                        "templates": [{"title": "قالب:A"}, {"title": "قالب:B"}],
                    }
                }
            }
        }
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        result = get_page_info_from_wikipedia("ar", "Test")
        assert result["templates"] == ["قالب:A", "قالب:B"]

    def test_linkshere_extraction(self, mocker):
        """Test linkshere extraction from page data."""
        mock_response = {
            "query": {
                "pages": {
                    "123": {
                        "pageid": 123,
                        "ns": 0,
                        "title": "Test",
                        "langlinks": [],
                        "linkshere": [
                            {"title": "Page1", "ns": 0},
                            {"title": "Page2", "ns": 10},
                            {"title": "Page3", "ns": 14},
                        ],
                    }
                }
            }
        }
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        result = get_page_info_from_wikipedia("ar", "Test")
        # Only ns 0 and 10 should be included
        assert len(result["linkshere"]) == 2
        assert result["countlinkshere"] == 2

    def test_categories_extraction(self, mocker):
        """Test categories extraction from page data."""
        mock_response = {
            "query": {
                "pages": {
                    "123": {
                        "pageid": 123,
                        "ns": 0,
                        "title": "Test",
                        "langlinks": [],
                        "categories": [{"title": "تصنيف:A"}, {"title": "تصنيف:B"}],
                    }
                }
            }
        }
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        result = get_page_info_from_wikipedia("ar", "Test")
        assert result["categories"] == ["تصنيف:A", "تصنيف:B"]

    def test_flagged_property(self, mocker):
        """Test flagged property extraction."""
        mock_response = {
            "query": {
                "pages": {
                    "123": {
                        "pageid": 123,
                        "ns": 0,
                        "title": "Test",
                        "langlinks": [],
                        "flagged": True,
                    }
                }
            }
        }
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        result = get_page_info_from_wikipedia("ar", "Test")
        assert result["flagged"] is True

    def test_iwlinks_extraction(self, mocker):
        """Test iwlinks extraction from page data."""
        mock_response = {
            "query": {
                "pages": {
                    "123": {
                        "pageid": 123,
                        "ns": 0,
                        "title": "Test",
                        "langlinks": [],
                        "iwlinks": [{"prefix": "w", "*": "Article"}, {"prefix": "s", "*": "Source"}],
                    }
                }
            }
        }
        mocker.patch("src.core.wiki_api.himoBOT2.submitAPI", return_value=mock_response)
        get_page_info_from_wikipedia.cache_clear()

        result = get_page_info_from_wikipedia("ar", "Test")
        assert result["iwlinks"] == {"w": "Article", "s": "Source"}
