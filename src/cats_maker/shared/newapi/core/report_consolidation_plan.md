# Error-module consolidation plan (`src/arwikibot/shared/newapi/core/`)

> **Scope:** the four modules that were gathered into `src/arwikibot/shared/newapi/core/` for
> side-by-side comparison:
> `result_error.py`, `out_json.py`, `handel_errors.py`, `exceptions.py`.
>
> **Audience:** developers working on `newapi` (the pywikibot wrapper used by the
> arwiki / Wikidata bots).
>
> **Goal:** decide which module is the single source of truth, produce a plan to
> retire `out_json.py`, and isolate Wikidata/Wikibase errors from MediaWiki errors.

---

## 1. TL;DR

| Question                                                 | Answer                                                                                                                                                                                                                                                          |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Use `exceptions.py` or `handel_errors.py`?               | **`exceptions.py`.** `handel_errors.py` is dead, legacy code that duplicates `exceptions.py::parse_api_error` and should be deleted.                                                                                                                            |
| Where should `out_json.py` go?                           | Its Wikibase logic moves into a **new, dedicated `core/wikibase_errors.py`** (subclassing the `ApiError` hierarchy from `exceptions.py`). The `output_json` / `"reagain"` string sentinel is replaced by a proper retryable `ApiResult`.                        |
| Can we separate Wikidata/Wikibase errors from MediaWiki? | **Yes, and we should.** `WikibaseError(ApiError)` lives in `wikibase_errors.py`; MediaWiki business/transport errors stay in `exceptions.py`. A single dispatcher `parse_api_error` keeps a registry and routes by code (and, for ambiguous codes, by backend). |
| Keep `result_error.py`?                                  | **Yes.** It is the _value_ side (`ApiResultError`) of the same pattern and is not in competition with the two `parse_api_error` modules.                                                                                                                        |

---

## 2. Inventory

| File               | Public symbols                                                                                                          | What it is                                                                                                                                          | Used in production?                                                 | Status                                          |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | ----------------------------------------------- |
| `result_error.py`  | `ApiResultError` (dataclass), `ApiResultExceptionError`                                                                 | **Value object** for a failed `ApiResult`. Never raised on its own.                                                                                 | Yes — `core/result.py`, `super_page.py`                             | **KEEP**                                        |
| `exceptions.py`    | `NewApiExceptionError`, `ApiError` (+ subclasses), `WikiClientError` (+ subclasses), `parse_api_error`, `to_api_result` | **Unified exception hierarchy + parsers.** The documented single source of truth.                                                                   | Yes — public `shared.newapi` API, `client_wiki/pages/super_page.py` | **KEEP & PROMOTE**                              |
| `handel_errors.py` | `HandleErrors.parse_api_error`                                                                                          | **Legacy** class that maps an error dict to `ApiResult.fail` directly (never builds an `ApiError`). Duplicates the branch logic of `exceptions.py`. | **No** — only referenced by its own unit test                       | **DELETE**                                      |
| `out_json.py`      | `parse_api_error_legacy`                                                                                                | **Legacy Wikibase-specific** parser. Returns `str\| bool`, calls `time.sleep(5)`, emits string sentinels (`"reagain"`, `"warn"`, `False`).          | Yes — `wd_clients/.../req_bots_new/handle_response.py`              | **MIGRATE → `wikibase_errors.py`, then DELETE** |

### Production consumers that matter for the migration

-   `out_json.parse_api_error_legacy` → `handle_response.py::ResponseHandler.handle_response`
    (the base class of `WdDescriptions`, `WdSitelinks`, `WdItems`, `WdLabels`, `WdClaims`).
-   The string sentinel is threaded through `ApiResult.data["output_json"]` and read by:
    -   `descriptions_wd.py:62` and `descriptions_wd.py:141` → recursive retry when `== "reagain"`.
    -   `core1/wd_link/wd_deps/wikidata_manager.py:59` → `result_data.get("output_json", "")`.
