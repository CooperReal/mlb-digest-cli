# Harness Patterns — Design

**Date:** 2026-04-19
**Status:** Approved
**Scope:** MLB Digest CLI (single-user, single-agent, CLI/no-UI)

Adapted application of the "Adding Harness Patterns to a Repo" ultraplan. Approach A: fill real gaps, skip phases whose skip criteria apply, note what's already covered. Phases 6 (isolation) and 7 (throughput) are skipped per the plan's own skip criteria for single-agent workflows.

## Goals

1. Close the gaps in the repo's agent harness that are not already covered by `CLAUDE.md`, `AGENTS.md` (untracked), `check.sh`, `tests/test_architecture.py`, or CI.
2. Preserve an audit trail (Phase 0) so a future agent can tell what was done and why.
3. Keep the additions small and load-bearing — no cargo-culting.

## Non-goals

- Replacing or duplicating `CLAUDE.md` / existing `AGENTS.md` content.
- Adding `docs/architecture.md` — `AGENTS.md` already serves that role.
- Adding `docs/conventions.md` — `CLAUDE.md` already serves that role.
- Isolation tooling (git worktree per task) — single-agent repo.
- Throughput-shaped policy (automerge, minimal review gates) — single-user repo.

## Deliverables

| File | Status | Purpose |
|---|---|---|
| `docs/harness-audit.md` | new | Phase 0: before-picture + per-phase status + remaining gaps |
| `AGENTS.md` | edit (untracked → tracked) | Prepend **Session start** / **Session end** checklists |
| `claude-progress.txt` | new | Append-only session log, seeded with one entry |
| `feature_list.json` | new | Truth-table: current capabilities (`passes: true`) + roadmap (`passes: false`) |
| `init.sh` | new | Fresh-clone → runnable in one command; idempotent |
| `docs/decisions/README.md` | new | ADR template + numbering + append-only rule |
| `docs/decisions/0001-teams-registry-as-single-source-of-truth.md` | new | Backfill ADR |
| `docs/decisions/0002-gmail-ios-dark-mode-blend-mode-hack.md` | new | Backfill ADR |
| `docs/decisions/0003-squash-only-merge-policy.md` | new | Backfill ADR |
| `docs/decisions/0004-architecture-tests-as-enforcement-layer.md` | new | Backfill ADR |

**Explicitly not adding:** `docs/architecture.md`, `docs/conventions.md`, worktree tooling, automerge policy.

## Component details

### 1. `docs/harness-audit.md`

Five sections, ~80–120 lines total:

1. **Snapshot.** Repo role (single-user daily-email CLI), single-agent workflow, CLI/no-UI, existing strengths (CI, architecture tests, secrets pre-commit, multi-team registry). This framing drives every skip decision.
2. **Per-phase status.** Table with columns `Phase` / `State before` / `Action taken` / `Skipped? Why`. One row per phase 0–7.
3. **Failure modes observed.** Honest answer: "n/a — preventive. This pass was structural, not reactive to a specific agent failure. Record observed failures here going forward so future passes can be targeted."
4. **What got built this pass.** File list with one-line purpose each.
5. **Remaining gaps.** e.g. UI feedback loops (n/a — CLI), observability hooks (add if the digest ever runs as a long-lived service), throughput policy (add if volume rises).

This doc is a snapshot — updated only when repo posture changes, not per-session.

### 2. `AGENTS.md` checklist prepend

Inserted immediately after the intro paragraph, before "What this repo does":

```
## Session start checklist

1. `pwd` — confirm you're in the repo root (C:\Users\cooper\braves)
2. Read `claude-progress.txt` — last 3 entries
3. `git log --oneline -20` and `git status`
4. Read `feature_list.json`; if working a roadmap item, pick one marked `passes: false`
5. `./init.sh` (idempotent — safe to re-run)
6. `bash check.sh` — if red, fix before starting new work

## Session end checklist

1. `bash check.sh` passes (or failures are documented in the progress entry)
2. Branch pushed, PR open, CI green before merge (see CLAUDE.md — squash-only)
3. Append an entry to `claude-progress.txt` — date, scope, state, next
4. Update `feature_list.json` only for features verified end-to-end this session
```

Rest of `AGENTS.md` unchanged. The file transitions from untracked to tracked in the same commit.

### 3. `claude-progress.txt`

Plain text, append-only. Entry format:

```
========================================================================
YYYY-MM-DD — <short scope>
Scope: <what the session was trying to do>
Added: <files / modules / features touched>
State: <green/red test state, open threads, known risks>
Next:  <what the next agent should pick up>
========================================================================
```

Four fixed slots (**Scope / Added / State / Next**). "Next" is the handoff. Seed with one entry for this session summarizing the harness setup.

### 4. `feature_list.json`

Hybrid truth-table: current capabilities + known roadmap. Extended schema with a `priority` field (nullable; used only for `passes: false` items):

