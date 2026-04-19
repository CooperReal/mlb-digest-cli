# 0003 — Architecture tests as enforcement layer

**Date:** 2026-04-19
**Status:** Accepted

## Context

The codebase has several invariants that are load-bearing but not expressed in the language itself:

- Layer dependency direction (`teams_registry`/`config` → `mlb_api`/`feeds` → `narrator` → `templates` → `emailer` → `cli`, no upward imports).
- Public functions in `mlb_api`, `feeds`, `config` must return dataclasses, not dicts.
- Public function signatures must declare return types (Click-decorated commands exempt).
- Custom exceptions end in `Error`, not `Exception`.
- No wildcard imports.
- Logging uses `%`-formatting, not f-strings (lazy + parseable).
- Non-data modules cap at 300 lines (`teams_registry` exempt — it's data).

These cannot be expressed in ruff alone without custom plugins, and putting them only in docs means they rot.

## Decision

Enforce via Python tests in `tests/test_architecture.py`. The tests use AST inspection and import analysis. They run as part of `bash check.sh` and in CI.

## Consequences

**Positive**

- Runs in CI and locally with zero new tooling.
- Failure messages can be specific and actionable ("module X imports Y but Y is at a higher layer — fix by moving X up or inverting the dependency").
- No dependency on custom ruff plugins (which would have to be written, packaged, and maintained).
- Tests are first-class code: refactor-safe, type-checked, easy to extend.

**Negative / trade-offs**

- Marginally slower than pure lint because of pytest startup overhead.
- Readers may be momentarily surprised that "tests" enforce style, not behavior. The test names are descriptive enough that the surprise is self-documenting.
- Test logic itself must be correct; a false negative silently erodes enforcement. The tests have their own review standard.

## Refs

- `tests/test_architecture.py`
- `AGENTS.md` — "Module layers (enforced by tests)"
- `check.sh` — `=== Architecture ===` step