-   `conftest.py:30` stubs `shared.newapi.core.out_json` (`time.sleep`) for tests.
-   Tests referencing it: `test_out_json.py`, `test_handle_response.py`,
    `test_descriptions_wd.py`, `test_wikidata_manager_edge.py`.

---

## 3. Detailed comparison

### 3.1 `exceptions.py` vs `handel_errors.py` — two parallel `parse_api_error`

Both map an API error dict to a result, and both branch on the _same_ MediaWiki
codes (`abusefilter-disallowed`, `maxlag`, `articleexists`, `no-such-entity`,
`protectedpage`). The differences are decisive:

| Aspect                                  | `exceptions.py::parse_api_error`                                                                                             | `handel_errors.HandleErrors.parse_api_error`                      |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Return type                             | `ApiError` **subclass** (rich: `code`, `message`, `info`, `is_retryable`, `raw_error`)                                       | `ApiResult.fail(...)` only — no `ApiError` is ever constructed    |
| Subclassing / typed errors              | Yes: `AbuseFilterError`, `MaxLagError`, `ArticleExistsError`, `NoSuchEntityError`, `ProtectedPageError`, `InvalidTokenError` | None                                                              |
| `ABUSEFILTER_ERRORS_FOR_DELAY` constant | Defined once                                                                                                                 | **Duplicated** (copy-paste)                                       |
| Wired into public API?                  | Yes (`shared/newapi/__init__.py` re-exports `parse_api_error`)                                                               | No                                                                |
| Side effects                            | None (pure)                                                                                                                  | None, but returns `ApiResult` directly, bypassing the value layer |
| Tests / real usage                      | `super_page.py` save/create, public API                                                                                      | Its own test only                                                 |

`handel_errors.py` is a **strict subset, done worse**: it reproduces the same
branch ladder but throws away the rich `ApiError` typing and duplicates the
abuse-filter delay list. There is no behaviour in `handel_errors.py` that is not
already covered (and improved upon) by `exceptions.py`.

### 3.2 `result_error.py` — the value half of the pattern

`ApiResultError` is _not_ in competition with the `parse_api_error` modules.
It is the normalized error **payload** carried inside `ApiResult` (and serialized
by `to_dict()`). The companion `ApiResultExceptionError` is raised only by
`ApiResult.unwrap()`. This is the correct, intentional design documented in the
existing `report_apierror_vs_apiresult_error.md`:

```
API error dict
   │  exceptions.parse_api_error()
   ▼
ApiError  (raised exception, rich fields)
   │  ApiResult.fail(code=…, error=…)  /  to_api_result()
   ▼
ApiResultError  (value object, serialized)  ──► ApiResult.error
   │  unwrap() on failure
   ▼
ApiResultExceptionError  (wraps ApiResultError)
```

So `result_error.py` stays. The only outstanding improvement (already noted in
the prior report, **already fixed in `super_page.py` lines 598-599 / 673-674**)
is to always pass `code=error.code`, not rely on `from_anything`'s
`isinstance(error, Exception)` branch.

### 3.3 `out_json.py` — the Wikibase legacy parser

`parse_api_error_legacy` is the only module that understands **Wikibase-specific**
codes, but it does so in a way that breaks the unified model:

-   **Return type is `str | bool`**, not an `ApiError`/`ApiResultError`.
-   It **emits string sentinels** (`"reagain"`, `"warn"`, the raw code, or `False`)
    that callers have to string-match.
-   It has a **side effect** (`time.sleep(5)`) for the `failed-save` rate-limit case
    — parsing should never sleep (see §5.3 for moving it out).
-   **Interim fix applied:** the fragile language-dependent text searches have been
    removed (see §3.4). The rate-limit is now detected via the stable
    `actionthrottledtext` _message name_, and `no-such-entity-link` via its
    _error code_ — no longer by matching the Arabic or English `info`/`html` text.
    The hard-coded `err_wait` Arabic string and the `item_not_found_error` English
    string are gone from the source.