```json
{
  "features": [
    {
      "id": "f001",
      "category": "core",
      "description": "Daily digest sends successfully via Gmail SMTP",
      "steps": [
        "uv run mlb-digest --no-email prints non-empty narrative",
        "uv run mlb-digest test-email delivers to EMAIL_RECIPIENTS",
        "uv run mlb-digest (full) exits 0"
      ],
      "passes": true,
      "priority": null,
      "last_verified": "2026-04-19"
    }
  ]
}
```

**Seed items** (~14):

*`passes: true` — current capabilities:*
- `f001` core — daily digest sends via Gmail SMTP
- `f002` flag — `--catchup` adds roster / season overview / playoff picture
- `f003` flag — `--no-email` prints to stdout
- `f004` flag — `--dry-run` dumps raw data, skips Claude
- `f005` flag — `--smoke-test` uses Haiku + `max_tokens=50`
- `f006` subcommand — `test-email`
- `f007` subcommand — `list-teams`
- `f008` config — multi-team support via `teams_registry` (30 teams)
- `f009` rendering — email survives Gmail iOS dark-mode inversion
- `f010` quality — `tests/test_architecture.py` enforces layer boundaries
- `f011` resilience — narrator failure degrades to raw numbers (exit 1)
- `f012` resilience — email failure degrades to stdout (exit 2)

*`passes: false` — known roadmap (from memory):*
- `f013` feature — CSV subscriber list as interim multi-recipient (priority: medium)
- `f014` feature — multi-recipient via database (priority: low — blocked by f013)

### 5. `init.sh`

```bash
#!/usr/bin/env bash
# Fresh clone → runnable. Idempotent; safe to re-run.
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed. Install: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

uv sync

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Fill in ANTHROPIC_API_KEY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD, EMAIL_RECIPIENTS before running."
fi

uv run pre-commit install

echo "Ready. Next: fill in .env, then 'bash check.sh' to verify."
```

Executable (`chmod +x`). **Not** in `init.sh`: running the test suite (that's `check.sh`), touching `.secrets.baseline` (pre-commit handles it), anything requiring network beyond `uv sync`.

### 6. ADRs

**`docs/decisions/README.md`**

```md
# Architecture Decision Records

One file per significant decision.

- Filename: `NNNN-kebab-case-title.md` (zero-padded, monotonically increasing)
- Sections: **Context**, **Decision**, **Consequences**, **Status** (Proposed / Accepted / Superseded by NNNN)
- Date the decision in the body, not the filename

ADRs are append-only. To change a decision, write a new ADR that supersedes the old one.
```

**Four backfill ADRs** — written as full prose, not skeletons:

1. **0001 — `teams_registry` as single source of truth.** Rationale for holding all 30 teams in one module rather than per-team config files. Ref: multi-team support PR #1.
2. **0002 — Gmail iOS dark-mode blend-mode hack.** Why `templates.py` uses `linear-gradient` backgrounds + `mix-blend-mode` wrappers (`gfix-screen` / `gfix-diff`). Gmail iOS auto-inverts colors and strips `<style>` blocks except the first. Refs commits `57d296f`, `999b629`. Without this ADR the CSS reads as cargo-cult.
3. **0003 — Squash-only merge policy.** Repo is configured squash-only with branch auto-delete on and required CI. Consequence: feature branches are short-lived; don't chain PRs off feature branches.
4. **0004 — Architecture tests as enforcement layer.** Why layer boundaries, dataclass-return rules, and naming conventions live in `tests/test_architecture.py` rather than ruff plugins or docs. Fails in CI with a specific remediation message; lint plugins would need to be custom-written; docs drift.

### 7. Branch + commit strategy

- **Branch:** `chore/harness-patterns`
- **Single commit** bundling all deliverables (squash-merge erases per-file commit granularity anyway).
- **Commit subject:** `chore: add agent harness (audit, session continuity, ADRs)`
- **PR:** against `master`, wait for CI (`check` + `smoke-test`) green, squash-merge.
- `bash check.sh` passes locally before push. Pre-commit hooks run normally; `.secrets.baseline` refreshed if the hook requests it. No `--no-verify`.
- **Not doing:** separate PR per phase, direct commits to `master`.

## Risks / constraints

- **`AGENTS.md` line count.** Prepending checklists pushes the file from ~140 to ~160 lines. Still under the ~200 budget the ultraplan suggests. Acceptable.
- **`feature_list.json` drift.** The session-end checklist mandates updating it only for features *verified end-to-end this session*. This prevents drift by preventing lazy updates.
- **ADR backfill accuracy.** Rationales are derived from current code + commit messages. If a past decision's real rationale differs, ADRs should be corrected before acceptance.
- **None of the new files are loaded at runtime.** All additions are docs or dev-time scripts. No impact on the digest hot path or existing tests.

## Verification

Before PR:

```bash
bash check.sh   # ruff + mypy + architecture tests + full suite
bash init.sh    # fresh-state smoke of init.sh itself (idempotent)
```

No new tests required — none of the additions are runtime code.

## Acceptance

Ship when:

1. All files in the deliverables table exist, committed on branch `chore/harness-patterns`.
2. `bash check.sh` passes locally.
3. PR opened against `master`, both CI jobs green.
4. You approve the ADR rationales after reading them.
