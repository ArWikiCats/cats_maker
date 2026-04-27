# api_sql — Refactoring Plan

> Database access layer for Wikimedia Tool Labs MySQL replicas (pymysql-based).
> Companion plan following same methodology as `mk_cats_refactor_plan.md`.
>
> **Status:** Quick Wins done; Phases 1, 2, 4, 5 done. Phase 3 (file rename shims) pending.

---

## 1. Executive Summary

`src/core/api_sql` provides SQL-based access to Wikimedia Analytics DB replicas to fetch Wikipedia page data (category members, cross-language differences). It has three layers:

| Layer | File         | Lines | Responsibility                                                            |
| ----- | ------------ | ----- | ------------------------------------------------------------------------- |
| Low   | `db_pool.py` | 158   | pymysql connection, query execution, byte decoding                        |
| Mid   | `service.py` | 227   | Namespace tables, `GET_SQL` gate, host/db name generation, query wrappers |
| High  | `sql_bot.py` | 158   | Business-logic queries (category member fetch, cross-language diff)       |

Key issues:

| Issue                                                                              | Location               | Impact                                                  |
| ---------------------------------------------------------------------------------- | ---------------------- | ------------------------------------------------------- |
| `sql_bot.py` duplicates `GET_SQL()` guard logic (3 times)                          | `sql_bot.py:24,74,111` | Violates DRY — mid-layer already guards                 |
| `sql_bot.py` calls `make_sql_connect_silent` directly (bypassing mid-layer)        | `sql_bot.py:49,120`    | Bypasses `sql_new` wrapper, duplicates host/db logic    |
| `sql_bot.py` reimplements namespace prefix logic                                   | `sql_bot.py:59-60`     | `service.add_nstext_to_title` already exists            |
| `sql_bot.py` reimplements byte decoding                                            | `sql_bot.py:13-16`     | `db_pool.decode_value` already exists                   |
| `service.py` `sql_new` has mutable default arg `values=[]`                         | `service.py:158`       | Shared mutable default across calls                     |
| `service.py` `sql_new_title_ns` mixes wiki code extraction with query logic        | `service.py:198-201`   | `make_labsdb_dbs_p` already handles this                |
| `db_pool.py` `_sql_connect_pymysql` tries to `fetchall` even on non-SELECT queries | `db_pool.py:81-88`     | `INSERT`/`UPDATE` have no result set; `fetchall` raises |
| Hardcoded namespace dicts in `service.py`                                          | `service.py:13-58`     | No constants file                                       |
| No type hints on many functions                                                    | All files              | Reduced IDE support and runtime safety                  |

**This plan reorganises the module in five sequential phases** with backward-compatible shims.

---

## 2. Non-Goals (Scope Guard)

-   No changes to SQL query **results** — output must be identical
-   No changes to external dependency (`pymysql`)
-   No changes to `.env.example`, `settings.py`, or CLI argument handling
-   No changes to the custom exception hierarchy in `src/exceptions.py`
-   No database schema changes

---

## 3. Proposed Directory Structure

```
src/core/api_sql/
├── __init__.py                  # Public API; re-exports
├── constants.py                 # Namespace dicts, default config values
├── models.py                    # Dataclasses: QueryResult, DbConfig
├── client.py                    # Low-level: pymysql connection, query execution, byte decoding
├── gateway.py                   # Mid-level: GET_SQL gate, host/db name gen, query wrappers
└── queries.py                   # High-level: business-logic queries (category diff)
```

Legacy files become thin shims:

| Old file     | Shim to                                               |
| ------------ | ----------------------------------------------------- |
| `db_pool.py` | `from .client import *`                               |
| `service.py` | `from .gateway import *` + `from .constants import *` |
| `sql_bot.py` | `from .queries import *`                              |

---

## 4. Quick Wins (Execute Before Any Phase)