-   The Wikibase codes it handles: `origin-not-empty`, `missingparam` (→ `"warn"`),
    `modification-failed` / `failed-modify`, `wikibase-validator-label-equals-description`,
    `wikibase-validator-label-with-description-conflict` (→ `"same description"`),
    `unresolved-redirect`, `failed-save` (+`actionthrottledtext`→`"reagain"`),
    `no-external-page`, `wikibase-api-invalid-json`, `no-such-entity-link`.

These are conceptually distinct from MediaWiki codes and belong in their own home,
not in a file named after a transport detail (`out_json`).

### 3.4 Interim fixes already applied (text → code-based detection)

Before the full migration in §8, the fragile language-dependent text searches
were replaced with stable `code` / `messages[].name` checks. These changes are
already committed and covered by updated tests:

-   **`out_json.py`** — `parse_api_error_legacy`:
    -   `failed-save` rate-limit is now detected via `messages_data.get("actionthrottledtext")`
        instead of the hard-coded Arabic `err_wait` string; the `time.sleep(5)` side
        effect stays (to be moved out in Phase C).
    -   `no-such-entity-link` is detected by its `error.code` instead of matching the
        English `info` text `"Could not find an Item ..."`.
    -   `wikibase-api-invalid-json` is detected via `messages_data` (message name),
        not a substring search of the serialized response.
    -   The `err_wait` and `item_not_found_error` constants were removed.
-   **`core1/wd_link/wd_deps/wikidata_manager.py`** — the `no-such-entity-link`
    fallback now compares `output_json == "no-such-entity-link"` (the code) instead
    of the English text.
-   **`shared/wd_clients/wd_api/wd_desc.py`** — the rate-limit and invalid-JSON
    checks now read message names from the raw response (`r4["error"]["messages"]`)
    via `_messages_data`, instead of searching the Arabic text in `r4_text`; the
    previously dead `_messages_data` (built from the always-empty envelope `error`
    key) is now sourced correctly.
-   **Tests** — `test_out_json.py`, `test_handle_response.py`,
    `test_descriptions_wd.py` (the `REAGAIN_RESP` fixture now carries the
    `actionthrottledtext` message) and `test_wikidata_manager_edge.py` were updated
    to assert code-based behaviour; all 29 related tests pass.

This makes the current code robust to language/wording changes while keeping the
`out_json.py` → `wikibase_errors.py` migration (§8) intact.

---

## 4. Decision 1 — `exceptions.py` vs `handel_errors.py`

**Adopt `exceptions.py` as the single source of truth for error parsing.**
`handel_errors.py` is redundant and partially incorrect (it never builds a typed
`ApiError`). Retire it:

1. Delete `src/arwikibot/shared/newapi/core/handel_errors.py`.
2. Delete `tests/unit/shared/newapi/core/test_handel_errors.py`.
3. Delete the now-duplicate `ABUSEFILTER_ERRORS_FOR_DELAY` that lived in
   `handel_errors.py` (the canonical one already lives in `exceptions.py`).
4. Confirm nothing imports `HandleErrors` (grep shows only its own test).

No production behaviour changes — `exceptions.parse_api_error` already covers
every branch `handel_errors` had.

---

## 5. Decision 2 — retire `out_json.py`

The goal is to move Wikibase error parsing into the unified `ApiError` model and
**eliminate the `output_json` string sentinel**.

### 5.1 Target: a dedicated `core/wikibase_errors.py`

Create `src/arwikibot/shared/newapi/core/wikibase_errors.py`. **Every field referenced in
§5.2 is declared here** (this resolves the truncated-snippet concern), and the
`WIKIBASE_CODES` set enumerates the non-`wikibase-` prefixed codes too (see §6.1):

