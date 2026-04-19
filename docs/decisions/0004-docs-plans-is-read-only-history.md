# 0004 — `docs/plans/` is read-only history

**Date:** 2026-04-19
**Status:** Accepted

## Context

`docs/plans/multi-team-files/` contains a snapshot of pre-merge design artifacts from the multi-team-support work: draft versions of `cli.py`, `config.py`, `teams_registry.py`, `narrator.py`, `templates.py`, example per-team TOML configs, and a draft test file. These files intentionally diverge from the current source tree. They are preserved as an audit trail of what was proposed vs. what shipped.

The directory is ruff-excluded in `pyproject.toml` (`extend-exclude = ["docs/plans/multi-team-files"]`), so it does not participate in lint. An agent or contributor discovering the directory without context could mistake it for a reference implementation and either edit the frozen files or copy outdated patterns into current code.

## Decision

Treat `docs/plans/multi-team-files/` (and anything else under `docs/plans/` of similar nature) as read-only history.

**Agents and contributors must NOT:**

- Edit files under `docs/plans/multi-team-files/`.
- Copy patterns from it into current source (patterns may be outdated; the current source is authoritative).
- Reference its files as examples of current conventions.

**Agents and contributors MAY:**

- Read it to understand design intent at the time of the PR.
- Reference it for historical context when explicitly asked.

## Consequences

**Positive**

- Design history preserved for audit and learning.
- Ruff exclusion prevents lint churn against frozen code.
- Explicit rules mean an agent discovering the directory has the context to avoid the trap.

**Negative / trade-offs**

- The directory will drift further from current source over time; that drift is expected and does not constitute a bug.
- An agent who skips this ADR and ignores the matching `AGENTS.md` bullet could still mistakenly treat the directory as current.

## Refs

- `docs/plans/multi-team-files/`
- `pyproject.toml:38` (`extend-exclude`)
- `AGENTS.md` — "Non-obvious things the graph (and source) reveal", bullet about `docs/plans/multi-team-files/` being ruff-excluded