-   [x] Fix mutable default arg `values=[]` → `values=None` in `service.py:sql_new` — changed to `values: tuple | list = ()` (tuple is immutable, bug fixed; not `None` as originally planned)
-   [x] Remove dead `decode_bytes` in `sql_bot.py:13-16` (use `db_pool.decode_value`) — already removed in a prior commit
-   [x] Add `__all__` to `sql_bot.py`
-   [x] Add `__all__` to `service.py`
-   [x] Add `__all__` to `db_pool.py` (already present)

---

## 5. Detailed Phases

### Phase 1 — Code Hygiene _(DONE)_

**Target:** All files in `api_sql`.

**5.1.1 Create `constants.py`** _(DONE)_

Move namespace dicts and wiki config from `service.py`:

```python
# Mapping of namespace IDs to localized text
NS_TEXT_AR: dict[str, str] = {
    "0": "", "1": "نقاش", "2": "مستخدم", "3": "نقاش المستخدم",
    "4": "ويكيبيديا", "5": "نقاش ويكيبيديا", "6": "ملف",
    "7": "نقاش الملف", "10": "قالب", "11": "نقاش القالب",
    "12": "مساعدة", "13": "نقاش المساعدة", "14": "تصنيف",
    "15": "نقاش التصنيف", "100": "بوابة", "101": "نقاش البوابة",
    "828": "وحدة", "829": "نقاش الوحدة", "2600": "موضوع",
    "1728": "فعالية", "1729": "نقاش الفعالية",
}

NS_TEXT_EN: dict[str, str] = {
    "0": "", "1": "Talk", "2": "User", "3": "User talk",
    "4": "Project", "5": "Project talk", "6": "File",
    "7": "File talk", "8": "MediaWiki", "9": "MediaWiki talk",
    "10": "Template", "11": "Template talk", "12": "Help",
    "13": "Help talk", "14": "Category", "15": "Category talk",
    "100": "Portal", "101": "Portal talk", "828": "Module",
    "829": "Module talk",
}

# Wiki code → host/db name special cases
WIKI_DATABASE_OVERRIDES: dict[str, str] = {
    "wikidata": "wikidatawiki",
    "be-x-old": "be_x_old",
    "be_tarask": "be_x_old",
    "be-tarask": "be_x_old",
}

# Suffixes that should not get "wiki" appended
WIKI_SUFFIX_VALID_ENDS: tuple[str, ...] = ("wiktionary",)

# Default replica config
REPLICA_CNF_FILENAME = "replica.my.cnf"
ANALYTICS_DB_TEMPLATE = "{wiki}.analytics.db.svc.wikimedia.cloud"
DATABASE_SUFFIX = "_p"
```

**5.1.2 Add full type hints to all functions** _(PARTIALLY DONE — signatures typed, but `_run_query` returns bare `list[dict]` without `Any`, several helpers still lack full annotations)_

| Function                        | Current signature                   | Target signature                                           |
| ------------------------------- | ----------------------------------- | ---------------------------------------------------------- | ------------------------------ |
| `load_db_config`                | `(db, host) -> dict`                | `(db: str, host: str) -> dict[str, Any]`                   |
| `_sql_connect_pymysql`          | `(query, db, host, values) -> list` | `(query: str, db: str, host: str, values: tuple            | None) -> list[dict[str, Any]]` |
| `make_sql_connect_silent`       | `(query, db, host, values)`         | `(query: str, db: str, host: str, values: tuple            | None) -> list[dict[str, Any]]` |
| `GET_SQL`                       | `() -> bool`                        | Already typed                                              |
| `add_nstext_to_title`           | `(title, ns, lang)`                 | `(title: str, ns: str                                      | int, lang: str) -> str`        |
| `make_labsdb_dbs_p`             | `(wiki) -> tuple`                   | `(wiki: str) -> tuple[str, str]`                           |
| `sql_new`                       | `(queries, wiki, values)`           | `(queries: str, wiki: str, values: tuple                   | None) -> list[dict[str, Any]]` |
| `sql_new_title_ns`              | `(queries, wiki, t1, t2, values)`   | `(queries: str, wiki: str, t1: str, t2: str, values: tuple | None) -> list[str]`            |
| `fetch_arcat_titles`            | `(arcatTitle)`                      | `(arcatTitle: str) -> list[str]`                           |
| `fetch_encat_titles`            | `(encatTitle)`                      | `(encatTitle: str) -> list[str]`                           |
| `get_exclusive_category_titles` | `(encatTitle, arcatTitle) -> list`  | Already typed (returns `list`)                             |