```python
from .exceptions import ApiError

# Every Wikibase code, INCLUDING the ones that do NOT start with "wikibase-"
# (audited against §3.3; see the caveat about `missingparam` in §6.1).
WIKIBASE_CODES = {
    "origin-not-empty",
    "missingparam",            # Wikibase *context* only — see §6.1 caveat
    "modification-failed",
    "failed-modify",
    "failed-save",
    "unresolved-redirect",
    "no-external-page",
    "no-such-entity-link",
    "wikibase-api-invalid-json",
}

class WikibaseError(ApiError):
    """Base for Wikibase/Wikidata API business errors (separate from MediaWiki).

    Adds two fields on top of ApiError:
      * severity: "error" (default) or "warning" — maps the legacy "warn" sentinel.
      * reason:   free-form sub-reason (used by ModificationFailedError).
    Structured parameters from the API (e.g. the label/description conflict
    triple lab/code/q) are preserved in ``raw_error`` (inherited from ApiError),
    never in a separate field — so nothing is lost on conversion.
    """

    def __init__(
        self,
        code: str,
        message: str,
        info: str = "",
        is_retryable: bool = False,
        raw_error: dict | None = None,
        severity: str = "error",
        reason: str = "",
    ) -> None:
        self.severity = severity
        self.reason = reason
        super().__init__(
            code, message, info=info, is_retryable=is_retryable, raw_error=raw_error
        )

class OriginNotEmptyError(WikibaseError):       # origin-not-empty
class ModificationFailedError(WikibaseError):    # reason: failed-modify | label-equals-description | label-description-conflict
class UnresolvedRedirectError(WikibaseError):    # unresolved-redirect
class FailedSaveError(WikibaseError):            # failed-save  (is_retryable=True on rate-limit)
class NoExternalPageError(WikibaseError):        # no-external-page
class InvalidJsonError(WikibaseError):           # wikibase-api-invalid-json
class NoSuchEntityLinkError(WikibaseError):      # no-such-entity-link

def parse_wikibase_error(error_dict: dict[str, Any]) -> WikibaseError: ...
```

All subclasses inherit `code`, `message`, `info`, `is_retryable`, `raw_error`,
plus the new `severity` / `reason`, so they plug straight into
`ApiResult.fail(code=…, error=…)` and `to_api_result` with **no** string sentinel.

> **Nested codes — read `messages[].name`, not `info`/`html`.** A single API
> error can carry _two_ overlapping codes: the top-level `error.code`
> (`failed-save`) **and** a sub-code inside `error.messages[].name`
> (`actionthrottledtext`). The retryable ("reagain") case is specifically
> `failed-save` **+** `actionthrottledtext` in `messages`; a bare `failed-save`
> is a hard failure. So `FailedSaveError.is_retryable` must be derived from
> `messages[].name == "actionthrottledtext"`, never from `code == "failed-save"`
> alone. Likewise `no-such-entity-link` is identified by its **code**, and
> `wikibase-api-invalid-json` by a **message name** — both stable, language
> independent. The `html` field is for display only and must never drive logic.

### 5.2 Map the legacy return values to the new model

| Legacy `parse_api_error_legacy` return                                      | New representation                                                                                                                                                                       |
| --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `"origin-not-empty"`                                                        | `OriginNotEmptyError(code="origin-not-empty")`                                                                                                                                           |
| `"warn"` (missingparam / generic modification-failed)                       | `WikibaseError(code=…, is_retryable=False, severity="warning")`; caller logs and continues                                                                                               |
| `"wikibase-api-failed-modify"`                                              | `ModificationFailedError(reason="failed-modify")`                                                                                                                                        |
| `"wikibase-validator-label-equals-description"`                             | `ModificationFailedError(reason="label-equals-description")`                                                                                                                             |
| `"same description"`                                                        | `ModificationFailedError(reason="label-description-conflict", raw_error=err)` — `lab/code/q` are read from `raw_error["messages"][0]["parameters"]` (no separate `details` field needed) |
| `"unresolved-redirect"`                                                     | `UnresolvedRedirectError`                                                                                                                                                                |
| `"reagain"` (failed-save **+** `actionthrottledtext` in `messages`)         | `FailedSaveError(is_retryable=True)` — retryable iff the `actionthrottledtext` **message name** is present; **no `sleep` here**                                                          |
| `False` (no-external-page, or failed-save _without_ `actionthrottledtext`)  | `NoExternalPageError` / `FailedSaveError(is_retryable=False)`                                                                                                                            |
| `"wikibase-api-invalid-json"` (matched via `messages[].name`)               | `InvalidJsonError`                                                                                                                                                                       |
| `no-such-entity-link` (matched via `code`, **not** the English `info` text) | `NoSuchEntityLinkError`                                                                                                                                                                  |
| unknown code                                                                | generic `WikibaseError(code=raw_code)`                                                                                                                                                   |

