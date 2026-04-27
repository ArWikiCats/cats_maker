"""Business Logic Service."""

import logging
import re
from typing import List

from .config import ConfigLoader
from .repository import CategoryRepository

logger = logging.getLogger(__name__)


class CategoryComparator:
    """
    Service class to compare categories between English and Arabic Wikipedias.
    """

    def __init__(self):
        self.repo = CategoryRepository()
        self.config = ConfigLoader()

    @staticmethod
    def normalize_category_title(title: str, prefix_pattern: str) -> str:
        """Strip a category prefix and normalise spaces to underscores."""
        if not title:
            return title
        # Remove prefix case-insensitively
        cleaned = re.sub(prefix_pattern, "", title, flags=re.IGNORECASE)
        # Replace spaces with underscores for consistency
        return cleaned.replace(" ", "_")

    def get_exclusive_category_titles(self, en_category: str, ar_category: str) -> List[str]:
        """
        Return English-wiki titles that are in en_category but absent from ar_category.

        Args:
            en_category: Name of the English category.
            ar_category: Name of the Arabic category.

        Returns:
            List of exclusive titles. Empty list if not in production or on error.
        """
        if not self.config.is_production():
            logger.info("Skipping category comparison: Not in production environment.")
            return []

        # Normalize inputs
        ar_title_clean = self.normalize_category_title(ar_category, "تصنيف:")
        en_title_clean = self.normalize_category_title(en_category, r"(\[\[en:)|(category:)|(\]\])")

        if not en_title_clean:
            logger.warning("Invalid category titles provided.")
            return []

        logger.info("Starting comparison for EN: '%s' and AR: '%s'", en_category, ar_category)

        # Fetch data from repositories
        en_titles = self.repo.fetch_english_titles_with_arabic_links(en_title_clean)

        ar_titles_set = set()

        if ar_title_clean:
            ar_titles = self.repo.fetch_arabic_titles_with_english_links(ar_title_clean)
            # Convert AR titles to a set for O(1) lookup performance
            ar_titles_set = set(ar_titles)

        logger.debug("Found %d EN titles and %d AR titles", len(en_titles), len(ar_titles))

        # Find exclusive titles
        exclusive = [t for t in en_titles if t not in ar_titles_set]

        logger.info("Comparison complete. Found %d exclusive titles.", len(exclusive))
        return exclusive
