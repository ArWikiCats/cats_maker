# wd_bots Refactoring Plan

## Overview

The `wd_bots` module handles all Wikidata interactions — reads (API queries) and writes (creating items, setting labels, sitelinks). It lives at `src/core/wd_bots/` and is consumed by `mk_cats`, `c18`, and other modules. The module has working test coverage for reads and error handling but has significant architectural debt.

## Current Architecture

```
src/core/wd_bots/
├── __init__.py          # Public API exports
├── wd_bots_main.py      # WD_API class (auth'd API client) + login
├── wd_api_bot.py        # Read-only Wikidata API query functions
├── to_wd.py             # Write operations (labels, sitelinks, items)
└── utils/
    ├── __init__.py       # Re-exports
    ├── lag_bot.py        # Global mutable lag state + adaptive sleep
    └── out_json.py       # API error response classification
```

### Key Pain Points

1. **Global mutable state** — `lag_bot.py` uses module-level dicts (`FFa_lag`, `newsleep`, `Find_Lag`) as singletons. Thread-unsafe and makes testing fragile.
2. **Dead code / logic bugs** — `do_lag()` has a `while GG is True` loop where both branches set `GG = False`, so it always runs exactly once regardless of actual lag.
3. **Buggy sleep logic** — `make_sleep_def()` uses `or` chains (`FFa_lag[1] <= 1 or FFa_lag[1] <= 2`) that always short-circuit on the first condition.
4. **No clear separation of concerns** — `wd_bots_main.py` mixes API transport, error handling, and lag checking. `to_wd.py` mixes parameter construction with business logic.
5. **No unit tests for `to_wd.py`** — The write layer is completely untested.
6. **No tests for `out_json.py`** — Error response parser has zero coverage.
7. **Stringly-typed error returns** — Functions return `"warn"`, `"reagain"`, `True`, `False`, `""` with no consistent result type.
8. **Dual error classification** — `WD_API.handle_err_wd` and `out_json.outbot_json_bot` have overlapping error-code logic.
9. **Magic numbers everywhere** — Retry counts, lag thresholds, sleep intervals are hard-coded.
10. **`filter_data()` has side effects** — Modifies `data` in-place AND calls `do_lag()` (which may sleep).

## Proposed Target Architecture

```
src/core/wd_bots/
├── __init__.py           # Public API exports (unchanged)
├── client.py             # Low-level authenticated API client (HTTP transport + retry)
├── queries.py            # Read-only query functions (moved from wd_api_bot.py)
├── operations.py         # Write operations (moved from to_wd.py, refactored)
├── errors.py             # Unified error classification (merged from handle_err_wd + out_json)
├── lag.py                # Lag manager class (replaces global state in lag_bot.py)
└── models.py             # Request/response models, enums, typed result types
```

## Refactoring Steps

### Phase 1: Extract Lag Manager (`lag.py`)

-   Replace module-level mutable dicts (`FFa_lag`, `newsleep`, `Find_Lag`) with a `LagManager` class.
-   Add proper state encapsulation with typed attributes.
-   Fix the `do_lag()` dead-code bug (the `while` loop that always exits).
-   Fix the `make_sleep_def()` `or`/`and` logic bug.
-   Extract magic numbers (`120` sec recheck, `5` sec threshold, `4` sleep tiers) into named constants or config parameters.
-   Make `LagManager` injectable into `WD_API` / `APIClient`.
-   Keep backward-compatible module-level wrapper functions (deprecated) that delegate to a module-level singleton.

### Phase 2: Unified Error Classification (`errors.py`)

-   Merge `WD_API.handle_err_wd()` (API-level error codes) and `out_json.outbot_json_bot()` (JSON response error codes) into a single `ErrorClassifier`.
-   Use an `Enum` for error types instead of stringly-typed returns: `ErrorType.ABUSE_FILTER`, `ErrorType.ARTICLE_EXISTS`, `ErrorType.MAXLAG`, `ErrorType.WARN`, `ErrorType.RETRY`, etc.
-   Return a structured `APIError` dataclass instead of a bare string or bool.
-   Deprecate `out_json.py` module.

### Phase 3: Extract API Client (`client.py`)

-   Extract the auth, transport, and retry logic from `WD_API` into a focused `APIClient` class.
-   `WD_API` becomes a thin composition wrapper or is replaced entirely.
-   Separate concerns:
    -   `APIClient` — handles HTTP transport, CSRF tokens, maxlag retries (up to 4x).
    -   Error handling delegates to `ErrorClassifier`.
    -   Lag checking delegates to `LagManager`.
-   No more in-place mutation of params dict.

### Phase 4: Refactor Queries (`queries.py`)

-   Rename from `wd_api_bot.py` to `queries.py`.
-   Move to using `APIClient` instead of raw `submitAPI`.
-   Preserve existing caching (`lru_cache`) but make cache sizes configurable.
-   Add typed return models instead of raw dicts where practical.
-   Keep existing function signatures as deprecated wrappers.

### Phase 5: Refactor Operations (`operations.py`)

-   Rename from `to_wd.py` to `operations.py`.
-   Write comprehensive unit tests (the write layer is currently 0% covered).
-   Separate parameter construction from execution.
-   Use the new `ErrorClassifier` return types instead of ad-hoc string checks.
-   Replace `bad_lag(nowait)` checks with a consistent pre-flight pattern.

### Phase 6: Update `__init__.py`

-   Keep public API stable (same exports).
-   Add deprecated import path warnings for renamed modules.

## Testing Strategy

| Component       | Current Coverage                                     | Target                             |
| --------------- | ---------------------------------------------------- | ---------------------------------- |
| `lag.py`        | Partial (test_lag_bot.py)                            | Full coverage including edge cases |
| `errors.py`     | Partial (test_handle_wd_errors.py) + 0% for out_json | Full coverage                      |
| `client.py`     | Partial (test_wd_newapi_bot.py)                      | Full coverage                      |
| `queries.py`    | Good (test_wd_api_bot.py)                            | Same, adapt to new client          |
| `operations.py` | 0%                                                   | Full coverage                      |

-   All tests use `pytest-mock` to mock HTTP — no real API calls.
-   `LagManager` tests mock `post_request_for_lag` and verify state transitions without real requests.
-   `ErrorClassifier` tests are pure unit tests (no mocks needed).

## Key Constraints

-   **Public API stability**: All functions exported from `__init__.py` must keep the same signatures.
-   **No new external dependencies**: Use only `requests` (already used) and stdlib.
-   **Backward-compatible deprecation**: Old module paths should work with deprecation warnings for at least one release cycle.
-   **No behavior changes**: The refactor should not change how the module interacts with Wikidata — same retry counts, same error handling outcomes, same lag behavior (just bug-fixed).

## Migration Path

1. Implement new classes (`LagManager`, `ErrorClassifier`, `APIClient`) alongside existing code.
2. Write tests for new code.
3. Make old modules delegate to new classes (with deprecation warnings).
4. Once all consumers are migrated, remove old modules.

## Future Considerations

-   Consider adding a `WikidataSession` context manager for batch operations.
-   Evaluate moving to `wikibase-rest-api` (REST endpoint) as an alternative transport layer.
-   Consider adding rate-limit awareness beyond what maxlag provides.
