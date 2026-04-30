# wiki_client/client.py
# Public interface. Composes cookies, requests_handler, and mwclient.Site
# into a single object other classes can use.

import functools
import logging
from pathlib import Path
from typing import Any, Optional

import mwclient
import mwclient.errors
import requests

from .config import COOKIES_DIR, DEFAULT_PATH
from .cookies import _delete_cookie_file, get_cookie_path, load_into_session, save_from_session
from .exceptions import LoginError, WikiClientError
from .requests_handler import wrap_session

logger = logging.getLogger(__name__)

# ── Merge #3: lru_cache session reuse ─────────────────────────────────────────
# If two classes instantiate WikiLoginClient for the same (lang, family,
# username) combination in the same process, they share one requests.Session
# instead of creating a second one and fighting over cookies.
# Cache size of 128 covers any realistic number of simultaneous wiki targets.


@functools.lru_cache(maxsize=128)
def _get_shared_session(lang: str, family: str, username: str) -> requests.Session:
    """Return (and cache) a requests.Session for the given wiki + user."""
    session = requests.Session()
    logger.debug("Created new session for %s.%s user=%s", lang, family, username)
    return session


class WikiLoginClient:
    """
    A thin wrapper around mwclient.Site that:

    - Persists the session across script runs via a Mozilla cookie jar.
    - Skips the login round-trip when saved cookies are still valid.
    - Transparently retries requests on CSRF errors and server maxlag.
    - Recovers automatically if the session expires mid-run
      (assertnameduserfailed).
    - Injects bot=1 and assertuser into all write-action requests.
    - Reuses the same requests.Session across instances for the same wiki+user.

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

        # Direct API call
        data = client.client_request({"action": "query", "titles": "Python"})

    The `site` property exposes the full mwclient.Site API.
    """

    # Write actions that need bot=1 and assertuser injected
    _WRITE_ACTIONS = {
        "edit",
        "create",
        "upload",
        "delete",
        "move",
        "wbeditentity",
        "wbsetclaim",
        "wbcreateclaim",
        "wbsetreference",
        "wbremovereferences",
        "wbsetaliases",
        "wbsetdescription",
        "wbsetlabel",
        "wbsetsitelink",
        "wbmergeitems",
        "wbcreateredirect",
    }

    def __init__(
        self,
        lang: str,
        family: str,
        username: str,
        password: str,
        cookies_dir: Optional[str] = None,
    ) -> None:
        """
        Initialise the client, load any saved cookies, and ensure the session
        is authenticated before returning.

        Args:
            lang:        Language code, e.g. "en", "de", "ar".
            family:      Site family, e.g. "wikipedia", "wiktionary", "wikidata".
            username:    Bot / user account name (bot-password suffix supported,
                         e.g. "MyBot@BotPassword").
            password:    Account password or bot password.
            cookies_dir: Directory where cookie files are stored.
                         Defaults to $HOME/cookies/ (or next to this file).
        """
        self.lang = lang
        self.family = family
        self.username = username
        self._password = password  # never logged or exposed

        # ── Cookie path ────────────────────────────────────────────────────
        self._cookie_path: Path = get_cookie_path(cookies_dir, family, lang, username)

        # ── Shared / cached session ────────────────────────────────────────
        # Merge #3: reuse the same session for the same (lang, family, user)
        shared_session = _get_shared_session(lang, family, username)

        # ── mwclient Site ──────────────────────────────────────────────────
        # Pass our shared session in so mwclient doesn't create its own.
        logger.debug("Creating mwclient.Site for %s.%s", lang, family)

        self.api_url = f"https://{self.lang}.{self.family}.org/w/api.php"
        self._site = mwclient.Site(
            f"{self.lang}.{self.family}.org",
            path=DEFAULT_PATH,
            pool=shared_session,  # inject the shared session
        )

        # ── Inject saved cookies ───────────────────────────────────────────
        load_into_session(self._site.connection, self._cookie_path)

        # ── Wrap the session with retry / CSRF / maxlag logic ──────────────
        wrap_session(self._site.connection, self._site)

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

        Call this if you know the session has expired and want to
        re-authenticate without creating a new WikiLoginClient instance.
        """
        logger.info("Forcing re-login for %s on %s.%s", self.username, self.lang, self.family)
        self._do_login()

    def save_cookies(self) -> None:
        """
        Persist the current session cookies to disk immediately.

        Called automatically after every login, but you can call this manually
        to checkpoint the session after a long batch of writes.
        """
        save_from_session(self._site.connection, self._cookie_path)
        logger.debug("Cookies saved to %s", self._cookie_path)

    def client_request(
        self,
        params: dict,
        method: str = "post",
        files: Optional[Any] = None,
    ) -> dict:
        """
        Send a GET or POST request to the wiki API and return the parsed JSON.

        Handles automatically:
          - format=json injection
          - bot=1 + assertuser for write actions (Merge #5)
          - CSRF token refresh and maxlag backoff (via session wrapper)
          - assertnameduserfailed mid-run session recovery (Merge #4)

        Args:
            params: MediaWiki API parameters as a plain dict.
                    ``format`` defaults to ``"json"`` if not supplied.
            method: ``"get"`` (default) or ``"post"``. Case-insensitive.
                    Use POST for write operations or large payloads.
            files:  Optional ``{field_name: file-like}`` dict for multipart
                    uploads. Forces POST automatically when supplied.

        Returns:
            Parsed JSON response as a dict.

        Raises:
            ValueError:         If *method* is not ``"get"`` or ``"post"``.
            WikiClientError:    On API-level errors not handled by retries.
            requests.HTTPError: On non-2xx HTTP responses.

        Examples::

            # Read
            data = client.client_request({"action": "query", "titles": "Python"})

            # Write (bot=1 and assertuser injected automatically)
            data = client.client_request(
                {"action": "edit", "title": "Sandbox", "text": "hello",
                 "summary": "test", "token": client.site.get_token("csrf")},
                method="post",
            )

            # Upload
            with open("image.png", "rb") as fh:
                data = client.client_request(
                    {"action": "upload", "filename": "image.png",
                     "token": client.site.get_token("csrf")},
                    method="post",
                    files={"file": fh},
                )
        """
        method = method.lower()
        if method not in ("get", "post"):
            raise ValueError(f"method must be 'get' or 'post', got {method!r}")

        if files is not None:
            method = "post"

        # Always JSON unless caller overrides
        params = {"format": "json", **params}

        # Merge #5: inject bot flag and identity assertion for write actions
        params = self._enrich_params(params)

        session: requests.Session = self._site.connection

        logger.debug(
            "%s %s action=%s files=%s",
            method.upper(),
            self.api_url,
            params.get("action"),
            list(files.keys()) if files else None,
        )

        # Merge #4: assertnameduserfailed recovery — retry once after re-login
        for attempt in range(2):
            if method == "get":
                response = session.request("GET", self.api_url, params=params)
            elif files:
                params["token"] = self._site.get_token("csrf")
                response = session.request("POST", self.api_url, data=params, files=files)
            else:
                params["token"] = self._site.get_token("csrf")
                response = session.request("POST", self.api_url, data=params)

            response.raise_for_status()
            result: dict = response.json()

            error = result.get("error", {})
            if not error:
                return result

            error_code = error.get("code", "")

            # ── assertnameduserfailed: session expired silently mid-run ────
            # Matches super_login.py post_it_parse_data recovery logic.
            if error_code == "assertnameduserfailed":
                if attempt == 0:
                    logger.warning(
                        "assertnameduserfailed for %s on %s.%s — " "clearing cookies and re-logging in",
                        self.username,
                        self.lang,
                        self.family,
                    )
                    # Nuke the stale cookie file and the cached session
                    _delete_cookie_file(self._cookie_path, reason="assertnameduserfailed")
                    _get_shared_session.cache_clear()
                    self._do_login()
                    continue  # retry the original request
                else:
                    raise WikiClientError(
                        f"assertnameduserfailed persists after re-login for "
                        f"{self.username} on {self.lang}.{self.family}"
                    )

            # All other errors — surface to the caller
            raise WikiClientError(f"API error {error_code or 'unknown'}: " f"{error.get('info', error)}")

        # Should never be reached
        return {}

    # ── Private helpers ────────────────────────────────────────────────────

    def _enrich_params(self, params: dict) -> dict:
        """
        Merge #5: inject write-action safety params.

        For any action that modifies wiki content:
          - ``bot=1``        marks edits as bot edits in the recent-changes log.
          - ``assertuser``   makes the API reject the request if the session
                             user doesn't match, preventing accidental edits
                             under the wrong account.

        Read-only actions (query, etc.) are left untouched.
        Also cleans up query params that don't belong in write requests
        (matches your old filter_params / params_w logic).
        """
        params = dict(params)
        action = params.get("action", "")

        # Strip write-only params from query actions
        if action == "query":
            params.pop("bot", None)
            params.pop("summary", None)
            return params

        # Inject bot marker and identity assertion for all write actions
        is_write = action in self._WRITE_ACTIONS or action.startswith("wb") or self.family == "wikidata"

        if is_write and self.username:
            params.setdefault("bot", 1)
            params.setdefault("assertuser", self.username)

        return params

    def _ensure_logged_in(self) -> None:
        """
        Check whether the current session is authenticated.

        Uses the userinfo API — if the returned user ID is 0 (anonymous),
        performs a fresh login. Otherwise the loaded cookies are still valid
        and we skip the round-trip entirely.
        """
        try:
            result = self._site.api("query", meta="userinfo")
            userinfo = result["query"]["userinfo"]
            user_id = userinfo.get("id", 0)
        except Exception as exc:
            logger.warning("Could not check login status (%s) — attempting login", exc)
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
            "Anonymous session — logging in as %s on %s.%s",
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
            raise LoginError(f"Login failed for {self.username} on " f"{self.lang}.{self.family}: {exc}") from exc

        logger.info(
            "Logged in successfully as %s on %s.%s",
            self.username,
            self.lang,
            self.family,
        )
        save_from_session(self._site.connection, self._cookie_path)

    def __repr__(self) -> str:
        return f"WikiLoginClient(" f"lang={self.lang!r}, " f"family={self.family!r}, " f"username={self.username!r})"


__all__ = [
    "WikiLoginClient",
]
