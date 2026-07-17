# api_client/cookies.py
# Pure functions for loading and saving a MozillaCookieJar.
# No class, no state — compose with anything that holds a requests.Session.

import logging
import os
import stat
import http.cookiejar
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# Cookie files older than this are treated as stale and deleted before loading.
_COOKIE_MAX_AGE_DAYS = 3


def get_cookie_path(
    cookies_dir: str,
    family: str,
    lang: str,
    username: str,
) -> Path:
    """
    Return the cookie file path for the given site + user combination.

    Base directory resolution order (mirrors your old cookies_bot.py):
      1. *cookies_dir* if explicitly passed.
      2. $HOME/cookies/ if the HOME env var is set.
      3. A cookies/ folder next to this file as a last resort.

    Convention: {cookies_dir}/{family}_{lang}_{username}.mozilla
    Example:    ~/cookies/wikipedia_en_mybot.mozilla

    The directory is created if it does not already exist.
    Normalisation: family, lang, and the base part of username are lowercased;
    spaces replaced with underscores; bot-password suffix (@...) stripped.
    """
    # ── Resolve base directory ─────────────────────────────────────────────
    base = Path(cookies_dir)

    base.mkdir(parents=True, exist_ok=True)

    # Set group-readable permissions on the directory (matches old chmod logic)
    try:
        os.chmod(base, stat.S_IRWXU | stat.S_IRWXG)
    except OSError as exc:
        logger.debug("Could not chmod cookies dir %s: %s", base, exc)

    logger.info("cookie path: %s", base)

    # ── Normalise filename components ──────────────────────────────────────
    family = family.lower()
    lang = lang.lower()
    # Strip bot-password suffix (e.g. "MyBot@BotPassword" -> "mybot")
    username = username.lower().replace(" ", "_").split("@")[0]

    file_path = base / f"{family}_{lang}_{username}.mozilla"
    logger.debug("resolved cookie file: %s", file_path)

    # ── Stale / empty file guard (from your check_if_file_is_old) ─────────
    _delete_if_stale(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path


def _delete_if_stale(path: Path) -> None:
    """
    Delete the cookie file if it is zero-bytes or older than _COOKIE_MAX_AGE_DAYS.

    Silently does nothing if the file does not exist.
    """
    if not path.exists():
        return

    # Zero-byte file is useless
    if path.stat().st_size == 0:
        _delete_cookie_file(path, reason="zero-byte file")
        return

    # File too old — the session it contains has almost certainly expired
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    if age > timedelta(days=_COOKIE_MAX_AGE_DAYS):
        _delete_cookie_file(path, reason=f"older than {_COOKIE_MAX_AGE_DAYS} days ({age.days}d)")


def _delete_cookie_file(path: Path, reason: str = "") -> None:
    """Delete a cookie file, logging the outcome."""
    try:
        path.unlink(missing_ok=True)
        logger.debug("Deleted stale cookie file %s (%s)", path, reason)
    except OSError as exc:
        logger.exception("Could not delete cookie file %s: %s", path, exc)


# ---------------------------------------------------------------------------
# CookiesClient — isolated cookie I/O (unchanged from original)
# ---------------------------------------------------------------------------


class CookiesClient:
    """Static helpers for loading and persisting LWP cookie jars."""

    @staticmethod
    def save_cookies(cj: http.cookiejar.LWPCookieJar) -> None:
        """
        Persist the current session cookies to disk immediately.

        Called automatically after every login, but you can call this manually
        to checkpoint the session after a long batch of writes.
        """
        try:
            # Save cookies to disk, ignoring discard and expire attributes
            cj.save(ignore_discard=True, ignore_expires=True)
            # Log successful cookie save operation
            logger.debug("Cookies saved to _cookie_path")
        except Exception:
            # Log any exceptions that occur during cookie saving
            logger.exception("Failed to save cookies")

    @staticmethod
    def _make_cookiejar(cookie_path: Path) -> http.cookiejar.LWPCookieJar:
        # Create a new LWPCookieJar instance with the specified path
        cj = http.cookiejar.LWPCookieJar(cookie_path)
        if cookie_path.exists():
            try:
                cj.load(ignore_discard=True, ignore_expires=True)
            except Exception as exc:
                logger.error("Error loading cookies: %s", exc)
        return cj


__all__ = [
    "CookiesClient",
    "get_cookie_path",
]
