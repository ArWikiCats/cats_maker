# wiki_api Refactoring Plan

## Overview

The `wiki_api` module provides the low-level HTTP transport layer and high-level query functions for interacting with MediaWiki APIs (Wikipedia, Commons, Wikidata). It is consumed by all three business-logic layers (`b18_new`, `c18_new`, `mk_cats`) and `wd_bots`. Located at `src/wiki_api/`.

## Current Architecture

```
src/wiki_api/
├── __init__.py              # Public API re-exports (10 symbols)
├── api_requests.py          # submitAPI() — low-level HTTP POST to MediaWiki API
├── check_redirects.py       # NEW_API class + remove_redirect_pages() helper
├── himoBOT2.py              # get_page_info_from_wikipedia() — rich per-page fetch
├── LCN_new.py               # WikiApiHandler class + backward-compat wrappers
└── sub_cats_bot.py          # sub_cats_query() — subcategory members with langlinks
```

### Key Pain Points

1. **Bug: undefined `r22` on ReadTimeout** — `api_requests.py:60` accesses `r22.json()` but `r22` is never assigned if `Session.post()` raises `ReadTimeout` (caught on line 54, no return/raise). This will cause a `NameError` at runtime.

2. **No tests for `api_requests.py`** — The foundational transport layer has zero unit test coverage.

3. **Dead code — unused `printurl` param, `url`/`url2` variables** in `submitAPI()`. The `url` and `url2` strings are computed but never used for the actual request; only `mainurl` is passed to `Session.post()`.

4. **Dead code — `WikiApiCache` class** in `LCN_new.py:15-18`. Never instantiated anywhere; `max_size` and `ttl_seconds` parameters are stored but unused.

5. **Dead code — `numb` variable** in `himoBOT2.py:87-88` assigned twice (`0` then `1`) but only used in one debug log line.

6. **Global mutable singleton — `LC_bot = WikiApiHandler()`** in `LCN_new.py:323`. Module-level singleton makes test isolation fragile (tests must manually clear state). Also: `API_n_CALLS = {1: 0}` global counter in `sub_cats_bot.py`.

7. **`deleted_pages` reference capture** — `LCN_new.py:327` captures a list reference at import time. Works currently but fragile if `LC_bot.deleted` were ever reassigned.

8. **`_parse_api_response()` has side effects** — both parses AND writes to `self.cache`, making it hard to unit-test the parsing logic separately.

9. **No separation of concerns** — `LCN_new.py` mixes: API query construction, response parsing, caching, reverse-cache building, and backward-compat wrappers all in one file.

10. **`check_redirects.py` duplicates API logic** — `NEW_API` class has its own query construction and pagination that overlaps with `WikiApiHandler`.

11. **Stringly-typed cache keys** — Ad-hoc tuple keys with string literals (`"sub_cats_query"`, `"en_links"`, `"Cat_without_hidden"`) are fragile and not type-safe.

12. **Bare `except Exception`** — `api_requests.py:57,62` silently swallows all errors.

## Proposed Target Architecture

```
src/wiki_api/
├── __init__.py              # Public API (unchanged exports)
├── transport.py             # submitAPI() — extracted from api_requests.py, bugfixed
├── models.py                # Typed result dataclasses, enums, cache key types
├── client.py                # WikiApiClient — unified API query class (replaces WikiApiHandler + NEW_API)
├── cache.py                 # WikiApiCache — proper cache with TTL + max size (replaces inline dict)
└── _compat.py               # Backward-compat wrappers for old function signatures
```

## Refactoring Steps

### Phase 1: Fix `transport.py` (extract from `api_requests.py`)

-   Rename `api_requests.py` → `transport.py`.
-   Fix the `NameError` bug: ensure `r22` is defined or return early from exception handlers.
-   Remove dead code: `printurl` parameter, `url`/`url2` variables.
-   Keep `_load_session()` with `lru_cache`; make User-Agent configurable.
-   Add comprehensive unit tests for all branches (success, ReadTimeout, generic exception, JSON parse failure).
-   Keep `submitAPI()` signature stable: `submitAPI(params, Code, family, **kwargs)` — drop `printurl`.

### Phase 2: Extract `cache.py`

-   Create a proper `WikiApiCache` class that actually implements TTL eviction and size limits (the current one is a stub).
-   Use `@dataclass` or typed `NamedTuple` for cache keys instead of ad-hoc tuples.
-   Make it injectable rather than a global singleton.
-   Keep thread-safe using `threading.Lock` if needed.

### Phase 3: Extract `client.py` (unified WikiApiClient)

