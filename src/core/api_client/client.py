"""

Examples::

client = WikiLoginClient(
    lang="en",
    family="wikipedia",
    username="MyBot",
    password="s3cr3t",
)
# Simple read
data = client.client_request({"action": "query", "titles": "Python"})

# Write — POST with auto CSRF + retry handling
data = client.client_request(
    {
        "action": "edit",
        "title": "Sandbox",
        "text": "hello",
        "summary": "test",
    },
    method="post",
)
"""

from __future__ import annotations

import copy
import http.cookiejar
import logging
import time
from pathlib import Path
from typing import Any, Optional, Union

import mwclient
import mwclient.errors
import requests

from ...config import settings
from . import config
from .cookies import _delete_cookie_file, get_cookie_path
from .exceptions import CSRFError, LoginError, MaxlagError, WikiClientError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RequestsHandler — transport + retry layer
# ---------------------------------------------------------------------------


class RequestsHandler:
    """
    Owns a requests.Session and drives every HTTP call through a unified
    retry loop that handles:

    - CSRF / bad token        → refresh token, reinject, retry
    - maxlag                  → exponential back-off, retry
    - assertnameduserfailed   → delegate re-login hook, retry once
    """

    # ------------------------------------------------------------------
    # Abstract-ish contract that subclasses must satisfy
    # ------------------------------------------------------------------

    @property
    def _session(self) -> requests.Session:
        raise NotImplementedError

    def _refresh_csrf_token(self) -> str:
        raise NotImplementedError

    def _on_assertnameduserfailed(self) -> None:
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Core request execution — the only method that touches the network
    # ------------------------------------------------------------------

    def _execute_request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        files: Optional[Any] = None,
    ) -> requests.Response:
        return self._session.request(
            method,
            url,
            params=params,
            data=data,
            files=files,
        )

    # ------------------------------------------------------------------
    # Retry loop
    # ------------------------------------------------------------------

    def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        files: Optional[Any] = None,
        assertnameduser_retries: int = 1,
    ) -> dict:
        """
        Execute a request and automatically retry on transient API errors.

        Works on copies of params/data so per-retry mutations never bleed
        into the caller's dict.

        Raises:
            CSRFError:          After exhausting CSRF token retries.
            MaxlagError:        After exhausting maxlag retries.
            WikiClientError:    On assertnameduserfailed or other API errors.
            requests.HTTPError: On non-2xx HTTP responses.
        """
        # Defensive copies — don't mutate the caller's dicts across retries
        working_params = dict(params) if params else {}
        working_data = dict(data) if data else {}

        attempt = 0
        named_user_attempts = 0

        while attempt < config.MAX_RETRIES:
            response = self._execute_request(
                method,
                url,
                params=working_params or None,
                data=working_data or None,
                files=files,
            )
            response.raise_for_status()

            # Only inspect JSON responses — pass everything else straight through
            if "application/json" not in response.headers.get("Content-Type", ""):
                return {}

            try:
                body: dict = response.json()
            except ValueError:
                return {}

            error = body.get("error", {})
            if not error:
                return body  # ← happy path

            error_code: str = error.get("code", "")
            error_info: str = error.get("info", "")

            # ── CSRF ──────────────────────────────────────────────────────
            if self._is_csrf_error(error_code, error_info):
                attempt += 1
                if attempt >= config.MAX_RETRIES:
                    raise CSRFError(
                        f"CSRF token remained invalid after {config.MAX_RETRIES} "
                        f"attempts. Last error: {error_info or error_code}"
                    )
                working_data, working_params = self._handle_csrf(
                    error_code, error_info, attempt, working_data, working_params
                )
                continue

            # ── maxlag ────────────────────────────────────────────────────
            if error_code == "maxlag":
                attempt += 1
                if attempt >= config.MAX_RETRIES:
                    raise MaxlagError(f"Server maxlag not resolved after {config.MAX_RETRIES} attempts.")
                self._handle_maxlag(response, attempt)
                continue

            # ── assertnameduserfailed ─────────────────────────────────────
            if error_code == "assertnameduserfailed":
                if named_user_attempts >= assertnameduser_retries:
                    raise WikiClientError("assertnameduserfailed persists after re-login")
                named_user_attempts += 1
                logger.warning(
                    "assertnameduserfailed — attempting recovery (try %d/%d)",
                    named_user_attempts,
                    assertnameduser_retries,
                )
                self._on_assertnameduserfailed()
                attempt = 0  # Reset CSRF/maxlag budget after re-login
                continue

            # ── No retryable error — surface to the caller ────────────────
            raise WikiClientError(f"API error {error_code}: {error_info}")

        raise MaxlagError(f"Exceeded {config.MAX_RETRIES} retries without a successful response.")

    # ------------------------------------------------------------------
    # Protected CSRF helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_csrf_error(code: str, info: str) -> bool:
        return code in ("badtoken", "notoken") or info == "Invalid CSRF token."

    def _handle_csrf(
        self,
        error_code: str,
        error_info: str,
        attempt: int,
        data: dict,
        params: dict,
    ) -> tuple[dict, dict]:
        """Refresh the CSRF token and reinject it into whichever dict carries it.

        Returns updated (data, params) copies — never mutates in place.
        """
        logger.debug(
            "CSRF error (%s) — refreshing token (attempt %d/%d)",
            error_code or error_info,
            attempt,
            config.MAX_RETRIES,
        )
        try:
            new_token = self._refresh_csrf_token()
        except Exception as exc:
            raise CSRFError(f"Failed to refresh CSRF token: {exc}") from exc

        return self._inject_token(new_token, data, params)

    @staticmethod
    def _inject_token(token: str, data: dict, params: dict) -> tuple[dict, dict]:
        """Return (data, params) copies with ``token`` updated to *token*.

        Only one dict should ever carry the key; we update the first match.
        """
        for bucket_name, bucket in (("data", data), ("params", params)):
            if "token" in bucket:
                bucket = dict(bucket)
                bucket["token"] = token
                logger.debug("Injected new CSRF token into %s", bucket_name)
                if bucket_name == "data":
                    return bucket, params
                return data, bucket
        return data, params

    # ------------------------------------------------------------------
    # Protected maxlag helper
    # ------------------------------------------------------------------

    def _handle_maxlag(self, response: requests.Response, attempt: int) -> None:
        """Sleep for the server-requested delay (or exponential back-off)."""
        retry_after = response.headers.get(config.MAXLAG_HEADER)
        try:
            delay = float(retry_after) if retry_after is not None else None
        except ValueError:
            delay = None

        if delay is None:
            delay = config.BACKOFF_BASE * (2**attempt)

        logger.debug(
            "maxlag — sleeping %.1f s (attempt %d/%d)",
            delay,
            attempt,
            config.MAX_RETRIES,
        )
        time.sleep(delay)


