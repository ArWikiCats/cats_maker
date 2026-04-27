# new_api — Refactoring Plan

> Object-oriented MediaWiki API abstraction layer (wrapper around `wiki_api`).
> Companion plan following the same methodology as `wiki_api_refactor_plan.md`.

---

## 1. Executive Summary

`src/core/new_api` provides an object-oriented interface for interacting with MediaWiki wikis (Wikipedia, Commons, Wikidata). It wraps the low-level `wiki_api` transport with classes (`ALL_APIS`, `MainPage`, `Login`, `CategoryDepth`) and dataclasses for structured data. It is consumed by 10 files across 5 modules.

### Current Structure

```
src/core/new_api/
├── __init__.py                    # Public API: exports botEdit, load_main_api, Login
├── pagenew.py                     # Module-level singleton factory (load_main_api)
├── api_utils/
│   ├── __init__.py                # Re-exports ASK_BOT, change_codes, bot_May_Edit
│   ├── ask_bot.py                 # ASK_BOT mixin: user confirm prompts, diffs
│   └── botEdit.py                 # bot_May_Edit: {{nobots}}/{{bots}} checks, time gates
└── super/
    ├── __init__.py                # Re-exports submodules
    ├── all_apis.py                # ALL_APIS factory class
    ├── bot.py                     # LOGIN_HELPS: HTTP session, cookies, login, raw requests
    ├── super_login.py             # Login class: post_params, token mgmt, error retry
    ├── super_page.py              # MainPage class: page CRUD, categories, langlinks, etc.
    ├── catdepth_new.py            # CategoryDepth: recursive category member traversal
    ├── cookies_bot.py             # Cookie file persistence (~/cookies/)
    ├── handel_errors.py           # HANDEL_ERRORS mixin: API error code handling
    └── params_help.py             # PARAMS_HELPS base: param normalization, JSON parsing
```

### Key Pain Points

| #   | Issue                                                                                                                                                                                                          | Location                                          | Impact                                           |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------ |
| 1   | **Fragile mixin inheritance** — `MainPage` inherits `ASK_BOT` + `HANDEL_ERRORS`; `Login` inherits `LOGIN_HELPS` + `HANDEL_ERRORS`. MRO is complex and implicit.                                                | `super_page.py`, `super_login.py`                 | Hard to follow, test, and maintain               |
| 2   | **Global mutable state** — Module-level dicts (`Save_or_Ask`, `Bot_Cache`, `Created_Cache`, `users_by_lang`, `logins_count`, `ar_lag`, `urls_prints`) make tests fragile and stateful.                         | 6 files across the module                         | Tests must manually reset state; race conditions |
| 3   | **Module-level singleton** — `main_api = load_main_api()` and `MainPage = main_api.MainPage` created at import time in `pagenew.py`.                                                                           | `pagenew.py:26-28`                                | Side effects on import; hard to test             |
| 4   | **No separation of concerns** — `bot.py` mixes HTTP session, cookies, login, and parameter handling in one 390-line file.                                                                                      | `bot.py`                                          | Low cohesion; hard to reason about               |
| 5   | **Missing `__all__`** — Several files lack explicit `__all__`.                                                                                                                                                 | 7 files                                           | Implicit exports; unclear public API             |
| 6   | **Spelling errors** — `prase_params` (should be `parse_params`), `handel_errors` (should be `handle_errors`), `loged_in` (should be `logged_in`), `tempyes` (unclear), `no_gcmsort` (unclear).                 | Multiple files                                    | Confusing to new developers                      |
| 7   | **High cyclomatic complexity** — `bot_May_Edit_do`, `get_text`, `get_infos`, `save`, `Create`, `params_work`, `pages_table_work`, `subcatquery_` all score ≥C (11+) on radon.                                  | Multiple files                                    | Hard to understand and test                      |
| 8   | **Missing type hints** — Most functions lack type annotations.                                                                                                                                                 | All files                                         | Reduced IDE support, no static checking          |
| 9   | **Hardcoded namespace dicts** — `ns_list` in `catdepth_new.py:17-39` duplicates `api_sql/constants.py`.                                                                                                        | `catdepth_new.py`                                 | DRY violation; drift risk                        |
| 10  | **Long files** — `super_page.py` (759 lines), `catdepth_new.py` (437 lines), `bot.py` (390 lines), `botEdit.py` (262 lines).                                                                                   | 4 files                                           | Cognitive load; hard to navigate                 |
| 11  | **Recursive error handling** — `post_params` calls itself recursively for CSRF refresh and maxlag retry (up to 4 depth).                                                                                       | `super_login.py:144-176`                          | Stack risk; no backoff on maxlag                 |
| 12  | **Inline blocking sleep** — `time.sleep(lage + 1)` on maxlag blocks the event loop.                                                                                                                            | `super_login.py:166`                              | Blocks all operations                            |
| 13  | **`_login` cache ambiguity** — `_login(lang, family, username)` is `@lru_cache`'d in `all_apis.py`, but credentials are updated via `add_users()` after the cached object is returned. Works but is confusing. | `all_apis.py:12-16`, `43-52`                      | Unclear semantics; fragile                       |
| 14  | **`params_w` mutates input dict** — Modifies the dict in-place and returns it. Callers may not expect mutation.                                                                                                | `params_help.py:23-46`                            | Surprising side effects                          |
| 15  | **`parse_data` handles two types** — Accepts both `dict` and `requests.Response` objects.                                                                                                                      | `params_help.py:48-77`                            | Unclear interface contract                       |
| 16  | **`Meta.info["done"]` magic string** — Boolean state tracked as dict key instead of a proper attribute.                                                                                                        | `super_page.py:32`                                | Type-unsafe; fragile                             |
| 17  | **Poor test coverage** — Only 4 test methods in 1 test file (73 lines), all using mock injection.                                                                                                              | `tests/new_api/`                                  | No coverage for error paths, auth, cookies       |
| 18  | **Dead/commented code** — `ASK_BOT.__init__` empty, `HANDEL_ERRORS.__init__` empty, commented-out debug lines throughout.                                                                                      | `ask_bot.py`, `handel_errors.py`, `super_page.py` | Code noise                                       |

