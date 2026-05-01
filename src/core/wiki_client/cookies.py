# wiki_client/cookies.py
# Pure functions for loading and saving a MozillaCookieJar.
# No class, no state — compose with anything that holds a requests.Session.

import logging
import os
import stat
from datetime import datetime, timedelta
from http.cookiejar import LoadError, MozillaCookieJar
from pathlib import Path

import requests
from requests.cookies import RequestsCookieJar

from .exceptions import CookieError

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

    # ── Normalise filename components ──────────────────────────────────────
    family = family.lower()
    lang = lang.lower()
    # Strip bot-password suffix (e.g. "MyBot@BotPassword" -> "mybot")
    username = username.lower().replace(" ", "_").split("@")[0]

    file_path = base / f"{family}_{lang}_{username}.mozilla"

    # ── Stale / empty file guard (from your check_if_file_is_old) ─────────
    _delete_if_stale(file_path)

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


def load_into_session(session: requests.Session, path: Path) -> bool:
    """
    Load a Mozilla cookie file into *session*.

    Returns True  if cookies were loaded successfully.
    Returns False if the file does not exist (caller should re-login).

    On a corrupt or unreadable file: logs a warning and returns False so the
    caller can fall back to a fresh login rather than crashing.
    """
    jar = MozillaCookieJar(str(path))

    if not path.exists():
        logger.debug("Cookie file not found: %s — will require login", path)
        session.cookies = RequestsCookieJar()
        return False

    try:
        # ignore_discard=True:  keep session cookies that have no expiry set
        # ignore_expires=True:  load all cookies; stale ones were already
        #                       removed by _delete_if_stale in get_cookie_path
        jar.load(ignore_discard=True, ignore_expires=True)
        logger.debug("Loaded %d cookies from %s", len(jar), path)
    except (LoadError, OSError) as exc:
        logger.exception("Could not load cookie file %s (%s) — will require login", path, exc)
        session.cookies = RequestsCookieJar()
        return False

    # requests.Session.cookies expects a RequestsCookieJar for full dict-style
    # access (.get(), ["key"], iteration). Copy all cookies from the Mozilla
    # jar into one so the session behaves normally.
    rcj = RequestsCookieJar()
    rcj.update(jar)
    session.cookies = rcj
    return True


def save_from_session(session: requests.Session, path: Path) -> None:
    """
    Save the current session cookies to a Mozilla cookie file.

    Persists session cookies that have no explicit expiry (ignore_discard=True)
    so the next cold-start can skip the login round-trip.

    File is written with mode 0o600 (owner read/write only).

    Raises CookieError on any write failure.
    """
    jar = MozillaCookieJar(str(path))
    for cookie in session.cookies:
        jar.set_cookie(cookie)

    try:
        jar.save(ignore_discard=True, ignore_expires=True)
    except OSError as exc:
        raise CookieError(f"Failed to save cookies to {path}: {exc}") from exc

    # Restrict to owner read/write only — cookie files contain auth credentials
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError as exc:
        logger.warning("Could not set permissions on %s: %s", path, exc)

    logger.debug("Saved %d cookies to %s", len(jar), path)


__all__ = [
    "get_cookie_path",
    "load_into_session",
    "save_from_session",
]
