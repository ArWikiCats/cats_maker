# Refactoring Roadmap

> How to start and proceed with the refactoring across all 7 modules.
> Order is driven by dependency chains — infrastructure first, business logic last.

---

## Dependency Map

```
wiki_api (HTTP transport) ─┬─> new_api (OOP API wrapper) ─┬─> b18_new
                            │                              ├─> mk_cats
                            │                              └─> c18_new
                            │
api_sql (DB access) ────────┼─> b18_new
                            ├─> c18_new
                            │
wd_bots (Wikidata) ─────────┼─> mk_cats
                            └─> c18_new
```

**Rule:** Always refactor a module only after all its upstream dependencies are done.

---

## Phase 0: Quick Wins (across all modules, in parallel)

Zero-risk changes that can be done immediately, in any order:

| #   | Task                                                   | Plans                       |
| --- | ------------------------------------------------------ | --------------------------- |
| 0.1 | Add `__all__` to all `__init__.py` and submodule files | All 7                       |
| 0.2 | Remove commented-out debug code                        | All 7                       |
| 0.3 | Remove empty `__init__` methods                        | new_api                     |
| 0.4 | Remove dead functions (`decode_bytes`, unused imports) | api_sql (**done**), new_api |
| 0.5 | Fix mutable default args (`values=[]` → `values=()`)   | api_sql (**done**)          |
| 0.6 | Replace mutable lists with tuples/frozensets           | mk_cats, c18_new            |
| 0.7 | Add `__pycache__` to `.gitignore`                      | mk_cats, c18_new            |
| 0.8 | Run `ruff` across all modules, fix auto-fixable issues | All 7                       |

**Estimated effort:** 1-2 hours. **Goal:** Get type-checking and linting baseline passing.

---

## Phase 1: Shared Infrastructure

### Step 1.1 — `wiki_api` refactoring

**Why first:** Every other module depends on `wiki_api` for HTTP transport.

**Execute per plan:** `wiki_api_refactor_plan.md`

-   Phase 1: Fix `r22` NameError bug in `transport.py` (urgent)
-   Phase 2: Extract `cache.py` with real TTL eviction
-   Phase 3: Create unified `client.py` (merge WikiApiHandler + NEW_API)
-   Phase 4: Clean up `himoBOT2.py`
-   Phase 5: Clean up `sub_cats_bot.py`
-   Phase 6: Add `_compat.py` backward-compat layer

**Verification:** `pytest tests/wiki_api/` passes, `ruff check src/core/wiki_api` is clean.

### Step 1.2 — `api_sql` refactoring _(Phases 1, 2, 4, 5 done; Phase 3 pending)_

**Why second:** Database layer needed by business logic modules. No dependency on `wiki_api`.

**Execute per plan:** `api_sql_refactor_plan.md`

| Phase      | Status  | Notes                                                                             |
| ---------- | ------- | --------------------------------------------------------------------------------- |
| Quick Wins | Done    | `__all__` added, mutable default fixed, dead code removed, formatting done        |
| Phase 1    | Done    | `constants.py` created; namespace dicts and config extracted                      |
| Phase 2    | Done    | Queries route through `sql_new`; `add_nstext_to_title` replaces `_with_ns_prefix` |
| Phase 3    | Pending | No file rename shims yet (`client.py`, `gateway.py`, `queries.py`)                |
| Phase 4    | Done    | `fetchall` skipped for non-SELECT; connection timeouts added                      |
| Phase 5    | Done    | 78/78 tests pass; 99% coverage                                                    |

**Verification:** `pytest tests/api_sql/` passes with >= 85% coverage.

### Step 1.3 — Shared constants & utils

**Why alongside:** Reduces duplication before business-layer refactoring starts.

-   Create `src/core/constants.py` with shared namespace dicts (from api_sql + new_api)
-   Create `src/core/utils/text.py` with `normalize_category_title()`, `clean_wiki_brackets()`, `extract_wikidata_qid()`
-   Ensure both are importable by `b18_new`, `c18_new`, `mk_cats`

### Step 1.4 — `wd_bots` refactoring

**Why after wiki_api:** Uses `wiki_api` transport. Needed by `mk_cats` and `c18_new`.

**Execute per plan:** `wd_bots_refactor_plan.md`

-   Phase 1: Extract `lag.py` (LagManager class)
-   Phase 2: Unified `errors.py` (merge handle_err_wd + out_json)
-   Phase 3: Extract `client.py` (APIClient)
-   Phase 4: Refactor `queries.py` (from wd_api_bot.py)
-   Phase 5: Refactor `operations.py` (from to_wd.py)
-   Phase 6: Update `__init__.py`

**Verification:** `pytest tests/wd_bots/` passes, 0% → >= 80% coverage on write layer.