### 5.3 Move the side effect out of the parser

The `time.sleep(5)` for the Arabic rate-limit message (`err_wait`) must **not**
live in a parser. Extract it into:

-   a `WikibaseRetryPolicy` (or reuse the existing `shared.wd_clients.utils.lag_bot`
    rate-limit helper), which the **caller** consults when `error.is_retryable` is
    `True`; **or**
-   the `requests_handler`/`api_client` retry layer, which already centralizes
    MediaWiki maxlag/retry waits.

> **Hard rule — never match on `info`/`html` text.** Any existing text search in
> `info` or `html` (in _any_ language) must be replaced by checking `code` or
> `messages[].name`, because the text is subject to change by language and
> wording, while the code / message name is the stable API contract. The
> `html` field is display-only and must never drive logic. This is exactly what
> the `out_json.py` fixes did: the rate-limit is now detected via the
> `actionthrottledtext` message name, and `no-such-entity-link` via its `code`.

### 5.4 Update the consumers

-   `handle_response.py::handle_response`: replace
    `error_result = parse_api_error_legacy(err)` +
    `ApiResult.fail(error=error_result, data={"r4": r4, "output_json": error_result})`
    with `ApiResult.fail(code=err.code, error=parse_wikibase_error(err))` and keep
    the raw `r4` in `data` (no more `output_json` sentinel).
-   `descriptions_wd.py:62` & `:141`: replace
    `(result.data or {}).get("output_json") == "reagain"` with
    `result.error and getattr(result.error, "is_retryable", False)` (or a typed
    `FailedSaveError` check). Keep the recursive `des_api(..., rea=False)` retry.
-   `core1/wd_link/wd_deps/wikidata_manager.py:59`: read the error from
    `result.error.code` / `result.error.message` instead of `output_json`.

### 5.5 Tests & stubs

-   Rewrite `tests/unit/shared/newapi/core/test_out_json.py` →
    `test_wikibase_errors.py`: assert `ApiResult.fail(...)` carries the correct
    `error.code` / `error.message` / `error.is_retryable` for each code, and add a
    separate test for the retry policy (`sleep` path) that no longer lives in the
    parser.
-   Update `test_handle_response.py`, `test_descriptions_wd.py`,
    `test_wikidata_manager_edge.py` to the new `ApiResult.error` contract.
-   **Add an integration test** `test_parse_api_error_routes_both_families` that
    feeds a Wikibase error dict (e.g. `modification-failed`) **and** a MediaWiki
    error dict (e.g. `articleexists`) through the **unified** `parse_api_error` in
    a single run, and asserts each resolves to the correct subclass
    (`ModificationFailedError` vs `ArticleExistsError`) and that `to_api_result`
    yields the expected `ApiResult`. Per-unit tests alone would not catch a
    misrouted code at the dispatcher level.
-   Remove the `shared.newapi.core.out_json` entry from `conftest.py:30`
    (and add `shared.newapi.core.wikibase_errors` if its `time.sleep` is stubbed).
-   Delete `out_json.py`.

---

## 6. Decision 3 — separating Wikidata/Wikibase from MediaWiki

Yes — and `wikibase_errors.py` above is the mechanism. Concretely:

-   **MediaWiki errors** (`ApiError` subclasses for `articleexists`, `maxlag`,
    `protectedpage`, `abusefilter-disallowed`, `badtoken`, …) and **transport**
    errors (`WikiClientError` tree) remain in `exceptions.py`.