---

## 2. Non-Goals (Scope Guard)

-   No changes to **external public API** — `load_main_api()`, `MainPage`, `Login`, `CatDepth` keep the same signatures
-   No changes to `wiki_api` (handled by `wiki_api_refactor_plan.md`)
-   No changes to `src/config/`, `.env.example`, or CLI argument handling
-   No changes to `src/exceptions.py`
-   No changes to HTTP transport (still uses `requests`)
-   No changes to 10 downstream consumers (they must work without import changes)

---

## 3. Proposed Target Architecture

```
src/core/new_api/
├── __init__.py                  # Public API: unchanged exports
├── factory.py                   # load_main_api() — moved from pagenew.py, no module-level singleton
├── api_utils/
│   ├── __init__.py              # Re-exports (unchanged)
│   ├── ask_bot.py               # ASK_BOT mixin (cleaned: no global Save_or_Ask)
│   └── botEdit.py               # bot_May_Edit (refactored: typed, no global Bot_Cache leakage)
└── super/
    ├── __init__.py              # Re-exports (unchanged)
    ├── all_apis.py              # ALL_APIS factory (unchanged API, internally cleaner)
    ├── client.py                # WikiApiClient — merged session mgmt + params + login (was bot.py part)
    ├── auth.py                  # AuthProvider — login, tokens, cookies (extracted from bot.py)
    ├── transport.py             # HTTP transport — Session, raw_request (extracted from bot.py)
    ├── super_login.py           # Login class — thinner, delegates to AuthProvider + Transport
    ├── super_page.py            # MainPage — split into smaller methods, typed, no mixins
    ├── catdepth_new.py          # CategoryDepth — cleaned, shared namespace constants
    ├── cookies_bot.py           # Cookie persistence (unchanged)
    ├── handel_errors.py         # HandleErrors mixin (renamed, internal cleanup)
    └── params_help.py           # PARAMS_HELPS (unchanged external, internal fixes)
```

Legacy files become thin shims or are removed after consumer migration:

| Old file           | New location / shim                                 |
| ------------------ | --------------------------------------------------- |
| `pagenew.py`       | `factory.py` (shim: `from .factory import *`)       |
| `bot.py`           | Split into `transport.py` + `auth.py` + `client.py` |
| `handel_errors.py` | Renamed to `handle_errors.py` (shim kept)           |

---

## 4. Quick Wins (Execute Before Any Phase)

