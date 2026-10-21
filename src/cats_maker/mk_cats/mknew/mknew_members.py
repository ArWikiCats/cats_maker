import logging
from collections.abc import Callable

from ..add_bot import add_to_page

logger = logging.getLogger(__name__)


class CategoryMembersAdder:
    """Adds a category to its member pages."""

    def __init__(self, add_to_page_func: Callable | None = None) -> None:
        self.add_to_page = add_to_page_func or add_to_page

    def add(self, final_list: list, title: str, callback: Callable | None = None) -> None:
        """Add the category `title` to every page in `final_list`."""
        title = title.replace("_", " ")

        if not title.startswith("تصنيف:"):
            title = f"تصنيف:{title}"

        if not final_list:
            return

        for n, page in enumerate(final_list, start=1):
            logger.info(f"cat:{title} page:{page} n:{n}/{len(final_list)}")
            save = self.add_to_page(page, title)
            if save and callback:
                try:
                    callback(title)
                except Exception as e:
                    logger.info(f"Error in callback: {e}")

    @staticmethod
    def log_members_info(members: list) -> None:
        """Log information about collected members."""
        formatted_member_list = ""
        if members and len(members) < 30:
            formatted_member_list = ",".join(members)
        logger.debug(f"Add to {len(members)} pages: {formatted_member_list}")
