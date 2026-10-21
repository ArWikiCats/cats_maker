import logging

from ...shared.wd_clients.wd_api import (
    add_labels,
    get_sitelinks_from_wikidata,
    log_to_wikidata,
    log_to_wikidata_qid,
)

logger = logging.getLogger(__name__)


class CategoryWikidataService:
    """Wikidata operations needed while creating a category (lookup, label, logging)."""

    def __init__(self, wiki_site_ar: dict, wiki_site_en: dict) -> None:
        self.wiki_site_ar = wiki_site_ar
        self.wiki_site_en = wiki_site_en

    def _get_site_identifiers(self) -> tuple[str, str]:
        """Get the Arabic and English site identifiers based on wiki family."""
        ar_site_wiki = "arwiki"
        en_site_lang = self.wiki_site_en["code"]  # "en"

        if (
            self.wiki_site_en["family"] != "wikipedia"
            and self.wiki_site_en["code"] != "commons"
        ):
            ar_site_wiki = f"ar{self.wiki_site_ar['family']}"
            en_site_lang = self.wiki_site_en["code"] + self.wiki_site_en["family"]

        return ar_site_wiki, en_site_lang

    def check_sitelink(self, en_page_title: str) -> tuple[bool, dict]:
        """Check if an Arabic sitelink exists in Wikidata for the English page."""
        ar_site_wiki, en_site_lang = self._get_site_identifiers()

        ar_info = get_sitelinks_from_wikidata(en_site_lang, en_page_title) or {}

        if (
            ar_info
            and ("sitelinks" in ar_info)
            and (ar_site_wiki in ar_info["sitelinks"])
        ):
            ar_page = ar_info["sitelinks"][ar_site_wiki]
            logger.debug(f'found "{ar_site_wiki}" link "{ar_page}" for en cat.')
            return True, ar_info

        logger.debug(f'No "{ar_site_wiki}" link for en cat "{en_page_title}"')
        return False, ar_info

    def add_arabic_label(self, qid: str, ar_title: str) -> None:
        """Add the Arabic label to the Wikidata item."""
        add_labels(qid, ar_title, "ar")

    def log_creation(self, ar_title: str, en_page_title: str, qid: str) -> None:
        """Log the created category to Wikidata (by QID when known)."""
        if qid:
            log_to_wikidata_qid(ar_title, qid)
        else:
            log_to_wikidata(ar_title, en_page_title)