-   [ ] Add `__all__` to: `super_page.py`, `super_login.py`, `bot.py`, `handel_errors.py`, `params_help.py`, `cookies_bot.py`, `ask_bot.py`, `botEdit.py`
-   [ ] Remove empty `__init__` methods: `ASK_BOT.__init__` in `ask_bot.py:39-40`, `HANDEL_ERRORS.__init__` in `handel_errors.py:12-13`
-   [ ] Remove commented-out debug code throughout (e.g., `super_page.py:298-302` giant example dicts, `botEdit.py:41,63-65,91-93`)
-   [ ] Remove unused `import copy` in `super_page.py:4`
-   [ ] Remove dead `decode_bytes` in `botEdit.py` (no such function — verify with vulture)
-   [ ] Add type hints to all function signatures across the module

---

## 5. Detailed Phases

### Phase 1 — Code Hygiene & Typing

**Target:** All files in `new_api`.

**5.1.1 Add `__all__` to all submodules**

| File                     | `__all__` entries                                                                                                                 |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| `api_utils/ask_bot.py`   | `ASK_BOT`, `showDiff`, `yes_answer`, `Save_or_Ask` (note: `Save_or_Ask` should become instance-scoped later)                      |
| `api_utils/botEdit.py`   | `bot_May_Edit`, `bot_May_Edit_do`, `check_create_time`, `check_last_edit_time`, `extract_templates_and_params`, `stop_edit_temps` |
| `super/bot.py`           | `LOGIN_HELPS`, `_load_session`, `users_by_lang`, `logins_count`                                                                   |
| `super/super_login.py`   | `Login`, `ar_lag`, `urls_prints`                                                                                                  |
| `super/super_page.py`    | `MainPage`, `Content`, `Meta`, `RevisionsData`, `LinksData`, `CategoriesData`, `TemplateData`                                     |
| `super/catdepth_new.py`  | `CategoryDepth`, `subcatquery`, `title_process`, `ns_list`                                                                        |
| `super/cookies_bot.py`   | `get_cookies`, `get_file_name`, `del_cookies_file`, `from_folder`                                                                 |
| `super/handel_errors.py` | `HANDEL_ERRORS`                                                                                                                   |
| `super/params_help.py`   | `PARAMS_HELPS`                                                                                                                    |

**5.1.2 Add full type hints to all functions**

Priority targets (highest usage):

| Function            | Current signature                                                      | Target signature                                                                                                                                                |
| ------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| `load_main_api`     | `(lang, family) -> ALL_APIS`                                           | `(lang: str, family: str = "wikipedia") -> ALL_APIS`                                                                                                            |
| `ALL_APIS.__init__` | `(self, lang, family, username, password)`                             | `(self, lang: str, family: str, username: str, password: str) -> None`                                                                                          |
| `MainPage.__init__` | `(self, login_bot, title, lang, family)`                               | `(self, login_bot: Login, title: str, lang: str, family: str = "wikipedia") -> None`                                                                            |
| `Login.__init__`    | `(self, lang, family)`                                                 | `(self, lang: str, family: str = "wikipedia") -> None`                                                                                                          |
| `subcatquery`       | `(login_bot, title, sitecode, family, **kwargs)`                       | `(login_bot: Login, title: str, sitecode: str = "en", family: str = "wikipedia", **kwargs: Any) -> dict`                                                        |
| `bot_May_Edit`      | `(text, title_page, botjob, page, delay)`                              | `(text: str, title_page: str, botjob: str = "all", page: MainPage                                                                                               | None = None, delay: int = 0) -> bool` |
| `post_params`       | `(self, params, Type, addtoken, GET_CSRF, files, do_error, max_retry)` | `(self, params: dict, Type: str = "get", addtoken: bool = False, GET_CSRF: bool = True, files: Any = None, do_error: bool = False, max_retry: int = 0) -> dict` |

**5.1.3 Fix spelling errors**

| Old name        | New name               | Location                                  |
| --------------- | ---------------------- | ----------------------------------------- |
| `prase_params`  | `_parse_params`        | `catdepth_new.py:80`                      |
| `handel_err`    | `handle_err`           | `handel_errors.py:15`                     |
| `handel_errors` | `handle_errors` (file) | `super/` directory; keep shim at old path |
| `HANDEL_ERRORS` | `HandleErrors`         | `handel_errors.py:11`                     |
| `loged_in`      | `logged_in`            | `bot.py:203,272`                          |
| `no_gcmsort`    | `no_gcm_sort`          | `catdepth_new.py:59,109,129,364`          |
| `tempyes`       | `template_whitelist`   | `catdepth_new.py:62,113,136`              |
| `ta_dir`        | `cookies_dir`          | `cookies_bot.py:27`                       |

**5.1.4 Extract namespace constants to shared location**