-   **Wikibase errors** get their own `WikibaseError(ApiError)` base + subclasses in
    `wikibase_errors.py`. Because they subclass `ApiError`, they automatically work
    with `ApiResult.fail`, `to_api_result`, `unwrap`, and any retry logic — but their
    codes/reasons are isolated, so Wikibase-specific semantics (sitelink conflicts,
    label/description conflicts, redirects) never pollute the MediaWiki parser.
-   **One dispatcher** keeps the two worlds tidy. Add to `exceptions.py`:

    ```python
    from .wikibase_errors import parse_wikibase_error, WikibaseError

    _WIKIBASE_PREFIX = "wikibase"  # codes like wikibase-api-*, wikibase-validator-*


    def parse_api_error(error_dict: dict[str, Any], backend: str = "mediawiki") -> ApiError:
        code = error_dict.get("code", "")
        # Route by explicit code set, by prefix, or (for ambiguous generic codes)
        # by the backend that produced the error.
        if code in WIKIBASE_CODES or code.startswith(_WIKIBASE_PREFIX) or backend == "wikibase":
            return parse_wikibase_error(error_dict)
        # ... existing MediaWiki branch ladder ...
    ```

    This makes the public `shared.newapi.parse_api_error` the single entry point
    while keeping the two error families in separate modules — exactly the
    "separate but unified" outcome requested.

    **Critical routing rule:** `WIKIBASE_CODES` must enumerate **every** Wikibase
    code from §3.3 that does _not_ start with `"wikibase"`, otherwise it would be
    silently misrouted to the MediaWiki branch ladder. The complete non-prefixed
    set is: `origin-not-empty`, `missingparam`, `modification-failed`,
    `failed-modify`, `failed-save`, `unresolved-redirect`, `no-external-page`,
    `no-such-entity-link` (the substring-detected cases `wikibase-api-invalid-json`
    and `no-such-entity-link` are also caught via message text in the parser).

    ### 6.1 `missingparam` is NOT Wikibase-exclusive

    `missingparam` is a **generic MediaWiki** error code, not a Wikibase one. In the
    legacy `out_json.py` it was treated as a non-fatal `"warn"` _only_ because that
    code path was reached from the Wikibase client. Routing by code alone would
    wrongly send every MediaWiki `missingparam` to `parse_wikibase_error`.

    **Resolution — make the dispatcher backend-aware, not code-alone:** when the
    failing call originated from a Wikibase action (`wb*` actions / the
    `wd_clients` request path), route generic codes like `missingparam` through
    `parse_wikibase_error`; otherwise they stay in the MediaWiki ladder. Practical
    options:

    -   pass a `backend: "wikibase" | "mediawiki"` hint into `parse_api_error` from
        the caller (the wikidata client already knows it talks to Wikidata), **or**
    -   keep `missingparam` in the MediaWiki ladder and downgrade its severity to a
        warning only at the wikidata-client call site (not in the parser).

    **Manual audit before locking the classification:** run `grep -rn` over `src/`
    for each Wikibase code — especially the non-`wikibase-` ones — to confirm where
    it is actually emitted, and only then finalize `WIKIBASE_CODES`.

---

## 7. Target layout

```
src/arwikibot/shared/newapi/core/
├── exceptions.py        # MediaWiki ApiError tree + WikiClientError tree
│                        # + parse_api_error() dispatcher (routes Wikibase→wikibase_errors)
├── wikibase_errors.py   # NEW: WikibaseError(ApiError) + subclasses + parse_wikibase_error()
├── result_error.py      # KEEP: ApiResultError value object + ApiResultExceptionError
├── result.py            # KEEP: ApiResult envelope (uses result_error + exceptions)
├── handel_errors.py     # DELETED
└── out_json.py          # DELETED (logic moved to wikibase_errors.py)
```

---

## 8. Phased migration (low-risk)

Each phase is independently revertible. **Explicit acceptance criteria** per phase
(replacing the vague "tests green" gate):