**5.1.3 Normalize naming to snake_case**

| Old name                | New name                             | Location                      |
| ----------------------- | ------------------------------------ | ----------------------------- |
| `encatTitle`            | `en_cat_title`                       | `sql_bot.py`                  |
| `arcatTitle`            | `ar_cat_title`                       | `sql_bot.py`                  |
| `enpageTitle`           | `en_page_title`                      | `sql_bot.py`                  |
| `db_p`                  | `db_name`                            | `service.py:sql_new`          |
| `ns_text_tab_ar`        | `NS_TEXT_AR` (module-level constant) | `service.py`                  |
| `ns_text_tab_en`        | `NS_TEXT_EN` (module-level constant) | `service.py`                  |
| `t1`, `t2` (parameters) | `title_key`, `ns_key`                | `service.py:sql_new_title_ns` |

**Success criteria:** `ruff check src/core/api_sql` passes. `mypy src/core/api_sql --ignore-missing-imports` passes (except `pymysql` stub issues).

---

### Phase 2 — Eliminate Duplication (DRY) _(PARTIALLY DONE)_

**5.2.1 Remove redundant `GET_SQL()` guards in `sql_bot.py`** _(DONE)_

`sql_bot.py` calls `GET_SQL()` at three entry points (`fetch_arcat_titles:24`, `get_exclusive_category_titles:74`, `fetch_encat_titles:111`). Since `service.py:sql_new` already guards with `GET_SQL()` and returns `[]` when disabled, the guards in `fetch_arcat_titles` and `fetch_encat_titles` are redundant if they route through `sql_new`.

**Action:** Remove `GET_SQL()` guards from `fetch_arcat_titles` and `fetch_encat_titles`. Keep guard only at the top-level entry point (`get_exclusive_category_titles`).

**Current state:** `_fetch_ar_titles` and `_fetch_en_titles` have no `GET_SQL()` guard. Only `get_exclusive_category_titles` guards.

**Before:**

```python
def fetch_arcat_titles(arcatTitle):
    if not GET_SQL():
        return []
    ...
    ar_results = make_sql_connect_silent(ar_queries, db=db_p, host=host, values=(arcatTitle,))
```

**After:**

```python
def fetch_arcat_titles(ar_cat_title: str) -> list[str]:
    ar_results = sql_new(ar_queries, wiki="ar", values=(ar_cat_title,))
```

**5.2.2 Route `sql_bot.py` queries through `sql_new` instead of `make_sql_connect_silent`** _(DONE)_

`fetch_arcat_titles` and `fetch_encat_titles` both call `make_labsdb_dbs_p` + `make_sql_connect_silent` directly, duplicating logic that already lives in `service.py:sql_new`.

**Action:** Replace the `make_labsdb_dbs_p` + `make_sql_connect_silent` pair with a call to `sql_new`:

**Before (fetch_encat_titles):**

```python
host, db_p = make_labsdb_dbs_p("enwiki")
en_results = make_sql_connect_silent(queries, host=host, db=db_p, values=(item,))
```

**After:**

```python
en_results = sql_new(queries, wiki="en", values=(item,))
```

**5.2.3 Use `add_nstext_to_title` in `sql_bot.py` instead of manual prefix logic** _(DONE)_

`fetch_arcat_titles:59-60` manually does:

```python
if ns_text_tab_ar.get(str(ns)):
    title = f"{ns_text_tab_ar.get(str(ns))}:{title}"
```

**Action:** Replace with `add_nstext_to_title(title, ns, lang="ar")` from `service.py`.