Move `ns_list` from `catdepth_new.py:17-39` to a shared module (`src/core/new_api/constants.py` or shared `src/constants.py`). Use the same constants from `api_sql/constants.py` if possible (deduplicate with `api_sql`).

```python
# src/core/new_api/constants.py
from ..api_sql.constants import NS_TEXT_AR  # or move ns_list here and import in both places
```

**Success criteria:** `ruff check src/core/new_api` passes. `mypy src/core/new_api --ignore-missing-imports` passes. All `__all__` defined. No spelling errors.

---

### Phase 2 — Eliminate Global Mutable State

**Target:** All module-level mutable state refactored into instance-scoped or injectable patterns.

**5.2.1 `Save_or_Ask` in `ask_bot.py`**

**Problem:** `Save_or_Ask = {}` is a module-level dict shared across all `ASK_BOT` instances. When `ask_put` is called with `job="save"`, setting `Save_or_Ask["save"] = True` affects all future save operations globally.

**Solution:** Move `Save_or_Ask` to instance-level in `ASK_BOT`:

```python
class ASK_BOT:
    def __init__(self):
        self._save_or_ask: dict[str, bool] = {}
        self._yes_answer = {"y", "a", "", "Y", "A", "all", "aaa"}

    def ask_put(self, nodiff=False, newtext="", text="", message="", job="Genral", username="", summary=""):
        ...
        if settings.bot.ask and not self._save_or_ask.get(job):
            ...
            if sa == "a":
                self._save_or_ask[job] = True
```

**5.2.2 `Bot_Cache` and `Created_Cache` in `botEdit.py`**

**Problem:** Module-level caches persist across test runs and bot jobs. `Bot_Cache` is keyed by `botjob` then `title_page`. `Created_Cache` is keyed by `title_page`. These should be instance-level or injected.

**Solution:** Convert to instance-level caches with configurable TTL:

```python
class BotEditChecker:
    def __init__(self):
        self._bot_cache: dict[str, dict[str, bool]] = {}
        self._created_cache: dict[str, bool] = {}

    def bot_may_edit(self, text="", title_page="", botjob="all", page=None, delay=0) -> bool:
        ...
```

`bot_May_Edit` becomes a module-level convenience function using a default instance, or consumers instantiate their own `BotEditChecker`.

**5.2.3 `users_by_lang` and `logins_count` in `bot.py`**

**Problem:** Global dicts shared across all sessions.

**Solution:** Move to `Login` instance state. `users_by_lang` is used in `post_it` to look up `username_in` by lang — this can become a class-level dict on `Login` or be passed explicitly.

```python
class Login(LOGIN_HELPS, HANDEL_ERRORS):
    _users_by_lang: ClassVar[dict[str, str]] = {}
    _logins_count: ClassVar[int] = 0
```

**5.2.4 `ar_lag` and `urls_prints` in `super_login.py`**

**Problem:** Module-level dicts `ar_lag = {1: 3}` and `urls_prints = {"all": 0}`.

**Solution:** Move `ar_lag` to instance state on `Login` (maxlag tracking is per-session). Move `urls_prints` to a debug utility or make instance-level.

**Success criteria:** No module-level mutable state remains. All caches and counters are instance-scoped. Tests can create isolated instances without shared state.

---

### Phase 3 — Decompose `bot.py` (Structural Split)

**Target:** Split `bot.py` (390 lines) into focused modules.

**5.3.1 Extract `transport.py`**

Move HTTP session management and raw request execution from `bot.py`:

| Code                       | New location   |
| -------------------------- | -------------- |
| `_load_session()` (cached) | `transport.py` |
| `raw_request()`            | `transport.py` |
| `post_it()`                | `transport.py` |
| `post_it_parse_data()`     | `transport.py` |
| `_handle_server_error()`   | `transport.py` |
| `make_new_session()`       | `transport.py` |

**Signature:**

```python
# transport.py
@lru_cache(maxsize=1024)
def load_session(lang: str, family: str, username: str) -> requests.Session: ...

class Transport:
    def __init__(self, lang: str, family: str, username: str, *, user_agent: str = ""): ...
    def raw_request(self, params: dict, files: Any = None, timeout: int = 30) -> requests.Response | None: ...
    def post_it(self, params: dict, files: Any = None, timeout: int = 30) -> requests.Response | None: ...
    def post_it_parse_data(self, params: dict, files: Any = None, timeout: int = 30) -> dict: ...
```

**5.3.2 Extract `auth.py`**

Move cookie handling and login logic:

| Code                         | New location |
| ---------------------------- | ------------ |
| `log_in()`                   | `auth.py`    |
| `get_logintoken()`           | `auth.py`    |
| `get_login_result()`         | `auth.py`    |
| `loged_in()` → `logged_in()` | `auth.py`    |
| `make_new_r3_token()`        | `auth.py`    |
| `add_User_tables()`          | `auth.py`    |
| Cookie persistence calls     | `auth.py`    |

**5.3.3 Thin `client.py` as facade**

`client.py` exposes a unified `WikiApiClient` class that combines `Transport` + `Auth`:

```python
class WikiApiClient:
    def __init__(self, lang: str, family: str, username: str, password: str): ...
    def post_params(self, params: dict, ...) -> dict: ...  # delegates to transport + auth
    def post_it_parse_data(self, params: dict, ...) -> dict: ...
```

**Success criteria:** `bot.py` no longer exists. `transport.py`, `auth.py`, `client.py` exist. `super_login.py` imports from `client.py` instead of `bot.py`. All tests pass.

---

### Phase 4 — Refactor `super_page.py` (MainPage)

**Target:** Reduce `super_page.py` from 759 lines to under 500. Split large methods.

**5.4.1 Extract data classes to `models.py`**

Move `Content`, `Meta`, `RevisionsData`, `LinksData`, `CategoriesData`, `TemplateData` to a new `models.py` file.

**5.4.2 Replace `Meta.info["done"]` magic string**

```python
# BEFORE
self.meta.info = {"done": False}
...
if not self.meta.info["done"]:
    self.get_infos()
self.meta.info["done"] = True

# AFTER
class Meta:
    info_loaded: bool = False
...
if not self.meta.info_loaded:
    self.get_infos()
self.meta.info_loaded = True
```

**5.4.3 Split large methods**

| Method          | Lines | Strategy                                                                    |
| --------------- | ----- | --------------------------------------------------------------------------- |
| `get_text`      | 65    | Extract redirect handling, revision parsing, create_data extraction         |
| `get_infos`     | 72    | Extract category parsing, langlink parsing, template parsing, each → helper |
| `save`          | 94    | Extract param building, response handling, validation                       |
| `Create`        | 71    | Extract param building, response handling                                   |
| `post_continue` | 46    | Simplify loop logic, extract continuation handling                          |

**5.4.4 Remove mixin inheritance**

`MainPage` currently inherits from `ASK_BOT` and `HANDEL_ERRORS`. Use composition instead:

```python
# BEFORE
class MainPage(ASK_BOT, HANDEL_ERRORS):
    ...

# AFTER
class MainPage:
    def __init__(self, ...):
        self._ask_bot = ASK_BOT()
        self._error_handler = HandleErrors()

    def save(self, ...):
        if not self._ask_bot.ask_put(...): ...
        ...
        if error:
            return self._error_handler.handle_err(error, ...)
```

**Success criteria:** `MainPage` class is under 500 lines. No mixin inheritance. `Meta.info["done"]` is replaced with `Meta.info_loaded`. All tests pass.

---

### Phase 5 — Fix Error Handling & Retry Logic

**Target:** Replace recursion with iteration, add exponential backoff.

**5.5.1 Replace recursion in `post_params`**

**Current:** `post_params` calls itself recursively for:

1. Invalid CSRF token (1 level)
2. Maxlag retry (up to 4 levels)

**Solution:** Iterative retry with `while` loop:

```python
def post_params(self, params, ...):
    if not self.r3_token:
        self.r3_token = self.make_new_r3_token()

    for attempt in range(5):  # max 5 attempts
        params["token"] = self.r3_token
        params = self.filter_params(params)
        data = self.make_response(params, ...)

        if not data:
            return {}

        error = data.get("error", {})
        if not error:
            return data

        # Handle CSRF
        if error.get("info") == "Invalid CSRF token.":
            self.r3_token = None
            self.r3_token = self.make_new_r3_token()
            continue

        # Handle maxlag with backoff
        if error.get("code") == "maxlag":
            lag = int(error.get("lag", "5"))
            sleep_time = min(2 ** attempt + lag, 30)  # exponential backoff
            time.sleep(sleep_time)
            continue

        # Unknown error — return as-is
        return data

    return {}  # exhausted retries
```

**5.5.2 Add exponential backoff to maxlag**

Replace the current `time.sleep(lage + 1)` with exponential backoff capped at 30 seconds.

**5.5.3 Fix `del_cookies_file` + session cache clear in `post_it_parse_data`**