# ---------------------------------------------------------------------------
# CookiesClient — cookie I/O helpers
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
            cj.save(ignore_discard=True, ignore_expires=True)
            logger.debug("Cookies saved to _cookie_path")
        except Exception:
            logger.exception("Failed to save cookies")

    @staticmethod
    def _make_cookiejar(cookie_path: Path) -> http.cookiejar.LWPCookieJar:
        cj = http.cookiejar.LWPCookieJar(cookie_path)
        if cookie_path.exists():
            try:
                cj.load(ignore_discard=True, ignore_expires=True)
            except Exception as exc:
                logger.error("Error loading cookies: %s", exc)
        return cj


# ---------------------------------------------------------------------------
# WikiLoginClient — business layer
# ---------------------------------------------------------------------------


class WikiLoginClient(CookiesClient, RequestsHandler):
    """
    A thin wrapper around mwclient.Site that:

    - Persists the session across script runs via a Mozilla cookie jar.
    - Skips the login round-trip when saved cookies are still valid.
    - Transparently retries requests on CSRF errors and server maxlag.
    - Recovers automatically if the session expires mid-run
      (assertnameduserfailed).
    - Injects bot=1 and assertuser into all write-action requests.

    RequestsHandler provides the transport/retry layer; this class owns
    only auth logic, parameter enrichment, and continuation pagination.
    """

    _WRITE_ACTIONS: frozenset[str] = frozenset(
        {
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
    )

    def __init__(
        self,
        lang: str,
        family: str,
        username: str,
        password: str,
        cookies_dir: str = settings.paths.cookies_dir,
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
                         Defaults to settings.paths.cookies_dir.
        """
        self.lang = lang
        self.family = family
        self.username = username
        self._password = password  # kept private — never log or expose this

        self._cookie_path: Path = get_cookie_path(cookies_dir, family, lang, username)

        logger.debug("Creating mwclient.Site for %s.%s", lang, family)
        self.api_url = f"https://{self.lang}.{self.family}.org/w/api.php"

        try:
            self._site = mwclient.Site(f"{self.lang}.{self.family}.org")
        except mwclient.errors.InvalidSiteIdError:
            raise WikiClientError(f"Invalid site ID: {self.lang}.{self.family}")

        # ── Inject saved cookies ───────────────────────────────────────────
        # mwclient stores its requests.Session at site.connection.
        self.cj = self._make_cookiejar(self._cookie_path)
        self._site.connection.cookies = self.cj

        # ── Authenticate if necessary ──────────────────────────────────────
        self._ensure_logged_in()

    # ------------------------------------------------------------------
    # RequestsHandler contract — concrete implementations
    # ------------------------------------------------------------------

    @property
    def _session(self) -> requests.Session:
        """The mwclient-managed session."""
        return self._site.connection

    def _refresh_csrf_token(self) -> str:
        """Force mwclient to fetch a fresh CSRF token from the server."""
        return self._site.get_token("csrf", force=True)

    def _on_assertnameduserfailed(self) -> None:
        """
        Session expired mid-run: nuke stale cookies and re-authenticate.
        Called by the base-class retry loop; never call directly.
        """
        logger.warning(
            "assertnameduserfailed for %s on %s.%s — clearing cookies and re-logging in",
            self.username,
            self.lang,
            self.family,
        )
        _delete_cookie_file(self._cookie_path, reason="assertnameduserfailed")
        self._do_login()

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
        if not self._site.logged_in:
            logger.info(
                "Forcing re-login for %s on %s.%s",
                self.username,
                self.lang,
                self.family,
            )
            self._do_login()

    def client_request(
        self,
        params: dict,
        method: str = "post",
        files: Optional[Any] = None,
    ) -> dict:
        """
        Send a GET or POST request to the wiki API and return the parsed JSON.

        This is the low-level escape hatch for callers that need to hit the API
        directly without going through mwclient's higher-level helpers. CSRF
        refresh, maxlag backoff, and assertnameduserfailed recovery are all
        handled transparently by the RequestsHandler base class.

        Args:
            params: MediaWiki API parameters as a plain dict.
                    ``action`` and ``format`` are required by the API;
                    ``format`` defaults to ``"json"`` if not supplied.
            method: ``"get"`` or ``"post"``. Case-insensitive.
                    Use POST for any write operation (edits, uploads, etc.)
                    or when the payload may exceed URL length limits.
            files:  Optional dict of ``{field_name: file-like object}`` for
                    multipart uploads (e.g. ``{"file": open("image.png","rb")}``).
                    Automatically forces the method to POST when supplied.

        Returns:
            Parsed JSON response as a dict.

        Raises:
            ValueError:         If *method* is not ``"get"`` or ``"post"``.
            CSRFError:          CSRF token invalid after all retries.
            MaxlagError:        Server maxlag unresolved after all retries.
            WikiClientError:    On other API-level errors.
            requests.HTTPError: On non-2xx HTTP responses.
        """
        method = method.lower()
        if method not in ("get", "post"):
            raise ValueError(f"method must be 'get' or 'post', got {method!r}")

        # Files can only travel via multipart POST
        if files is not None:
            method = "post"

        # Always request JSON and inject write-action safety params
        params = self._enrich_params({"format": "json", **params})

        logger.debug(
            "%s %s params=%s files=%s",
            method.upper(),
            self.api_url,
            # Never log token values
            {k: ("***" if k == "token" else v) for k, v in params.items()},
            list(files.keys()) if files else None,
        )

        if method == "get":
            return self._request_with_retry(
                "GET",
                self.api_url,
                params=params,
            )
        else:
            # Always fetch a fresh CSRF token for POST — the retry loop will
            # refresh it automatically on CSRF errors.
            params["token"] = self._site.get_token("csrf")
            return self._request_with_retry(
                "POST",
                self.api_url,
                data=params,
                files=files,
            )

    def post_continue(
        self,
        params: dict,
        action: str,
        _p_: str = "pages",
        p_empty: Optional[Union[list, dict]] = None,
        Max: int = 500_000,
        first: bool = False,
        _p_2: str = "",
        _p_2_empty: Optional[Union[list, dict]] = None,
    ) -> Union[list, dict]:
        """
        Handles MediaWiki API continuation queries.
        Should mimic behavior of old Login.post_continue.

        Args:
            params:      Base API parameters.
            action:      Top-level JSON key to extract results from
                         (e.g. ``"query"``, ``"wbsearchentities"``).
            _p_:         Sub-key inside *action* (default ``"pages"``).
            p_empty:     Seed value for the accumulator (list or dict).
            Max:         Stop accumulating after this many results.
            first:       Return only the first element of the result list.
            _p_2:        Secondary sub-key when *first* is True.
            _p_2_empty:  Seed for secondary accumulator.

        Returns:
            Accumulated results as a list or dict, depending on *p_empty*.
        """
        logger.debug("post_continue start. action=%s _p_=%s", action, _p_)

        if isinstance(Max, str) and Max.isdigit():
            Max = int(Max)
        if Max == 0:
            Max = 500_000

        p_empty = p_empty if p_empty is not None else []
        _p_2_empty = _p_2_empty if _p_2_empty is not None else []

        results = p_empty
        continue_params: dict = {}
        iterations = 0

        while continue_params or iterations == 0:
            page_params = copy.deepcopy(params)
            iterations += 1

            if continue_params:
                logger.debug("Applying continue_params: %s", continue_params)
                page_params.update(continue_params)

            body = self.client_request(page_params)

            if not body:
                logger.debug("post_continue: empty response, stopping")
                break

            continue_params = {}

            if action == "wbsearchentities":
                data = body.get("search", [])
            else:
                continue_params = body.get("continue", {})
                data = body.get(action, {}).get(_p_, p_empty)

                if _p_ == "querypage":
                    data = data.get("results", [])
                elif first:
                    if isinstance(data, list) and data:
                        data = data[0]
                        if _p_2:
                            data = data.get(_p_2, _p_2_empty)

            if not data:
                logger.debug("post_continue: no data in response, stopping")
                break

            logger.debug("post_continue: +%d items (total %d)", len(data), len(results))

            if Max <= len(results) > 1:
                logger.debug("post_continue: Max=%d reached, stopping", Max)
                break

            if isinstance(results, list):
                results.extend(data)
            else:
                results = {**results, **data}

        logger.debug("post_continue: done, %d total results", len(results))
        return results

    # ── Private helpers ────────────────────────────────────────────────────

    def _ensure_logged_in(self) -> None:
        """
        Check whether the current session is authenticated.
        """
        if self._site.logged_in:
            logger.info("Session already authenticated (logged_in=%s)", self._site.logged_in)
            return
        if self._cookie_path.exists():
            try:
                self._site.site_init()
                if self._site.logged_in:
                    logger.info("Revived session via cookies as %s", self._site.username)
                    return
            except Exception as exc:
                logger.error("site_init failed: %s", exc)

        # if not self._site.logged_in: self._do_login()
        # don't login yet, user can use login() method

    def _enrich_params(self, params: dict) -> dict:
        """
        Inject write-action safety params.

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

        if self._site.logged_in:
            logger.info(
                "Logged in successfully as %s on %s.%s",
                self.username,
                self.lang,
                self.family,
            )
            self.save_cookies(self.cj)

    def __repr__(self) -> str:
        return f"WikiLoginClient(lang={self.lang!r}, family={self.family!r}, " f"username={self.username!r})"


__all__ = [
    "RequestsHandler",
    "WikiLoginClient",
]
