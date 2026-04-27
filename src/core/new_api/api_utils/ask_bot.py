"""

from ...api_utils import ASK_BOT

"""

import difflib
import logging

from ....config import settings

yes_answer = ["y", "a", "", "Y", "A", "all", "aaa"]
Save_or_Ask = {}

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
            logger.warning(line)
        elif line.startswith("-") and not line.startswith("---"):
            logger.warning(line)
        else:
            logger.warning(line)


class ASK_BOT:
    def __init__(self):
        pass

    def ask_put(self, nodiff=False, newtext="", text="", message="", job="Genral", username="", summary=""):
        """
        Prompts the user to confirm saving changes to a page, optionally displaying a diff.

        If enabled by command-line arguments or parameters, shows the difference between the current and new text, displays summary information, and asks the user to accept or reject the changes. Supports skipping further prompts for subsequent edits.

        Args:
            nodiff: If True, skips displaying the diff.

        Returns:
            True if the user accepts the changes or prompting is not required; False otherwise.
        """
        message = message or "Do you want to accept these changes?"
        if settings.bot.ask and not Save_or_Ask.get(job):
            if text or newtext:
                if not settings.bot.no_diff and not nodiff:
                    if len(newtext) < 70000 and len(text) < 70000 or settings.bot.show_diff:
                        showDiff(text, newtext)
                    else:
                        logger.warning("showDiff error..")
                logger.warning(f"diference in bytes: {len(newtext) - len(text):,}")
                logger.warning(f"len of text: {len(text):,}, len of newtext: {len(newtext):,}")
            if summary:
                logger.warning(f"-Edit summary: {summary}")
            logger.warning(f"<<lightyellow>>ASK_BOT: {message}? (yes, no) {username=}")
            sa = input("([y]es, [N]o, [a]ll)?")
            if sa == "a":
                Save_or_Ask[job] = True
                logger.warning("<<lightgreen>> ---------------------------------")
                logger.warning(f"<<lightgreen>> save all:{job} without asking.")
                logger.warning("<<lightgreen>> ---------------------------------")
            if sa not in yes_answer:
                logger.warning("wrong answer")
                return False
        return True
