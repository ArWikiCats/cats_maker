#!/usr/bin/python3
"""
Refactored module for handling MediaWiki API calls for categories, langlinks, etc.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from . import submitAPI

logger = logging.getLogger(__name__)

page_is_redirect = {}  # self.page_is_redirect


class WikiApiCache:
    def __init__(self, max_size=1000, ttl_seconds=3600):
        self.cache: Dict[Tuple, Any] = {}


class WikiApiHandler:
    """
    A class to handle MediaWiki API interactions, encapsulating state like cache,
    API call counts, and page data.
    """

    def __init__(self, default_en_site_code: str = "en", family: str = "wikipedia"):
        # Configuration
        self.family = family
        self.en_site_config = {"code": default_en_site_code, "family": family}
        # ---
        # State variables (previously global)
        # ---
        self.cache: Dict[Tuple, Any] = {}
        # ---
        self.arpage_inside_en_cat: Dict[str, List[str]] = {}
        self.page_is_redirect: Dict[str, List[str]] = {}
        self.deleted: List[str] = []
        self.api_call_count: int = 0

    def get_arpage_inside_encat_all(self):
        return self.arpage_inside_en_cat

    def get_deleting_page(self):
        return self.deleted

    def _increment_api_call(self):
        """Increments the API call counter."""
        self.api_call_count += 1
        return self.api_call_count

    # --- Public methods mimicking the old functions ---

    def get_arpage_inside_encat(self, key: str) -> Optional[List[str]]:
        """Gets the list of arabic pages inside an english category."""
        return self.arpage_inside_en_cat.get(key)

    def find_page_data(
        self, page_title: str, prop: str = "", lllang: str = "", site_code: str = "en"
    ) -> Optional[Dict]:
        """
        Retrieves data (langlinks, categories, etc.) for a given page.
        This is the refactored version of find_LCN.
        """
        logger.debug("-----------")
        props = prop or "langlinks"

        cache_key = (page_title, site_code, props)
        if cache_key in self.cache:
            logger.debug(f"Returning cached data for {cache_key}")
            return self.cache[cache_key]

        if not page_title or "#" in page_title:
            self.cache[cache_key] = False
            return False

        params = {
            "action": "query",
            "format": "json",
            # "prop": "categories|langlinks|templates",
            "prop": props,
            "titles": page_title,
            "redirects": 1,
            "utf8": 1,
            # "clprop": "hidden",
            # "cllimit": 500,
            # 'tllimit': 50,
            # "lllang": lllang_target
        }

        if lllang:
            params["lllang"] = lllang

        if "langlinks" in props:
            params["lllimit"] = "max"

        if "categories" in props:
            params["clprop"] = "hidden"
            params["cllimit"] = "max"

        if "templates" in props:
            params["tlnamespace"] = "10"
            params["tllimit"] = "max"

        count = self._increment_api_call()

        logger.info(f"<<lightblue>> API CALL {count}: for ({self.family}:{page_title}), prop: {props}")

        logger.debug(f" for page {site_code}:{page_title}")

        api_response = submitAPI(params, site_code, self.family, printurl=False)

        if not (api_response and "query" in api_response and "pages" in api_response["query"]):
            logger.debug("<<lightblue>> API call failed or returned no query/pages.")
            logger.debug(api_response)
            self.cache[cache_key] = False
            return False

        query = api_response["query"]

        if "-1" in query["pages"]:
            logger.info(f'Page not found (id: -1) for "{site_code}:{page_title}"')
            self.deleted.append(page_title)
            self.cache[cache_key] = False
            return False

        page_results = self._parse_api_response(query, site_code, props)

        # Cache the final processed result for the original title
        self.cache[cache_key] = page_results
        return page_results

    def _parse_api_response(self, query: Dict, site_code: str, props: str = "") -> Dict:
        """Helper to parse the 'pages' and 'redirects' part of an API response."""
        results = {}
        redirect_map = {r["from"]: r["to"] for r in query.get("redirects", [])}

        for _page_id, page_data in query["pages"].items():
            title = page_data["title"]
            logger.debug(f"<<lightblue>>--------------\n self_cache add {title} :")

            # Handle redirects
            if title in redirect_map.values():
                original_title = next((k for k, v in redirect_map.items() if v == title), None)
                if original_title:
                    results[original_title] = {"redirect": title}

            data = results.setdefault(title, {"langlinks": {}})

            if "langlinks" in page_data:
                langlinks = {ll["lang"]: ll["*"] for ll in page_data["langlinks"]}

                data["langlinks"] = langlinks

                self.cache[(title, site_code, "langlinks")] = langlinks
                # Cache reverse lookup
                for lang, link in langlinks.items():
                    self.cache[(link, lang, "en_links")] = title  # Assuming site_code is 'en'

            if "categories" in page_data:
                all_cats = [c["title"] for c in page_data["categories"]]
                non_hidden_cats = [c["title"] for c in page_data["categories"] if "hidden" not in c]

                data["categories"] = all_cats
                data["cat_with_out_hidden"] = non_hidden_cats

                self.cache[(title, site_code, "categories")] = all_cats
                self.cache[(title, site_code, "cat_with_out_hidden")] = non_hidden_cats

                logger.debug(f"<<lightblue>> categories: {all_cats}")
                logger.debug(f"<<lightblue>> cat_with_out_hidden: {non_hidden_cats}")

            ns = page_data.get("ns")
            if ns:
                data["ns"] = ns
                self.cache[(title, site_code, "ns")] = ns
                logger.debug(f"<<lightblue>> ns: {ns}")

            if "templates" in page_data:
                templates = [t["title"] for t in page_data["templates"]]
                data["templates"] = templates
                self.cache[(title, site_code, "templates")] = templates
                logger.debug(f"<<lightblue>> templates: {templates}")

        self.cache[(title, site_code, props)] = {title: data}
        logger.debug("<<lightred>>--------------")

        return results

    def find_non_hidden_categories(self, page_title: str, prop: str = "", site_code: str = "ar") -> Optional[Dict]:
        """
        Retrieves non-hidden categories for a given page.
        Refactored version of find_Page_Cat_without_hidden.
        """
        if not page_title or "#" in page_title:
            logger.info(f"(page_title == '{page_title}') or (page_title.find('#') != -1)")
            return False

        cache_key = (page_title, site_code, "Cat_without_hidden", prop)

        logger.debug(f"<<lightgreen>>-----------\n find Page_Cat_without_hidden for {site_code}:{page_title} ")
        if cache_key in self.cache:
            logger.info("get_cache_L_C_N(cache_key)")
            return self.cache[cache_key]

        # If the page's redirect list doesn't exist, initialize it
        self.page_is_redirect.setdefault(site_code, [])

        # Define target language for langlinks
        lllang_target = "ar" if site_code != "ar" else self.en_site_config["code"]

        params = {
            "action": "query",
            "format": "json",
            "prop": prop or "langlinks",
            "titles": page_title,
            "generator": "categories",
            "gclshow": "!hidden",
            "gcllimit": "max",
            "lllang": lllang_target,
            "lllimit": "max",
            "utf8": 1,
        }

        if site_code in ["en", "fr", "de"]:
            params["prop"] = "langlinks|templates"

        count = self._increment_api_call()

        logger.info(f"<<lightblue>> API CALL {count}: for {site_code}:{page_title}")

        # Submit the API request
        api_response = submitAPI(params, site_code, self.family)

        if not (api_response and "query" in api_response and "pages" in api_response["query"]):
            return False

        # Initialize counters and lists
        all_cat = 0
        hidden = 0
        cat_with = 0
        cat_without = 0

        # Get the pages from the query
        pages = api_response["query"]["pages"]
        results = {}
        cats_without_langlinks = []

        for _page_id, cat_data in pages.items():
            all_cat += 1

            # Get the category title
            cat_title = cat_data["title"]

            # Initialize the category details in the results
            results[cat_title] = {}

            if "redirects" in cat_data:
                self.page_is_redirect.setdefault(site_code, [])
                self.page_is_redirect[site_code].extend([red["from"] for red in cat_data["redirects"]])

            ns = cat_data.get("ns")
            if ns:
                results[cat_title]["ns"] = ns
                self.cache[(cat_title, site_code, "ns")] = ns

            if "templates" in cat_data:
                templates = [x["title"] for x in cat_data["templates"]]
                results[cat_title]["templates"] = templates
                self.cache[(cat_title, site_code, "templates")] = templates

            if "categories" in cat_data:
                logger.info("<<lightred>> 'categories' in cat_data")
                hidden += len([cat for cat in cat_data["categories"] if "hidden" in cat])

                categories = [cat["title"] for cat in cat_data["categories"] if "hidden" not in cat]

                results[cat_title]["categories"] = categories
                self.cache[(cat_title, site_code, "categories")] = categories

            if "langlinks" in cat_data:
                cat_with += 1
                for ll in cat_data["langlinks"]:
                    linked_page = ll["*"]
                    results[cat_title][ll["lang"]] = linked_page

                    # Cache forward and reverse links
                    cache_key2 = (cat_title, site_code, lllang_target, "en_links")
                    logger.debug(f" add cache_key2 : {cache_key2} : linked_page:{linked_page}")

                    self.cache[cache_key2] = linked_page

                    oppsite_tubb = (linked_page, lllang_target, site_code, "en_links")
                    logger.debug(f" add oppsite_tubb : {oppsite_tubb} : cat_title:{cat_title}")
                    self.cache[oppsite_tubb] = cat_title
            else:
                cat_without += 1
                cats_without_langlinks.append(cat_title)

        logger.debug(f'<<lightred>>find_Cat_without_hidden for {site_code}:{self.family}:page:"{page_title}" : ')

        logger.debug(
            f"<<lightblue>> \tfind {all_cat} cat, {cat_with} with links, {cat_without} without, hidden {hidden}"
        )

        # Update state for categories without langlinks
        if cats_without_langlinks:
            logger.debug("Categories without langlinks: " + (",a: ".join(cats_without_langlinks)))

            for cat in cats_without_langlinks:
                self.arpage_inside_en_cat.setdefault(cat, []).append(page_title)

        self.cache[cache_key] = results

        return results


# --- BACKWARD COMPATIBILITY LAYER ---
# This part ensures that any other file using this module will not break.


# 1. Create a single, global instance of the new class.
# The name LC_bot is chosen to match the original import `from c18_new import LCN_new`
LC_bot = WikiApiHandler()

# 2. Re-create the old functions as wrappers that call the new methods.

deleted_pages = LC_bot.get_deleting_page()


def find_LCN(enlink, prop="", lllang="", family="wikipedia", first_site_code="en"):
    # The new method is more generic, so we adapt the call.
    return LC_bot.find_page_data(page_title=enlink, prop=prop, lllang=lllang, site_code=first_site_code)


def find_Page_Cat_without_hidden(enlink, prop="", site_code="", family="wikipedia"):
    # The family parameter is now part of the instance, but we keep it for compatibility.
    return LC_bot.find_non_hidden_categories(page_title=enlink, prop=prop, site_code=site_code or "ar")


def get_arpage_inside_encat(key):
    return LC_bot.get_arpage_inside_encat(key)


def set_cache_L_C_N(key, value):
    LC_bot.cache[key] = value


def get_cache_L_C_N(key):
    return LC_bot.cache.get(key)


def get_deleted_pages():
    return deleted_pages
