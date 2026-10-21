import logging

logger = logging.getLogger(__name__)


class CategoryManagerStats:
    """Manages the creation and processing of Wikipedia categories."""

    def __init__(self) -> None:
        # Category processing state
        self._done_d: list[str] = []
        self._new_cat_done: dict[str, int] = {}
        self._already_created: list[str] = []

    def clear_processing_state(self) -> None:
        """Clear all processing state to prevent state leakage between runs."""
        self._done_d.clear()
        self._new_cat_done.clear()
        self._already_created.clear()

    def check_done_d(self, title: str) -> bool:
        """Check if the category has already been processed."""
        return title in self._done_d

    def insert_done_d(self, title: str) -> None:
        self._done_d.append(title)

    def insert_already_created(self, title: str) -> None:
        self._already_created.append(title)

    def get_processing_state(self) -> dict:
        """Get the current processing state for testing and debugging."""
        return {
            "done_d": list(self._done_d),
            "new_cat_done": dict(self._new_cat_done),
            "already_created": list(self._already_created),
        }

    def _scan_ar_title(self, title: str) -> bool:
        if title in self._already_created:
            logger.debug(f'title "{title}" is in _already_created')
            return False

        cat3 = str(title)
        if cat3 in self._new_cat_done:
            self._new_cat_done[cat3] += 1
            logger.debug(f'We tried {self._new_cat_done[cat3]} times to create title: "{cat3}".')
            return False
        else:
            self._new_cat_done[cat3] = 1
        return True


__all__ = [
    "CategoryManagerStats",
]
