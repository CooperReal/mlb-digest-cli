# 0005 — Agent-harness sizing

**Date:** 2026-04-19
**Status:** Accepted

## Context

The "Adding Harness Patterns to a Repo" ultraplan defines eight phases (0–7) of agent harness work: audit, repo-as-source-of-truth, session continuity, startup discipline, feedback loops, mechanical enforcement, isolation, and throughput policy. Not every repo needs every phase; the plan itself has explicit skip criteria.

This repo is:

- Single-user (one human runs all agents).
- Single-agent at a time (no parallel orchestration).
- CLI-only (no UI, no long-lived service).
- Python, with pre-existing CI (`check.sh`, GitHub Actions), architecture tests, `detect-secrets` baseline, and pre-commit hooks.

## Decision

Adopt phases 0–5 pragmatically. Skip phases 6 and 7.

- **Phase 0 — Audit.** This ADR is the audit.
- **Phase 1 — Repo as source of truth.** Already satisfied by `CLAUDE.md` (rules/style/commit policy), `AGENTS.md` (architecture facts), `README.md` (user-facing commands), and `docs/decisions/` (rationale). No separate `docs/architecture.md` or `docs/conventions.md` — they would duplicate existing docs.
- **Phase 2 — Session continuity.** Satisfied by `docs/superpowers/specs/` and `docs/plans/`, which persist through context clears. Spec-driven work is the continuity mechanism; a separate `claude-progress.txt` would duplicate what git history + committed specs already provide.
- **Phase 3 — Startup discipline.** Session start/end checklists prepended to `AGENTS.md`.
- **Phase 4 — Feedback loops.** `bash check.sh` bundles secrets baseline, lint (ruff), type check (mypy), architecture tests, and the full pytest suite. A non-blocking graph-freshness warning in `check.sh` surfaces `graphify-out/` staleness so `AGENTS.md`'s architecture facts do not silently diverge from `src/`. `/graphify` regeneration remains manual because it is an LLM call — too expensive to gate every commit.
- **Phase 5 — Mechanical enforcement.** `tests/test_architecture.py` (see ADR 0003) enforces layer direction, return-type rules, naming conventions, module-size caps.
- **Phase 6 — Isolation / worktrees.** Skipped. Single agent at a time; no parallel-agent contention to isolate against.
- **Phase 7 — Throughput policy.** Skipped. Single user; automerge and minimal-review gates would create risk without throughput benefit.

## Consequences

**Positive**

- The harness is sized to observed needs, not speculative ones.
- Skipped phases are named and justified, not silently absent.
- Future revisits have a decision matrix to update rather than starting from scratch.

**Negative / trade-offs**

- If any of the "triggers for revisit" fire, some harness work will be retrofitted under time pressure rather than put in place proactively.

## Triggers for revisit

Write a new ADR that supersedes this one if any of the following become true:

- Multi-agent orchestration is introduced (revisit Phase 6).
- A UI is added (revisit Phase 4 — browser feedback loop).
- A long-lived service is deployed (revisit Phase 4 — observability hooks).
- More than one concurrent contributor (revisit Phase 7).

## Refs

- `docs/superpowers/specs/2026-04-19-harness-patterns-design.md`
- `CLAUDE.md`, `AGENTS.md`, `README.md`
- `tests/test_architecture.py`
- `check.sh`