**5.2.4 Remove duplicate `decode_bytes` in `sql_bot.py`** _(DONE — already removed in prior commit)_

`sql_bot.py:13-16` defines `decode_bytes` which duplicates `db_pool.py:decode_value`. The function is never called in `sql_bot.py` — it is dead code.

**Action:** Remove `decode_bytes` from `sql_bot.py`.

**Success criteria:** `sql_bot.py` no longer imports `make_sql_connect_silent`, `make_labsdb_dbs_p`, or `ns_text_tab_ar` directly. All queries route through `sql_new`. No dead code. _(DONE)_

---

### Phase 3 — Structural Split _(NOT DONE)_

**Target:** Decompose files into clear layers.

**5.3.1 Rename `db_pool.py` → `client.py`**

Pure rename with shim. Contains: `load_db_config`, `_sql_connect_pymysql`, `decode_value`, `decode_bytes_in_list`, `make_sql_connect_silent`.

**5.3.2 Split `service.py` into `gateway.py` + `constants.py`**

| New file       | Contents                                                                                                                                            |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `constants.py` | `NS_TEXT_AR`, `NS_TEXT_EN`, `WIKI_DATABASE_OVERRIDES`, `WIKI_SUFFIX_VALID_ENDS`, `REPLICA_CNF_FILENAME`, `ANALYTICS_DB_TEMPLATE`, `DATABASE_SUFFIX` |
| `gateway.py`   | `GET_SQL`, `add_nstext_to_title`, `make_labsdb_dbs_p`, `sql_new`, `sql_new_title_ns`                                                                |

**5.3.3 Rename `sql_bot.py` → `queries.py`**

Pure rename with shim. Contains: `fetch_arcat_titles`, `fetch_encat_titles`, `get_exclusive_category_titles`.

**Success criteria:** All old file paths importable via deprecation shims (`db_pool.py`, `service.py`, `sql_bot.py`). All new paths work.

---

### Phase 4 — Error Handling & Robustness _(DONE)_

**5.4.1 Handle non-SELECT queries in `_run_query`** _(DONE)_

Currently `_sql_connect_pymysql` unconditionally calls `cursor.fetchall()`. For `INSERT`/`UPDATE`/`DELETE` queries, this raises `pymysql.Error` which is caught and re-raised as `DatabaseFetchError`.

**Action:** Detect statement type and conditionally fetch:

```python
def _is_select_query(query: str) -> bool:
    return query.lstrip().upper().startswith("SELECT")

def _sql_connect_pymysql(
    query: str, db: str = "", host: str = "", values: tuple | None = None
) -> list[dict[str, Any]]:
    ...
    with connection as conn, conn.cursor() as cursor:
        cursor.execute(query, params)
        if _is_select_query(query):
            return list(cursor.fetchall())
        return []
```

**5.4.2 Fix mutable default argument in `sql_new`** _(DONE — changed to `values: tuple | list = ()`)_

`service.py:158`:

```python
def sql_new(queries, wiki="", values=[]):
```

**Action:** Change to `values=None` and handle inside:

```python
def sql_new(queries: str, wiki: str = "", values: tuple | None = None) -> list[dict[str, Any]]:
    if values is None:
        values = ()
    ...
```

**5.4.3 Add connection timeout and retry logic (optional)**

Consider adding `connect_timeout=10` and `read_timeout=30` to `load_db_config` for production robustness. This is a low-risk, high-value change for a live bot.

**Success criteria:** `fetchall` never called on non-SELECT queries. Mutable default eliminated. Connection timeouts configurable.

---

### Phase 5 — Testing & Validation _(DONE)_

**5.5.1 Update existing tests**

Tests need updating to match the refactored structure:

| Test file                                                  | Changes needed                                                                                                  |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `tests/api_sql/test_sql_bot.py`                            | Update imports if paths change. Remove tests for `GET_SQL()` inside `fetch_*` if guards removed.                |
| `tests/api_sql/test_wiki_sql.py`                           | Update imports of namespace dicts to `constants`. Verify `add_nstext_to_title`, `make_labsdb_dbs_p` still work. |
| `tests/api_sql/test_mysql_client/test_mysql_client.py`     | Add test for non-SELECT query (no fetchall).                                                                    |
| `tests/api_sql/test_mysql_client/test_make_sql_connect.py` | No changes expected.                                                                                            |
| `tests/conftest.py`                                        | Update mock path if `make_sql_connect_silent` moves.                                                            |

**5.5.2 Add missing unit tests**

| Function               | Test cases                                                                                               |
| ---------------------- | -------------------------------------------------------------------------------------------------------- |
| `_is_select_query`     | SELECT, INSERT, UPDATE, DELETE, whitespace prefix, empty string                                          |
| `load_db_config`       | LRU cache behavior, config dict structure, replica path                                                  |
| `_sql_connect_pymysql` | Connection failure, query failure, fetch failure, non-SELECT (no error), parameterized query, DictCursor |
| `sql_new`              | `GET_SQL()` disabled → empty list, valid query, missing wiki, None values                                |
| `fetch_arcat_titles`   | Empty input, namespace prefix stripping (تصنيف:), space-to-underscore, empty results                     |
| `fetch_encat_titles`   | `category:`/`Category:` prefix stripping, `[[en:...]]` bracket stripping, empty results                  |

**5.5.3 Integration test**

Run the full `find_sql` flow before/after each phase to verify identical output:

```bash
# Can only run in production (APP_ENV=production) with replica.my.cnf
# In test environment, verify mock-based integration test in test_main_flow.py still passes
pytest tests/api_sql/ tests/integration/test_main_flow.py -v
```

**Success criteria:** All existing tests pass. `pytest tests/api_sql/ --cov=src/core/api_sql --cov-report=term-missing` shows ≥ 85% coverage. _(DONE — 78 tests pass, 99% coverage)_

---

## 6. Public API Changes

| Current public symbol                   | New canonical location                          | Shim kept?             |
| --------------------------------------- | ----------------------------------------------- | ---------------------- |
| `api_sql.GET_SQL`                       | `api_sql.gateway.GET_SQL`                       | Yes, via `__init__.py` |
| `api_sql.sql_new`                       | `api_sql.gateway.sql_new`                       | Yes, via `__init__.py` |
| `api_sql.sql_new_title_ns`              | `api_sql.gateway.sql_new_title_ns`              | Yes, via `__init__.py` |
| `api_sql.add_nstext_to_title`           | `api_sql.gateway.add_nstext_to_title`           | Yes, via `__init__.py` |
| `api_sql.get_exclusive_category_titles` | `api_sql.queries.get_exclusive_category_titles` | Yes, via `__init__.py` |
| `api_sql.db_pool.*`                     | `api_sql.client.*`                              | Via `db_pool.py` shim  |
| `api_sql.service.*`                     | `api_sql.gateway.*` + `api_sql.constants.*`     | Via `service.py` shim  |
| `api_sql.sql_bot.*`                     | `api_sql.queries.*`                             | Via `sql_bot.py` shim  |

The public API exported from `__init__.py` stays **identical** — no consumer code changes needed.

---

## 7. Acceptance Criteria

-   [x] `sql_bot.py` no longer calls `make_sql_connect_silent` or `make_labsdb_dbs_p` directly — routes through `sql_new`
-   [x] `sql_bot.py` no longer has `GET_SQL()` guards inside helper fetchers
-   [x] `sql_bot.py` uses `add_nstext_to_title` instead of manual namespace prefixing
-   [x] Dead `decode_bytes` removed from `sql_bot.py`
-   [x] Mutable default fixed (`values=[]` → `values=()`) — tuple default avoids mutable-default bug
-   [x] `_run_query` handles non-SELECT queries without calling `fetchall`
-   [x] Namespace dicts moved to `constants.py`
-   [ ] All old file paths remain importable via shims _(pending Phase 3)_
-   [x] `ruff check src/core/api_sql` passes with zero errors
-   [x] `mypy src/core/api_sql --ignore-missing-imports` passes
-   [x] `pytest tests/api_sql/` passes — 78/78 pass, 99% coverage
-   [ ] `pytest tests/integration/test_main_flow.py` passes
-   [ ] All downstream consumers (`c18/sql_cat.py`, `c18/cat_tools_enlist.py`, `c18/dontadd.py`, `c18/cats_tools/ar_from_en.py`) continue to work with zero import changes