Current code clears the module-level `_load_session` cache when `assertnameduserfailed` occurs. This is fragile. Instead, create a new session for the affected user:

```python
if code == "assertnameduserfailed":
    logger.warning("assertnameduserfailed — re-authenticating")
    del_cookies_file(self.cookies_file)
    self.session = None  # Force new session on next request
    return self.post_it_parse_data(params, files, timeout)
```

**Success criteria:** No recursion in `post_params`. Exponential backoff for maxlag. Re-authentication does not clear other users' sessions.

---

### Phase 6 — Refactor `catdepth_new.py`

**Target:** Reduce complexity, clean parameter handling.

**5.6.1 Refactor `params_work` method (45 lines)**

Split into focused methods:

-   `_determine_gcmtype()` — computed `gcmtype` based on `ns`, `nslist`, `depth`
-   `_build_prop_list()` — which props to include
-   `params_work()` — orchestrates the above

**5.6.2 Refactor `pages_table_work` method (65 lines)**

Extract inner operations:

-   `_extract_timestamp_revid()` — from page data
-   `_filter_by_namespace()` — apply ns/nslist filtering
-   `_merge_templates()` — template dedup
-   `_merge_langlinks()` — langlink update
-   `_merge_categories()` — category list update

**5.6.3 Refactor `subcatquery_` method (45 lines)**

Simplify the depth loop. Use a queue pattern instead of nested loops with `tqdm`.

**5.6.4 Fix `title_process` to accept dynamic prefixes**

Replace hardcoded dict with configurable parameter or shared constant:

```python
CATEGORY_PREFIXES: dict[str, str] = {
    "ar": "تصنيف:",
    "en": "Category:",
    "www": "Category:",
}

def title_process(title: str, sitecode: str, prefixes: dict[str, str] | None = None) -> str:
    prefixes = prefixes or CATEGORY_PREFIXES
    prefix = prefixes.get(sitecode)
    if prefix and not title.startswith(prefix):
        title = prefix + title
    return title
```

**Success criteria:** `params_work` < 20 lines. `pages_table_work` < 40 lines. `subcatquery_` < 30 lines. All tests pass.

---

### Phase 7 — Fix `params_w` Mutation Bug

**Target:** `params_w` in `params_help.py` should not mutate input.

**Current:** Modifies `params` dict in-place and returns it.

**Solution:** Make a copy before mutation:

```python
def params_w(self, params: dict) -> dict:
    params = dict(params)  # shallow copy — safe for string values
    if self.family == "wikipedia" and self.lang == "ar" and params.get("summary") and self.username.find("bot") == -1:
        params["summary"] = ""
    params["bot"] = 1
    ...
    return params
```

**Success criteria:** `params_w` does not mutate caller's dict. All downstream consumers work unchanged.

---

### Phase 8 — Testing & Validation

**5.8.1 Fix existing tests**

`tests/new_api/TestMainPageNew.py` uses monkeypatching on `load_main_api` which currently returns a module-level singleton. After Phase 2 (no global singleton), tests need updating:

```python
@pytest.fixture
def api_en(monkeypatch, fake_api):
    monkeypatch.setattr("src.new_api.factory.load_main_api", lambda lang="en": fake_api)
    return fake_api
```

**5.8.2 Add missing unit tests**

| Component                   | Test cases                                                                |
| --------------------------- | ------------------------------------------------------------------------- |
| `transport.py` (new)        | Session creation, raw_request success/timeout/error, post_it, parse_data  |
| `auth.py` (new)             | Login token fetch, login result, cookie load/save, re-auth flow           |
| `MainPage.get_text`         | Page exists, page missing, redirect, redirect follow, with/without props  |
| `MainPage.get_infos`        | Empty page, full metadata, partial data, no categories, no langlinks      |
| `MainPage.save`             | Success, baserevid included, false_edit rejection, user abort, API error  |
| `MainPage.Create`           | Success, page already exists, user abort, noask=True                      |
| `MainPage.post_continue`    | Pagination loop, empty results, max limit reached, API failure            |
| `CategoryDepth.subcatquery` | Single level, depth=0, depth=N, ns filter, template filter, lang filter   |
| `CategoryDepth.params_work` | All gcmtype combos, ns/nslist combos, no_props, tempyes                   |
| `bot_May_Edit`              | No templates, {{nobots}}, {{bots allow/deny}}, stop list match, cache hit |
| `check_create_time`         | <3h old, >3h old, no timestamp, non-main-namespace                        |
| `check_last_edit_time`      | Bot editor, delay not passed, delay passed, no timestamp                  |
| `Login.post_params`         | CSRF retry, maxlag retry (0-4), maxlag exhausted, fatal error, success    |
| `Login.filter_params`       | format/json injection, bot/summary removal, formatversion default         |
| `Login.make_response`       | Success (parse), error handled, error skipped (do_error=False)            |
| `ASK_BOT.ask_put`           | Accepted, rejected, "all" (skip future), no settings.bot.ask              |
| `params_w`                  | No mutation of input, assertuser, minor, summary cleared for non-bot      |
| `parse_data`                | Valid JSON, servedby stripped, mailing list in error, invalid JSON        |