-   Merge `WikiApiHandler` (from `LCN_new.py`) and `NEW_API` (from `check_redirects.py`) into a single `WikiApiClient` class.
-   Responsibilities:
    -   Build MediaWiki API query parameters.
    -   Submit via `transport.submitAPI()`.
    -   Parse responses into typed dataclasses.
    -   Handle pagination (continue tokens).
    -   Cache results via injected `WikiApiCache`.
-   Separate pure parsing functions (no side effects) from the client logic.
-   Remove `_parse_api_response()` side effects — make it return data, not write to cache.

### Phase 4: Refactor `himoBOT2.py`

-   `get_page_info_from_wikipedia()` can remain as a standalone cached function, but:
    -   Use `WikiApiClient` internally instead of calling `submitAPI` directly.
    -   Remove dead `numb` variable.
    -   Return a typed dataclass instead of raw dict.
    -   Add unit tests for edge cases (redirect, missing page, `findtemp` parameter).

### Phase 5: Refactor `sub_cats_bot.py`

-   Replace module-level `API_n_CALLS` global with an instance counter or remove it if not consumed externally.
-   Use `WikiApiClient` and `WikiApiCache` instead of raw `submitAPI` + global `get_cache_L_C_N`.
-   Add unit tests for edge cases (`ctype="subcat"`, `ctype="page"`, empty result, API failure).

### Phase 6: `_compat.py` backward compatibility

-   Keep all 10 public API symbols exported from `__init__.py` with the same signatures.
-   Old module-level functions delegate to the new classes with deprecation warnings.
-   Once all consumers (`b18_new`, `c18_new`, `mk_cats`, `wd_bots`) are updated, remove the compat layer.

### Phase 7: Update `__init__.py` and `_compat.py`

-   Re-export from new modules.
-   No changes to public API signatures.

## Testing Strategy

| Component                     | Current Status              | Target                                                          |
| ----------------------------- | --------------------------- | --------------------------------------------------------------- |
| `transport.py` (api_requests) | 0% coverage                 | Full: success, ReadTimeout, generic exception, JSON parse error |
| `cache.py` (new)              | 0% (stub exists)            | Full: set/get, TTL expiry, max-size eviction, key types         |
| `client.py` (WikiApiClient)   | Partial (via LCN_new tests) | Full: all query types, pagination, error responses              |
| `himoBOT2.py`                 | Partial (5 tests)           | Full: redirect, missing, findtemp, all return fields            |
| `sub_cats_bot.py`             | Partial (9 tests)           | Full: ctypes, empty result, error handling                      |
| `check_redirects.py`          | Indirect only               | Full: chunking, deep-merge, redirect detection                  |

-   All tests use `pytest-mock` to mock `transport.submitAPI()`.
-   `WikiApiCache` tests are pure unit tests (no mocks needed).
-   The `NameError` bug fix must have a regression test.

## Key Constraints

-   **Public API stability**: All 10 symbols in `__init__.__all__` keep their exact signatures (`submitAPI`, `find_LCN`, `find_Page_Cat_without_hidden`, `get_arpage_inside_encat`, `set_cache_L_C_N`, `get_cache_L_C_N`, `sub_cats_query`, `get_deleted_pages`, `get_page_info_from_wikipedia`, `remove_redirect_pages`).
-   **No new external dependencies**: `requests` only.
-   **Backward-compatible deprecation**: Old import paths work with deprecation warnings for one release cycle.
-   **No behavior changes**: Same API endpoint construction, same default parameters, same caching semantics (but bugfixed).

## Migration Path

1. Create new modules (`transport.py`, `cache.py`, `client.py`, `models.py`) alongside existing code.
2. Write tests for new code.
3. Add `_compat.py` wrappers in existing files delegating to new code.
4. Update `__init__.py` to export from new modules (through compat layer).
5. Update consumers to use new API directly.
6. Remove old files after all consumers migrated.

## Bug Fix Checklist

| Bug                            | File                   | Line    | Fix                                                                    |
| ------------------------------ | ---------------------- | ------- | ---------------------------------------------------------------------- |
| `r22` undefined on ReadTimeout | `api_requests.py`      | 60      | Return `{}` in exception handler or initialize `r22 = None` before try |
| `make_sleep_def` `or` chain    | `lag_bot.py` (wd_bots) | 108-121 | Change `or` to `and` for range checks                                  |

Note: The `lag_bot.py` bug is listed here because of the shared integration — `wiki_api` provides the transport that feeds into `wd_bots`. It is owned by the `wd_bots` refactor plan.

## Future Considerations

-   Consider adding typed `APIResponse` dataclasses for all query types (langlinks, categories, templates, info).
-   Evaluate `aiohttp` for concurrent API queries (many functions query multiple pages in loops).
-   Consider exposing `WikiApiClient` as a context manager for proper session lifecycle.
-   The `findtemp` parameter in `get_page_info_from_wikipedia` could be generalized to arbitrary template filters.
