import logging

logger = logging.getLogger(__name__)

# Category processing state - encapsulated in module-level variables
# These are cleared between runs to prevent state leakage
_done_d: list = []
_new_cat_done: dict = {}
_already_created: list = []


def clear_processing_state() -> None:
    """Clear all processing state. Call between runs to prevent state leakage."""
    _done_d.clear()
    _new_cat_done.clear()
    _already_created.clear()


def get_processing_state():
    """Get current processing state for testing/debugging."""
    return {
        "done_d": list(_done_d),
        "new_cat_done": dict(_new_cat_done),
        "already_created": list(_already_created),
    }


def _scan_ar_title(title) -> bool:
    if title in _already_created:
        logger.debug(f'title "{title}". in _already_created')
        return False

    cat3 = str(title)
    if cat3 in _new_cat_done.keys():
        _new_cat_done[cat3] += 1
        logger.debug(f'We tried {_new_cat_done[cat3]} times to/created title:"{cat3}".')
        return False
    else:
        if cat3 in _new_cat_done.keys():
            logger.debug(f'2070:new trying with cat: "{title}"')
            _new_cat_done[cat3] += 1
        else:
            _new_cat_done[cat3] = 1
    return True


__all__ = [
    "get_processing_state",
    "clear_processing_state",
    "_scan_ar_title",
]