---

## 8. Risks & Mitigations

| Risk                                                                                  | Impact | Mitigation                                                                             |
| ------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------- |
| Removing `GET_SQL()` from `fetch_*` functions could expose dev to real DB calls       | Medium | Keep guard at `get_exclusive_category_titles` — these are the only public entry points |
| `sql_new` returns `[]` silently when SQL is disabled; `fetch_*` callers may not check | Low    | Behavior identical to current — not a regression                                       |
| Renaming files breaks internal relative imports                                       | Medium | Shim files at old paths guarantee backward compat                                      |
| `_is_select_query` misses edge cases (CTE, comments before SELECT)                    | Low    | Conservative — only affects non-SELECT paths that would have broken anyway             |
| `decode_bytes` removal could affect external consumers                                | Low    | Function was never called; safe to remove                                              |

---

## 9. Current vs. Target Structure

```
Current:                              Target:
src/core/api_sql/                          src/core/api_sql/
├── __init__.py                       ├── __init__.py          (unchanged exports)
├── db_pool.py                   ├── constants.py         (new — namespace dicts, config)
├── service.py                       ├── models.py            (new — dataclasses)
├── sql_bot.py                        ├── client.py            (was db_pool.py)
                                      ├── gateway.py           (was service.py sans constants)
                                      └── queries.py           (was sql_bot.py)

Legacy shims (import from new locations):
├── db_pool.py  →  from .client import *       # noqa: F401, F403
├── service.py      →  from .constants import *    # noqa: F401, F403
                       from .gateway import *        # noqa: F401, F403
└── sql_bot.py       →  from .queries import *       # noqa: F401, F403
```

---

## 10. Execution Order

| Phase      | Steps                                                                  | Status  | Estimated effort | Dependencies |
| ---------- | ---------------------------------------------------------------------- | ------- | ---------------- | ------------ |
| Quick Wins | Fix mutable default, remove dead code, add `__all__`                   | Done    | 15 min           | None         |
| Phase 1    | Create `constants.py`, add type hints, rename symbols                  | Done    | 1 hr             | Quick Wins   |
| Phase 2    | DRY: route through `sql_new`, use `add_nstext_to_title`, remove guards | Done    | 1 hr             | Phase 1      |
| Phase 3    | Rename and split files, add shims                                      | Pending | 30 min           | Phase 2      |
| Phase 4    | Fix `fetchall` for non-SELECT, add connection timeout                  | Done    | 30 min           | Phase 3      |
| Phase 5    | Update tests, add missing tests                                        | Done    | 1-2 hr           | Phase 4      |

**Total estimated effort:** ~4-5 hours. **Spent so far:** ~2 hours.

---

## 11. Downstream Consumers Verification

After refactoring, verify these consumer files still work (imports unchanged due to `__init__.py` stability):

| Consumer file                          | Symbols imported from api_sql |
| -------------------------------------- | ----------------------------- |
| `src/core/c18/sql_cat.py`          | `GET_SQL`, `sql_new_title_ns` |
| `src/core/c18/cat_tools_enlist.py` | (via settings-based SQL flag) |
| `src/core/c18/dontadd.py`          | (via settings-based SQL flag) |
| `tests/integration/test_main_flow.py`  | (mock-based import test)      |

No import changes are needed — `api_sql/__init__.py` re-exports all public symbols unchanged.

---

_Plan created 2026-04-26. Follows same methodology as `mk_cats_refactor_plan.md` and `c18_master_refactoring_plan.md`._