1. **Phase A — delete dead code.** Remove `handel_errors.py` + its test.
   _Acceptance:_ `ruff check src/`, `pytest -m "not network and not slow"`, and
   `python scripts/check_imports.py` all pass; `grep -rn HandleErrors src/` is empty.
2. **Phase B — add `wikibase_errors.py`.** Introduce the `WikibaseError` hierarchy
   (with `severity` / `reason`), `WIKIBASE_CODES`, and `parse_wikibase_error`, plus
   the dispatcher hook in `exceptions.parse_api_error`. Legacy `out_json` still used.
   _Acceptance:_ unit tests pass for **every** Wikibase code in §3.3; the MediaWiki
   ladder is unchanged and its tests still pass (routing limited to the
   `wikibase*` prefix only, so no behaviour shift yet).
3. **Phase C — extract retry wait.** Move the `failed-save` rate-limit detection
    - `time.sleep` into a `WikibaseRetryPolicy` / reuse `lag_bot`.
      _Acceptance:_ `parse_wikibase_error` has **zero** side effects —
      `grep -n time.sleep src/arwikibot/shared/newapi/core/wikibase_errors.py` is empty; the
      retry policy owns the wait.
4. **Phase D — switch `handle_response.py`** to `parse_wikibase_error` +
   `ApiResult.fail(code=…, error=…)`; drop `output_json`.
   _Acceptance — behavioural-parity gate (do this **before** deleting `out_json`):_
   for the `failed-save` rate-limit payload, assert the new `ApiResult` carries
   `error.is_retryable == True` **and** that the caller still performs the exact
   same retry (`des_api(..., rea=False)`) that the old `"reagain"` sentinel did.
   Capture old `output_json` vs new `error` values for representative payloads and
   diff them; only proceed once parity is proven. (See also §9.)
5. **Phase E — update callers** (`descriptions_wd.py` ×2, `wikidata_manager.py`)
   to read `result.error` instead of `output_json`.
   _Acceptance:_ `grep -rn output_json src/` is empty; the recursive retry in
   `descriptions_wd` still triggers on a retryable error.
6. **Phase F — tests & cleanup.** Rewrite `test_out_json.py` → `test_wikibase_errors.py`,
   fix `test_handle_response.py` / `test_descriptions_wd.py` /
   `test_wikidata_manager_edge.py`, add the routing integration test (§5.5), drop
   the `conftest` `out_json` stub, delete `out_json.py`.
   _Acceptance:_ all tests green; `conftest.py` no longer references `out_json`.

Each phase is independently revertible and keeps the test suite green.

---

## 9. Risks & verification

-   **Behavioural parity for `"reagain"`:** the recursive retry in `descriptions_wd`
    must still trigger. Verify with `test_descriptions_wd.py` after Phase E by
    asserting retry happens when `error.is_retryable` is `True`. The Phase D
    parity gate (§8) must be signed off before `out_json` is deleted.
-   **`output_json` lookups:** grep for `output_json` after Phase F must return
    nothing in `src/`.
-   **Misrouted codes:** the §5.5 integration test guards the dispatcher; the §6.1
    manual `grep` audit confirms `WIKIBASE_CODES` is complete (no `wikibase-`-less
    Wikibase code left to fall through to MediaWiki).
-   **Forbidden `src.` imports:** `scripts/check_imports.py` must stay clean
    (use `shared.newapi.core.wikibase_errors`, never `src.…`).
-   **Run before/after:** `ruff check src/ && ruff format src/ && pytest -m "not network and not slow" && python scripts/check_imports.py`.

---

## 10. Summary of decisions

1. **`exceptions.py` wins** over `handel_errors.py`; delete `handel_errors.py`.
2. **Retire `out_json.py`** by moving its Wikibase logic into the new
   `wikibase_errors.py` and replacing the `output_json` sentinel with a real
   retryable `ApiResult`.
3. **Separate Wikibase from MediaWiki** via `WikibaseError(ApiError)` in its own
   module, behind the single `parse_api_error` dispatcher (code-set + backend hint).
4. **`result_error.py` stays** as the value half of the pattern.
