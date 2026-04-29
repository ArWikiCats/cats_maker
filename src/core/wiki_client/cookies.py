# wiki_client/cookies.py
# Pure functions for loading and saving a MozillaCookieJar.
# No class, no state — compose with anything that holds a requests.Session.

import logging
import os
import stat
from http.cookiejar import LoadError, MozillaCookieJar
from pathlib import Path

import requests
from requests.cookies import RequestsCookieJar

from . import config
from .exceptions import CookieError

logger = logging.getLogger(__name__)


def get_cookie_path(
    cookies_dir: str,
    family: str,
    lang: str,
    username: str,
) -> Path:
    """
    Return the cookie file path for the given site + user combination.

    Convention: {cookies_dir}/{family}_{lang}_{username}.mozilla
    Example:    cookies/wikipedia_en_MyBot.mozilla

    The directory is created if it does not already exist.
    """
    path = Path(cookies_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{family}_{lang}_{username}.mozilla"


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
        # ignore_expires=False: expired cookies are silently skipped by the jar
        # ignore_discard=True:  keep session cookies that have no expiry set
        jar.load(ignore_discard=True, ignore_expires=False)
    except (LoadError, OSError) as exc:
        logger.warning("Could not load cookie file %s (%s) — will require login", path, exc)
        session.cookies = RequestsCookieJar()
        return False

    # requests.Session.cookies expects a RequestsCookieJar for full dict-style
    # access. Copy all cookies from the Mozilla jar into one.
    rcj = RequestsCookieJar()
    rcj.update(jar)
    session.cookies = rcj
    logger.debug("Loaded %d cookies from %s", len(jar), path)
    return True


def save_from_session(session: requests.Session, path: Path) -> None:
    """
    Save the current session cookies to a Mozilla cookie file.

    Persists session cookies that have no explicit expiry (ignore_discard=True)
    and ignores whether cookies are flagged as expired in metadata
    (ignore_expires=True) so nothing is accidentally dropped on save.

    File is written with mode 0o600 (owner read/write only).

    Raises CookieError on any write failure.
    """
    # Build a fresh MozillaCookieJar targeting the destination path, then copy
    # every cookie from the session jar into it.
    jar = MozillaCookieJar(str(path))
    for cookie in session.cookies:
        jar.set_cookie(cookie)

    try:
        jar.save(ignore_discard=True, ignore_expires=True)
    except OSError as exc:
        raise CookieError(f"Failed to save cookies to {path}: {exc}") from exc

    # Restrict to owner read/write only — cookies contain auth credentials
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError as exc:
        logger.warning("Could not set permissions on %s: %s", path, exc)

    logger.debug("Saved %d cookies to %s", len(jar), path)