**5.8.3 Add integration test**

Test real Login → MainPage flow with mocked HTTP responses (using `responses` or `pytest-httpserver`):

```python
def test_login_get_text_flow(responses):
    # Mock login token
    responses.post("https://ar.wikipedia.org/w/api.php", json={...})
    # Mock login
    responses.post("https://ar.wikipedia.org/w/api.php", json={...})
    # Mock query
    responses.post("https://ar.wikipedia.org/w/api.php", json={...})

    api = load_main_api("ar", "wikipedia")
    page = api.MainPage("Test Page")
    text = page.get_text()
    assert text == "expected text"
```

**Success criteria:**

| Metric                         | Current | Target |
| ------------------------------ | ------- | ------ |
| Test files                     | 1       | ≥6     |
| Test methods                   | 4       | ≥40    |
| `pytest tests/new_api/`        | passes  | passes |
| Coverage (`src/core/new_api/`) | ~5%     | ≥75%   |

---

## 6. Public API Stability

| Public symbol                    | Current location           | New location                        | Changes?            |
| -------------------------------- | -------------------------- | ----------------------------------- | ------------------- |
| `new_api.load_main_api`          | `new_api/__init__.py`      | `new_api/__init__.py` (unchanged)   | None                |
| `new_api.Login`                  | `new_api/__init__.py`      | `new_api/__init__.py` (unchanged)   | None                |
| `new_api.MainPage`               | `new_api.pagenew.MainPage` | `new_api.pagenew.MainPage` (shim)   | None (module attr)  |
| `new_api.CatDepth`               | `new_api.pagenew.CatDepth` | `new_api.pagenew.CatDepth` (shim)   | None (module attr)  |
| `new_api.botEdit`                | `new_api/__init__.py`      | `new_api/__init__.py` (unchanged)   | None                |
| `pagenew.load_main_api`          | `pagenew.py`               | `factory.py` (shim at `pagenew.py`) | None                |
| `pagenew.MainPage`               | `pagenew.py:27`            | `pagenew.py` (shim)                 | Module attr removed |
| `pagenew.CatDepth`               | `pagenew.py:28`            | `pagenew.py` (shim)                 | Module attr removed |
| `super.super_page.MainPage`      | `super/super_page.py`      | Same location (cleaned)             | Internal only       |
| `super.super_login.Login`        | `super/super_login.py`     | Same location (cleaned)             | Internal only       |
| `super.catdepth_new.subcatquery` | `super/catdepth_new.py`    | Same location (cleaned)             | Internal only       |

**No consumer code changes required.** All 10 downstream consumers import from `new_api` or its submodules and will see zero API changes.

---

## 7. Migration Path

1. **Phase 1** (Hygiene): Add `__all__`, type hints, fix spelling, extract constants — non-breaking, done in-place.
2. **Phase 2** (Global state): Refactor global dicts to instance-scoped — requires updating instantiations in `super_page.py`, `super_login.py`, etc. Backward-compatible via default instances for module-level convenience functions.
3. **Phase 3** (Split bot.py): Create new `transport.py`, `auth.py`, `client.py` alongside existing `bot.py`. Add shim in `bot.py` that imports from new locations.
4. **Phase 4** (MainPage refactor): Extract models, remove mixins, split methods — done in-place on `super_page.py`, no API changes.
5. **Phase 5** (Error handling): Fix recursion → iteration. Replace `time.sleep` with exponential backoff.
6. **Phase 6** (catdepth_new): Simplify methods, share namespace constants.
7. **Phase 7** (params_w fix): Fix mutation bug — low risk, covered by type hints.
8. **Phase 8** (Testing): Update existing tests, add missing tests.

---

## 8. Acceptance Criteria