### Step 1.5 — `new_api` refactoring

**Why after wiki_api:** Wraps wiki_api. Needed by all 3 business modules.

**Execute per plan:** `new_api_refactor_plan.md`

-   Phase 1: Hygiene (`__all__`, type hints, spelling fixes, constants extraction)
-   Phase 2: Global mutable state → instance-scoped
-   Phase 3: Split `bot.py` → `transport.py` + `auth.py` + `client.py`
-   Phase 4: Refactor `super_page.py` (MainPage) — composition over mixins
-   Phase 5: Fix error handling (recursion → iteration, exponential backoff)
-   Phase 6: Refactor `catdepth_new.py`
-   Phase 7: Fix `params_w` mutation bug
-   Phase 8: Tests

**Verification:** `pytest tests/new_api/` passes, >= 75% coverage.

---

## Phase 2: Business Logic Modules

### Step 2.1 — `b18_new` refactoring

**Why first of the three:** Lightest module, fewest dependencies.

**Execute per plan:** `b18_new_refactor_plan.md`

-   Phase 1: `constants.py` + `utils/text.py` (use shared utils from Step 1.3)
-   Phase 2: Refactor `sql_cat_checker.py` → `core/category_validator.py`
-   Phase 3: Refactor `cat_tools_enlist.py` → `core/member_lister.py`
-   Phase 4: Merge `sql_cat.py` + `cat_tools_enlist2.py` → `core/category_resolver.py` + `io/`
-   Phase 5: Add `models.py`
-   Phase 6: Update `__init__.py` with deprecation shims
-   Phase 7: Tests

**Verification:** `pytest tests/b18_new/` passes, > 80% coverage.

### Step 2.2 — `mk_cats` refactoring

**Why second:** Depends on `new_api` + `wd_bots` (both done). Used by `c18_new`.

**Execute per plan:** `mk_cats_refactor_plan.md`

-   Phase 1: `constants.py`, type hints, snake_case, encapsulate module state (ProcessingState)
-   Phase 2: Structural split — `mknew.py` into `category_pipeline.py` + `label_resolver.py`
-   Phase 3: Complexity reduction — simplify `make_ar` and `add_text_to_cat`
-   Phase 4: Move files to new directory structure
-   Phase 5: Tests

**Verification:** `pytest tests/mk_cats/` passes, >= 80% coverage. Integration diff on `Science` category is empty.

### Step 2.3 — `c18_new` refactoring

**Why last:** Largest module (7+ files), highest complexity, depends on everything.

**Execute per plan:** `c18_new_master_refactoring_plan.md`

-   Phase 1: `constants.py`, snake_case, type hints
-   Phase 2: Deduplication — merge `ar_from_en.py` + `ar_from_en2.py`, merge templatequery files
-   Phase 3: Complexity reduction — `filter_cats_text` predicates, cross-wiki linker, sort, doc_handler
-   Phase 4: Structural reorganization into `core/`, `tools/`, `io/`, `utils/`
-   Phase 5: Tests

**Verification:** `pytest tests/c18_new/` passes, >= 80% coverage. `radon cc` shows no function above grade B.

---

## Phase 3: Integration & Validation

| Step | Task                                 | Verification                                                |
| ---- | ------------------------------------ | ----------------------------------------------------------- |
| 3.1  | Run full test suite                  | `pytest tests/` — all pass                                  |
| 3.2  | Run linter across entire `src/core/` | `ruff check src/core/` — zero errors                        |
| 3.3  | Run type checker                     | `mypy src/core/ --ignore-missing-imports` — passes          |
| 3.4  | Integration diff test                | Run `python run.py -encat:Science` before/after, diff empty |
| 3.5  | Complexity gate                      | `radon cc src/core/ -s` — no function above grade B         |
| 3.6  | Coverage gate                        | All modules >= 80% coverage                                 |

---

## Quick Start (TL;DR)

```bash
# 1. Get linting/typing baseline
ruff check src/core/ --statistics
mypy src/core/ --ignore-missing-imports --statistics

# 2. Fix wiki_api NameError bug (most urgent)
#    wiki_api_refactor_plan.md → Phase 1

# 3. Build shared infrastructure
#    api_sql: constants.py done; DRY done; fetchall fix done
#    utils:   shared constants.py + utils/text.py
#    utils:   shared constants.py + utils/text.py

# 4. Refactor upstream layers in order:
#    wiki_api → wd_bots → new_api

# 5. Refactor downstream layers in order:
#    b18_new → mk_cats → c18_new

# 6. Validate
pytest tests/ --cov=src/core --cov-report=term-missing
```

**Total estimated effort:** ~40-60 hours across all modules.

---

_Generated 2026-04-26._
