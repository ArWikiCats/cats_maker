import difflib
import logging
from .printe_helper import make_str
logger = logging.getLogger(__name__)


def showDiff(oldtext: str, newtext: str) -> None:
    """Show the difference between two text strings using the logger."""

    diff = difflib.unified_diff(
        oldtext.splitlines(),
        newtext.splitlines(),
        lineterm="",
        fromfile="Old Text",
        tofile="New Text",
    )
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            logger.warning(make_str(f"<<lightgreen>>{line}<<default>>"))
        elif line.startswith("-") and not line.startswith("---"):
            logger.warning(make_str(f"<<lightred>>{line}<<default>>"))
        else:
            logger.warning(make_str(line))