-   [ ] `ruff check src/core/new_api` passes with zero errors
-   [ ] `mypy src/core/new_api --ignore-missing-imports` passes
-   [ ] `radon cc src/core/new_api -n C` reports no functions with complexity ≥ C
-   [ ] No file in `src/core/new_api/` exceeds 500 lines (except `super_page.py` ≤500)
-   [ ] No module-level mutable state remains (globals → instance-scoped)
-   [ ] No mixin inheritance on `MainPage` (uses composition instead)
-   [ ] `post_params` uses iteration, not recursion
-   [ ] `params_w` does not mutate its input dict
-   [ ] `Meta.info["done"]` replaced with `Meta.info_loaded`
-   [ ] All old import paths work (`from new_api.pagenew import MainPage`, etc.)
-   [ ] `pytest tests/new_api/` passes with ≥ 75% coverage
-   [ ] All 10 downstream consumers work without import changes

---

## 9. Risks & Mitigations

| Risk                                                                 | Impact | Mitigation                                                               |
| -------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------ |
| Removing `MainPage` module-level singleton breaks implicit consumers | Medium | Keep shim at `pagenew.py` that creates the singleton lazily              |
| Global state refactor introduces subtle timing bugs                  | Medium | Run all downstream tests after Phase 2; parallel runs in CI              |
| Type hints reveal pre-existing type errors                           | Low    | Fix gradually; use `# type: ignore` for low-risk false positives         |
| Splitting `bot.py` breaks relative imports                           | Medium | Shim file at `bot.py` guarantees backward compat                         |
| Recursion→iteration changes maxlag retry behavior                    | Low    | Keep same max retry count (4) and total sleep budget                     |
| `params_w` copy could miss edge cases (nested dicts)                 | Low    | Current usage only passes flat dicts with string values; shallow copy OK |
| `ApiSolute` etc. (other modules) import from `new_api` internals     | Low    | Check all consumers before removing old import paths                     |

---

## 10. Execution Order & Effort

| Phase      | Steps                                                         | Estimated effort | Dependencies |
| ---------- | ------------------------------------------------------------- | ---------------- | ------------ |
| Quick Wins | `__all__`, empty init removal, dead code, comments            | 30 min           | None         |
| Phase 1    | Type hints, spelling fixes, constants extraction              | 1-2 hr           | Quick Wins   |
| Phase 2    | Global state → instance-scoped (Save_or_Ask, Bot_Cache, etc.) | 1.5 hr           | Phase 1      |
| Phase 3    | Split `bot.py` → `transport.py` + `auth.py` + `client.py`     | 1.5 hr           | Phase 2      |
| Phase 4    | Refactor `super_page.py` (models, composition, split methods) | 2 hr             | Phase 3      |
| Phase 5    | Fix error handling (recursion→iteration, backoff)             | 1 hr             | Phase 3      |
| Phase 6    | Refactor `catdepth_new.py`                                    | 1 hr             | Phase 1      |
| Phase 7    | Fix `params_w` mutation bug                                   | 15 min           | Phase 1      |
| Phase 8    | Update tests, add missing tests                               | 2-3 hr           | All phases   |

**Total estimated effort:** ~10-13 hours.

---

## 11. Downstream Consumers Verification

After refactoring, verify these consumer files still work:

| Consumer file                                | Symbols imported from `new_api`                  |
| -------------------------------------------- | ------------------------------------------------ |
| `src/mk_cats/mknew.py`                       | `load_main_api`                                  |
| `src/mk_cats/categorytext.py`                | `load_main_api`                                  |
| `src/mk_cats/create_category_page.py`        | `load_main_api`                                  |
| `src/mk_cats/add_bot.py`                     | `load_main_api`                                  |
| `src/core/c18/sql_cat.py`                | `load_main_api`                                  |
| `src/core/c18/cat_tools2.py`             | `load_main_api`                                  |
| `src/core/c18/cats_tools/ar_from_en2.py` | `load_main_api`                                  |
| `src/core/c18/bots/text_to_temp_bot.py`  | `load_main_api`                                  |
| `src/core/wiki_api/check_redirects.py`       | `load_main_api`                                  |
| `src/core/wd_bots/wd_bots_main.py`           | `password`, `username` (from `pagenew`), `Login` |

No import changes are needed. `new_api/__init__.py` and `pagenew.py` (with shim) re-export all public symbols unchanged.

---

_Plan created 2026-04-26. Follows same methodology as `wiki_api_refactor_plan.md`, `api_sql_refactor_plan.md`, and `mk_cats_refactor_plan.md`._
