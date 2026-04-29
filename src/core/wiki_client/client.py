# wiki_client/client.py
# Public interface.  Compose cookies, requests_handler, and mwclient.Site
# into a single object other classes can use.

import logging
from pathlib import Path

import mwclient
import mwclient.errors

from . import config, cookies, requests_handler
from .exceptions import LoginError

logger = logging.getLogger(__name__)


class WikiLoginClient:
    """
    A thin wrapper around mwclient.Site that:

    - Persists the session across script runs via a Mozilla cookie jar.
    - Skips the login round-trip when saved cookies are still valid.
    - Transparently retries requests on CSRF errors and server maxlag.

    Usage
    -----
        client = WikiLoginClient(
            lang="en",
            family="wikipedia",
            username="MyBot",
            password="s3cr3t",
        )
        page = client.site.pages["Python"]
        print(page.text())

    The `site` property exposes the full mwclient.Site API.
    """

    def __init__(
        self,
        lang: str,
        family: str,
        username: str,
        password: str,
        cookies_dir: str = config.COOKIES_DIR,
    ) -> None:
        """
        Initialise the client, load any saved cookies, and ensure the session
        is authenticated before returning.

        Args:
            lang:        Language code, e.g. "en", "de", "fr".
            family:      Site family, e.g. "wikipedia", "wiktionary", "wikidata".
            username:    Bot / user account name.
            password:    Account password (or bot password).
            cookies_dir: Directory where cookie files are stored.
                         Defaults to config.COOKIES_DIR ("cookies/").
        """
        self.lang = lang
        self.family = family
        self.username = username
        self._password = password  # kept private — never log or expose this

        # ── Cookie path ────────────────────────────────────────────────────
        self._cookie_path: Path = cookies.get_cookie_path(cookies_dir, family, lang, username)

        # ── mwclient Site ──────────────────────────────────────────────────
        # mwclient.Site accepts a (family, lang) tuple to build the hostname.
        # e.g. ("wikipedia", "en") → en.wikipedia.org
        logger.debug("Creating mwclient.Site for %s.%s", lang, family)
        self._site = mwclient.Site(
            (family, lang),
            path=config.DEFAULT_PATH,
        )

        # ── Inject saved cookies ───────────────────────────────────────────
        # mwclient stores its requests.Session at site.connection.
        cookies.load_into_session(self._site.connection, self._cookie_path)

        # ── Wrap the session with retry / CSRF / maxlag logic ──────────────
        requests_handler.wrap_session(self._site.connection, self._site)

        # ── Authenticate if necessary ──────────────────────────────────────
        self._ensure_logged_in()

    # ── Public properties ──────────────────────────────────────────────────

    @property
    def site(self) -> mwclient.Site:
        """The underlying mwclient.Site — use this to interact with the wiki."""
        return self._site

    # ── Public methods ─────────────────────────────────────────────────────

    def login(self) -> None:
        """
        Force a fresh login regardless of cookie state.

        Call this if you know the session has expired and want to re-authenticate
        without creating a new WikiLoginClient instance.
        """
        logger.info("Forcing re-login for %s on %s.%s", self.username, self.lang, self.family)
        self._do_login()

    def save_cookies(self) -> None:
        """
        Persist the current session cookies to disk immediately.

        mwclient automatically saves cookies after login, but you can call this
        after a long batch of writes to checkpoint the session mid-run.
        """
        cookies.save_from_session(self._site.connection, self._cookie_path)
        logger.debug("Cookies saved to %s", self._cookie_path)

    # ── Private helpers ────────────────────────────────────────────────────

    def _ensure_logged_in(self) -> None:
        """
        Check whether the current session is authenticated.

        - If the loaded cookies are still valid, skip the login round-trip.
        - If not (anonymous session or expired cookies), perform a fresh login.
        """
        try:
            result = self._site.api("query", meta="userinfo")
            user_id = result["query"]["userinfo"]["id"]
        except Exception as exc:
            logger.warning("Could not check login status: %s — attempting login", exc)
            user_id = 0

        if user_id != 0:
            logger.info(
                "Session still valid for %s on %s.%s (uid=%d) — skipping login",
                self.username,
                self.lang,
                self.family,
                user_id,
            )
            return

        logger.info(
            "Anonymous session detected — logging in as %s on %s.%s",
            self.username,
            self.lang,
            self.family,
        )
        self._do_login()

    def _do_login(self) -> None:
        """
        Perform the mwclient login handshake and persist the resulting cookies.

        Raises:
            LoginError: if mwclient rejects the credentials.
        """
        try:
            self._site.login(self.username, self._password)
        except mwclient.errors.LoginError as exc:
            raise LoginError(f"Login failed for {self.username} on {self.lang}.{self.family}: {exc}") from exc

        logger.info(
            "Logged in successfully as %s on %s.%s",
            self.username,
            self.lang,
            self.family,
        )
        cookies.save_from_session(self._site.connection, self._cookie_path)

    def __repr__(self) -> str:
        return f"WikiLoginClient(" f"lang={self.lang!r}, " f"family={self.family!r}, " f"username={self.username!r})"
